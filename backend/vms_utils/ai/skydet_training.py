from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset

from vms_utils.ai.skydet_detector import (
    SkyDetModel,
    _letterbox_resize,
    _make_points,
    _xyxy_from_points_ltrb,
)


class _YoloDetectionDataset(Dataset):
    def __init__(self, root: Path, image_size: int) -> None:
        self.root = root
        self.image_size = image_size
        self.images = sorted((root / "images" / "train").glob("*"))
        if not self.images:
            raise RuntimeError("The dataset has no training images.")

    def __len__(self) -> int:
        return len(self.images)

    def __getitem__(self, index: int):
        image_path = self.images[index]
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Unable to read training image: {image_path.name}")
        height, width = image.shape[:2]
        boxes: list[list[float]] = []
        labels: list[int] = []
        label_path = self.root / "labels" / "train" / f"{image_path.stem}.txt"
        if label_path.exists():
            for line in label_path.read_text(encoding="utf-8").splitlines():
                values = line.split()
                if len(values) < 5:
                    continue
                class_id, center_x, center_y, box_width, box_height = map(float, values[:5])
                center_x *= width
                center_y *= height
                box_width *= width
                box_height *= height
                boxes.append(
                    [
                        center_x - (box_width / 2),
                        center_y - (box_height / 2),
                        center_x + (box_width / 2),
                        center_y + (box_height / 2),
                    ]
                )
                labels.append(int(class_id))

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        letterboxed, meta = _letterbox_resize(rgb, self.image_size)
        boxes_tensor = torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4)
        if boxes_tensor.numel():
            boxes_tensor[:, [0, 2]] = boxes_tensor[:, [0, 2]] * meta["scale"] + meta["pad_left"]
            boxes_tensor[:, [1, 3]] = boxes_tensor[:, [1, 3]] * meta["scale"] + meta["pad_top"]
        tensor = torch.from_numpy(letterboxed).permute(2, 0, 1).float() / 255.0
        return tensor, boxes_tensor, torch.tensor(labels, dtype=torch.long)


def _collate(batch):
    images, boxes, labels = zip(*batch)
    return torch.stack(images), list(boxes), list(labels)


def _flatten_outputs(cls_outs, reg_outs, ctr_outs, num_classes: int):
    cls = torch.cat(
        [value.permute(0, 2, 3, 1).reshape(value.shape[0], -1, num_classes) for value in cls_outs],
        dim=1,
    )
    reg = torch.cat(
        [value.permute(0, 2, 3, 1).reshape(value.shape[0], -1, 4) for value in reg_outs],
        dim=1,
    )
    ctr = torch.cat(
        [value.permute(0, 2, 3, 1).reshape(value.shape[0], -1) for value in ctr_outs],
        dim=1,
    )
    points = torch.cat(
        [
            _make_points(value.shape[-2], value.shape[-1], stride, value.device)
            for value, stride in zip(cls_outs, (4, 8, 16, 32))
        ],
        dim=0,
    )
    return cls, reg, ctr, points


def _sample_loss(
    cls_logits: torch.Tensor,
    reg_pred: torch.Tensor,
    ctr_logits: torch.Tensor,
    points: torch.Tensor,
    boxes: torch.Tensor,
    labels: torch.Tensor,
    num_classes: int,
) -> torch.Tensor:
    cls_targets = torch.zeros_like(cls_logits)
    positive = torch.zeros(points.shape[0], dtype=torch.bool, device=points.device)
    assigned_ltrb = torch.zeros_like(reg_pred)
    centerness = torch.zeros_like(ctr_logits)

    if boxes.numel():
        boxes = boxes.to(points.device)
        labels = labels.to(points.device)
        px = points[:, 0:1]
        py = points[:, 1:2]
        left = px - boxes[:, 0]
        top = py - boxes[:, 1]
        right = boxes[:, 2] - px
        bottom = boxes[:, 3] - py
        ltrb = torch.stack([left, top, right, bottom], dim=-1)
        inside = ltrb.min(dim=-1).values > 0
        areas = ((boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])).unsqueeze(0)
        candidate_areas = torch.where(inside, areas, torch.full_like(areas, float("inf")))
        minimum_area, assigned_index = candidate_areas.min(dim=1)
        positive = torch.isfinite(minimum_area)
        if positive.any():
            assigned_ltrb[positive] = ltrb[
                torch.arange(points.shape[0], device=points.device)[positive],
                assigned_index[positive],
            ]
            assigned_labels = labels[assigned_index[positive]].clamp(0, num_classes - 1)
            cls_targets[positive, assigned_labels] = 1.0
            pos_ltrb = assigned_ltrb[positive]
            lr = pos_ltrb[:, [0, 2]]
            tb = pos_ltrb[:, [1, 3]]
            centerness[positive] = torch.sqrt(
                (lr.min(dim=1).values / lr.max(dim=1).values.clamp(min=1e-6))
                * (tb.min(dim=1).values / tb.max(dim=1).values.clamp(min=1e-6))
            )

    probability = torch.sigmoid(cls_logits)
    bce = F.binary_cross_entropy_with_logits(cls_logits, cls_targets, reduction="none")
    focal_weight = torch.where(cls_targets > 0, 0.25, 0.75) * (probability - cls_targets).abs().pow(2)
    cls_loss = (bce * focal_weight).sum() / max(1, int(positive.sum()))
    if not positive.any():
        return cls_loss

    predicted_boxes = _xyxy_from_points_ltrb(points[positive], reg_pred[positive])
    target_boxes = _xyxy_from_points_ltrb(points[positive], assigned_ltrb[positive])
    intersection_min = torch.maximum(predicted_boxes[:, :2], target_boxes[:, :2])
    intersection_max = torch.minimum(predicted_boxes[:, 2:], target_boxes[:, 2:])
    intersection = (intersection_max - intersection_min).clamp(min=0).prod(dim=1)
    predicted_area = (predicted_boxes[:, 2:] - predicted_boxes[:, :2]).clamp(min=0).prod(dim=1)
    target_area = (target_boxes[:, 2:] - target_boxes[:, :2]).clamp(min=0).prod(dim=1)
    iou = intersection / (predicted_area + target_area - intersection + 1e-6)
    reg_loss = (1 - iou).mean()
    ctr_loss = F.binary_cross_entropy_with_logits(ctr_logits[positive], centerness[positive])
    return cls_loss + (2.0 * reg_loss) + ctr_loss


def train_skydet(
    data_yaml: Path,
    output_dir: Path,
    class_names: list[str],
    epochs: int,
    image_size: int,
    batch_size: int,
    base_checkpoint: Path,
) -> tuple[Path, dict]:
    if not class_names:
        raise RuntimeError("SkyDet training requires at least one object class.")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dataset = _YoloDetectionDataset(data_yaml.parent, image_size)
    loader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
        collate_fn=_collate,
    )
    model = SkyDetModel(num_classes=len(class_names)).to(device)
    if base_checkpoint.exists():
        checkpoint = torch.load(base_checkpoint, map_location="cpu")
        state = checkpoint.get("model", checkpoint)
        compatible = {
            key: value
            for key, value in state.items()
            if key in model.state_dict() and model.state_dict()[key].shape == value.shape
        }
        model.load_state_dict(compatible, strict=False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    best_loss = float("inf")
    best_path = output_dir / "skydet_best.pt"
    output_dir.mkdir(parents=True, exist_ok=True)
    history: list[float] = []

    for epoch in range(epochs):
        model.train()
        epoch_losses: list[float] = []
        for images, boxes, labels in loader:
            images = images.to(device)
            optimizer.zero_grad(set_to_none=True)
            cls_outs, reg_outs, ctr_outs = model(images)
            cls_flat, reg_flat, ctr_flat, points = _flatten_outputs(
                cls_outs, reg_outs, ctr_outs, len(class_names)
            )
            loss = torch.stack(
                [
                    _sample_loss(
                        cls_flat[index],
                        reg_flat[index],
                        ctr_flat[index],
                        points,
                        boxes[index],
                        labels[index],
                        len(class_names),
                    )
                    for index in range(images.shape[0])
                ]
            ).mean()
            if not torch.isfinite(loss):
                raise RuntimeError("SkyDet loss became non-finite.")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
            optimizer.step()
            epoch_losses.append(float(loss.detach().cpu()))

        epoch_loss = float(np.mean(epoch_losses)) if epoch_losses else float("inf")
        history.append(epoch_loss)
        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(
                {
                    "model": model.state_dict(),
                    "epoch": epoch + 1,
                    "train_loss": best_loss,
                    "class_names": class_names,
                    "image_size": image_size,
                },
                best_path,
            )

    (output_dir / "metrics.json").write_text(
        __import__("json").dumps({"train_loss": history}, separators=(",", ":")),
        encoding="utf-8",
    )
    return best_path, {
        "training_backend": "skydet_fcos",
        "best_train_loss": best_loss,
        "epochs_completed": epochs,
        "device": str(device),
    }
