from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from vms_api.appsettings import get_settings
from vms_utils.ai.detected_object import DetectedObject


@dataclass(frozen=True)
class SkyDetConfig:
    class_names: tuple[str, ...] = ("airplane", "boat", "car", "ship")
    image_size: int = 640
    num_classes: int = 4
    fpn_dim: int = 64
    head_depth: int = 2
    use_depthwise_head: bool = True
    use_stride4: bool = True
    use_ghost_neck: bool = True
    ghost_ratio: int = 2
    use_se_neck: bool = False
    use_cbam_neck: bool = False
    use_dilated_conv: bool = True
    dilation_rate: int = 2
    pre_nms_topk: int = 3000


CFG = SkyDetConfig()


class ConvBNAct(nn.Module):
    def __init__(
        self,
        cin: int,
        cout: int,
        k: int,
        s: int = 1,
        p: int | None = None,
        g: int = 1,
        act: bool = True,
        dilation: int = 1,
    ) -> None:
        super().__init__()
        if p is None:
            p = (k // 2) * dilation
        self.conv = nn.Conv2d(cin, cout, k, stride=s, padding=p, groups=g, bias=False, dilation=dilation)
        self.bn = nn.BatchNorm2d(cout)
        self.act = nn.SiLU() if act else nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.act(self.bn(self.conv(x)))


class GhostConv(nn.Module):
    def __init__(self, cin: int, cout: int, k: int = 1, s: int = 1, ratio: int = 2, dilation: int = 1) -> None:
        super().__init__()
        self.cout = cout
        primary = int(math.ceil(cout / ratio))
        cheap = cout - primary
        self.primary = ConvBNAct(cin, primary, k, s=s, dilation=dilation)
        self.cheap = ConvBNAct(primary, cheap, 3, g=primary) if cheap > 0 else None

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        y = self.primary(x)
        if self.cheap is None:
            return y
        return torch.cat([y, self.cheap(y)], dim=1)[:, : self.cout, :, :]


def make_neck_conv(cin: int, cout: int, k: int = 1, s: int = 1, dilation: int = 1) -> nn.Module:
    if CFG.use_ghost_neck:
        return GhostConv(cin, cout, k=k, s=s, ratio=CFG.ghost_ratio, dilation=dilation)
    return ConvBNAct(cin, cout, k, s=s, dilation=dilation)


class SqueezeExcite(nn.Module):
    def __init__(self, c: int, r: int = 8) -> None:
        super().__init__()
        hidden = max(8, c // r)
        self.fc1 = nn.Conv2d(c, hidden, 1)
        self.fc2 = nn.Conv2d(hidden, c, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        s = F.adaptive_avg_pool2d(x, 1)
        s = F.silu(self.fc1(s))
        return x * torch.sigmoid(self.fc2(s))


class CBAM(nn.Module):
    def __init__(self, c: int, r: int = 8, k: int = 7) -> None:
        super().__init__()
        hidden = max(8, c // r)
        self.mlp1 = nn.Conv2d(c, hidden, 1)
        self.mlp2 = nn.Conv2d(hidden, c, 1)
        self.spatial = nn.Conv2d(2, 1, k, padding=k // 2, bias=False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg = F.adaptive_avg_pool2d(x, 1)
        mx = F.adaptive_max_pool2d(x, 1)
        c_att = torch.sigmoid(self.mlp2(F.silu(self.mlp1(avg))) + self.mlp2(F.silu(self.mlp1(mx))))
        x = x * c_att
        avg2 = torch.mean(x, dim=1, keepdim=True)
        mx2, _ = torch.max(x, dim=1, keepdim=True)
        return x * torch.sigmoid(self.spatial(torch.cat([avg2, mx2], dim=1)))


class PANet4(nn.Module):
    def __init__(self, in_channels: list[int]) -> None:
        super().__init__()
        c2, c3, c4, c5 = in_channels
        dilation = CFG.dilation_rate if CFG.use_dilated_conv else 1
        self.lat2 = make_neck_conv(c2, CFG.fpn_dim)
        self.lat3 = make_neck_conv(c3, CFG.fpn_dim)
        self.lat4 = make_neck_conv(c4, CFG.fpn_dim)
        self.lat5 = make_neck_conv(c5, CFG.fpn_dim)
        self.out2 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.out3 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.out4 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.out5 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.down23 = ConvBNAct(CFG.fpn_dim, CFG.fpn_dim, 3, s=2)
        self.down34 = ConvBNAct(CFG.fpn_dim, CFG.fpn_dim, 3, s=2)
        self.down45 = ConvBNAct(CFG.fpn_dim, CFG.fpn_dim, 3, s=2)
        self.pan3 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.pan4 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.pan5 = make_neck_conv(CFG.fpn_dim, CFG.fpn_dim, k=3, dilation=dilation)
        self.se2 = SqueezeExcite(CFG.fpn_dim) if CFG.use_se_neck else None
        self.se3 = SqueezeExcite(CFG.fpn_dim) if CFG.use_se_neck else None
        self.se4 = SqueezeExcite(CFG.fpn_dim) if CFG.use_se_neck else None
        self.se5 = SqueezeExcite(CFG.fpn_dim) if CFG.use_se_neck else None
        self.cb2 = CBAM(CFG.fpn_dim) if CFG.use_cbam_neck else None
        self.cb3 = CBAM(CFG.fpn_dim) if CFG.use_cbam_neck else None
        self.cb4 = CBAM(CFG.fpn_dim) if CFG.use_cbam_neck else None
        self.cb5 = CBAM(CFG.fpn_dim) if CFG.use_cbam_neck else None

    def _att(self, x: torch.Tensor, se: nn.Module | None, cb: nn.Module | None) -> torch.Tensor:
        if se is not None:
            x = se(x)
        if cb is not None:
            x = cb(x)
        return x

    def forward(self, feats: list[torch.Tensor]) -> list[torch.Tensor]:
        c2, c3, c4, c5 = feats
        p2 = self.lat2(c2)
        p3 = self.lat3(c3)
        p4 = self.lat4(c4)
        p5 = self.lat5(c5)
        p4 = p4 + F.interpolate(p5, size=p4.shape[-2:], mode="nearest")
        p3 = p3 + F.interpolate(p4, size=p3.shape[-2:], mode="nearest")
        p2 = p2 + F.interpolate(p3, size=p2.shape[-2:], mode="nearest")
        p2 = self._att(self.out2(p2), self.se2, self.cb2)
        p3 = self._att(self.out3(p3), self.se3, self.cb3)
        p4 = self._att(self.out4(p4), self.se4, self.cb4)
        p5 = self._att(self.out5(p5), self.se5, self.cb5)
        n3 = self.pan3(p3 + self.down23(p2))
        n4 = self.pan4(p4 + self.down34(n3))
        n5 = self.pan5(p5 + self.down45(n4))
        return [p2, n3, n4, n5]


class Scale(nn.Module):
    def __init__(self, init: float = 1.0) -> None:
        super().__init__()
        self.s = nn.Parameter(torch.tensor(init, dtype=torch.float32))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x * self.s


class DepthwiseSeparableConv(nn.Module):
    def __init__(self, c: int, dilation: int = 1) -> None:
        super().__init__()
        self.dw = nn.Conv2d(c, c, 3, padding=dilation, groups=c, bias=False, dilation=dilation)
        self.pw = nn.Conv2d(c, c, 1, bias=False)
        self.gn = nn.GroupNorm(16, c)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return F.silu(self.gn(self.pw(self.dw(x))))


class FCOSHead(nn.Module):
    def __init__(self, num_classes: int = CFG.num_classes) -> None:
        super().__init__()
        self.num_classes = num_classes
        dilation = CFG.dilation_rate if CFG.use_dilated_conv else 1

        def tower() -> nn.Sequential:
            return nn.Sequential(*[DepthwiseSeparableConv(CFG.fpn_dim, dilation=dilation) for _ in range(CFG.head_depth)])

        self.cls_tower = tower()
        self.reg_tower = tower()
        self.cls_logits = nn.Conv2d(CFG.fpn_dim, num_classes, 3, padding=1)
        self.bbox_pred = nn.Conv2d(CFG.fpn_dim, 4, 3, padding=1)
        self.ctr_logits = nn.Conv2d(CFG.fpn_dim, 1, 3, padding=1)
        self.scales = nn.ModuleList([Scale(1.0) for _ in range(4)])

    def forward(self, feats: list[torch.Tensor]) -> tuple[list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
        cls_out, reg_out, ctr_out = [], [], []
        for i, x in enumerate(feats):
            c = self.cls_tower(x)
            r = self.reg_tower(x)
            cls_out.append(self.cls_logits(c))
            reg_out.append(F.relu(self.scales[i](self.bbox_pred(r))).clamp(0.0, 256.0))
            ctr_out.append(self.ctr_logits(r))
        return cls_out, reg_out, ctr_out


class MobileNetV3SmallBackbone(nn.Module):
    def __init__(self, probe_size: int = 256) -> None:
        super().__init__()
        import torchvision
        from torchvision.models.feature_extraction import create_feature_extractor

        model = torchvision.models.mobilenet_v3_small(weights=None)
        self.features = model.features
        self.extractor = create_feature_extractor(
            self.features,
            return_nodes={"1": "c2", "2": "c3", "7": "c4", "12": "c5"},
        )
        with torch.no_grad():
            out = self.extractor(torch.zeros(1, 3, probe_size, probe_size))
            self.out_channels = [int(out[key].shape[1]) for key in ("c2", "c3", "c4", "c5")]

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        out = self.extractor(x)
        return [out["c2"], out["c3"], out["c4"], out["c5"]]


class SkyDetModel(nn.Module):
    def __init__(self, num_classes: int = CFG.num_classes) -> None:
        super().__init__()
        self.backbone = MobileNetV3SmallBackbone()
        self.neck = PANet4(self.backbone.out_channels)
        self.head = FCOSHead(num_classes=num_classes)

    def forward(self, x: torch.Tensor) -> tuple[list[torch.Tensor], list[torch.Tensor], list[torch.Tensor]]:
        return self.head(self.neck(self.backbone(x)))


def _make_points(h: int, w: int, stride: int, device: torch.device) -> torch.Tensor:
    ys = torch.arange(h, device=device) * stride + stride * 0.5
    xs = torch.arange(w, device=device) * stride + stride * 0.5
    yy, xx = torch.meshgrid(ys, xs, indexing="ij")
    return torch.stack([xx, yy], dim=-1).reshape(-1, 2)


def _xyxy_from_points_ltrb(points_xy: torch.Tensor, ltrb: torch.Tensor) -> torch.Tensor:
    x, y = points_xy[:, 0], points_xy[:, 1]
    l, t, r, b = ltrb.unbind(-1)
    return torch.stack([x - l, y - t, x + r, y + b], dim=-1)


def _nms_xyxy(boxes: torch.Tensor, scores: torch.Tensor, threshold: float) -> torch.Tensor:
    if boxes.numel() == 0:
        return torch.empty((0,), dtype=torch.long, device=boxes.device)
    x1, y1, x2, y2 = boxes.unbind(-1)
    areas = (x2 - x1).clamp(min=0) * (y2 - y1).clamp(min=0)
    order = scores.argsort(descending=True)
    keep: list[torch.Tensor] = []
    while order.numel() > 0:
        i = order[0]
        keep.append(i)
        if order.numel() == 1:
            break
        rest = order[1:]
        xx1 = torch.maximum(x1[i], x1[rest])
        yy1 = torch.maximum(y1[i], y1[rest])
        xx2 = torch.minimum(x2[i], x2[rest])
        yy2 = torch.minimum(y2[i], y2[rest])
        inter = (xx2 - xx1).clamp(min=0) * (yy2 - yy1).clamp(min=0)
        iou = inter / (areas[i] + areas[rest] - inter + 1e-6)
        order = rest[iou <= threshold]
    return torch.stack(keep)


def _letterbox_resize(img: np.ndarray, out_size: int) -> tuple[np.ndarray, dict[str, float]]:
    h0, w0 = img.shape[:2]
    scale = out_size / max(h0, w0)
    nh = int(round(h0 * scale))
    nw = int(round(w0 * scale))
    resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_LINEAR)
    top = (out_size - nh) // 2
    left = (out_size - nw) // 2
    canvas = np.zeros((out_size, out_size, 3), dtype=resized.dtype)
    canvas[top : top + nh, left : left + nw] = resized
    return canvas, {
        "orig_h": float(h0),
        "orig_w": float(w0),
        "scale": float(scale),
        "pad_left": float(left),
        "pad_top": float(top),
    }


class SkyDetDetector:
    """SkyDet adapter for the same detection contract used by the video pipeline."""

    def __init__(self, model_path: Path | None = None) -> None:
        self._settings = get_settings()
        self._model_path = Path(model_path or self._settings.skydet_model_path)
        self._model: SkyDetModel | None = None
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._class_names = tuple(CFG.class_names)
        self._num_classes = len(self._class_names)
        self._points: torch.Tensor | None = None
        self._level_slices: list[tuple[int, int]] = []
        self._load_attempted = False
        self._box_expansion_ratio = min(
            0.25,
            max(0.0, float(os.getenv("SKYDET_BOX_EXPANSION_RATIO", "0.08"))),
        )
        self.load_error: str | None = None

    def _load_model(self) -> None:
        if self._load_attempted:
            return
        self._load_attempted = True
        if not self._model_path.exists():
            self.load_error = f"SkyDet model not found: {self._model_path}"
            return
        try:
            checkpoint: dict[str, Any] = torch.load(self._model_path, map_location="cpu")
            checkpoint_class_names = checkpoint.get("class_names") if isinstance(checkpoint, dict) else None
            if checkpoint_class_names:
                self._class_names = tuple(str(name) for name in checkpoint_class_names)
                self._num_classes = len(self._class_names)
            model = SkyDetModel(num_classes=self._num_classes).to(self._device)
            state_dict = checkpoint.get("model", checkpoint)
            model.load_state_dict(state_dict, strict=True)
            model.eval()
            self._model = model
            self.load_error = None
        except Exception as error:
            self._model = None
            self.load_error = str(error)

    @torch.no_grad()
    def _build_points(self, cls_outs: list[torch.Tensor]) -> None:
        """Build the fixed anchor-point grid from a real forward pass.

        The old implementation ran a second, dummy 640x640 inference while loading
        the model only to discover these shapes. Building the grid from the first
        real result keeps exactly the same geometry and removes a large first-call
        latency penalty, especially on CPU.
        """

        all_points: list[torch.Tensor] = []
        self._level_slices = []
        start = 0
        for level, stride in enumerate((4, 8, 16, 32)):
            height, width = cls_outs[level].shape[-2], cls_outs[level].shape[-1]
            points = _make_points(height, width, stride, self._device)
            all_points.append(points)
            end = start + points.shape[0]
            self._level_slices.append((start, end))
            start = end
        self._points = torch.cat(all_points, dim=0)

    @torch.no_grad()
    def detect(
        self,
        frame: np.ndarray,
        confidence_threshold: float,
        iou_threshold: float,
        max_detections: int,
    ) -> list[DetectedObject]:
        self._load_model()
        if self._model is None:
            return []
        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            letterboxed, meta = _letterbox_resize(rgb, CFG.image_size)
            tensor = torch.from_numpy(letterboxed).permute(2, 0, 1).float().unsqueeze(0) / 255.0
            tensor = tensor.to(self._device)
            use_amp = self._device.type == "cuda"
            with torch.amp.autocast(device_type="cuda", enabled=use_amp):
                cls_outs, reg_outs, ctr_outs = self._model(tensor)
            if self._points is None:
                self._build_points(cls_outs)
            if self._points is None:
                self.load_error = "SkyDet output grid could not be initialized."
                return []
            self.load_error = None
            return self._decode(cls_outs, reg_outs, ctr_outs, meta, confidence_threshold, iou_threshold, max_detections)
        except Exception as error:
            self.load_error = str(error)
            return []

    def _decode(
        self,
        cls_outs: list[torch.Tensor],
        reg_outs: list[torch.Tensor],
        ctr_outs: list[torch.Tensor],
        meta: dict[str, float],
        score_threshold: float,
        nms_threshold: float,
        max_detections: int,
    ) -> list[DetectedObject]:
        cls_logits = torch.cat(
            [c[0].permute(1, 2, 0).reshape(-1, self._num_classes) for c in cls_outs],
            dim=0,
        )
        reg_pred = torch.cat([r[0].permute(1, 2, 0).reshape(-1, 4) for r in reg_outs], dim=0)
        ctr_logits = torch.cat([t[0].permute(1, 2, 0).reshape(-1) for t in ctr_outs], dim=0)
        scores, labels = torch.sigmoid(cls_logits).max(dim=-1)
        scores = scores * torch.sigmoid(ctr_logits)

        keep = scores > score_threshold
        if keep.sum() == 0:
            return []

        points = self._points[keep]
        boxes = _xyxy_from_points_ltrb(points, reg_pred[keep])
        scores_k = scores[keep]
        labels_k = labels[keep]

        if scores_k.numel() > CFG.pre_nms_topk:
            topk = torch.topk(scores_k, k=CFG.pre_nms_topk, largest=True).indices
            boxes = boxes[topk]
            scores_k = scores_k[topk]
            labels_k = labels_k[topk]

        keep_all: list[torch.Tensor] = []
        for class_id in range(self._num_classes):
            class_indices = torch.where(labels_k == class_id)[0]
            if class_indices.numel() == 0:
                continue
            keep_all.append(class_indices[_nms_xyxy(boxes[class_indices], scores_k[class_indices], nms_threshold)])
        if not keep_all:
            return []

        keep_idx = torch.cat(keep_all, dim=0)
        keep_idx = keep_idx[scores_k[keep_idx].argsort(descending=True)][:max_detections]
        boxes_np = boxes[keep_idx].detach().cpu().numpy()
        scores_np = scores_k[keep_idx].detach().cpu().numpy()
        labels_np = labels_k[keep_idx].detach().cpu().numpy()

        scale = meta["scale"]
        left = meta["pad_left"]
        top = meta["pad_top"]
        original_w = meta["orig_w"]
        original_h = meta["orig_h"]
        boxes_np[:, 0] = np.clip((boxes_np[:, 0] - left) / scale, 0, original_w - 1)
        boxes_np[:, 1] = np.clip((boxes_np[:, 1] - top) / scale, 0, original_h - 1)
        boxes_np[:, 2] = np.clip((boxes_np[:, 2] - left) / scale, 0, original_w - 1)
        boxes_np[:, 3] = np.clip((boxes_np[:, 3] - top) / scale, 0, original_h - 1)

        if self._box_expansion_ratio > 0:
            widths = np.maximum(1.0, boxes_np[:, 2] - boxes_np[:, 0])
            heights = np.maximum(1.0, boxes_np[:, 3] - boxes_np[:, 1])
            expand_x = widths * self._box_expansion_ratio
            expand_y = heights * self._box_expansion_ratio
            boxes_np[:, 0] = np.clip(boxes_np[:, 0] - expand_x, 0, original_w - 1)
            boxes_np[:, 1] = np.clip(boxes_np[:, 1] - expand_y, 0, original_h - 1)
            boxes_np[:, 2] = np.clip(boxes_np[:, 2] + expand_x, 0, original_w - 1)
            boxes_np[:, 3] = np.clip(boxes_np[:, 3] + expand_y, 0, original_h - 1)

        detections: list[DetectedObject] = []
        for box, score, label in zip(boxes_np, scores_np, labels_np):
            class_id = int(label)
            detections.append(
                DetectedObject.create(
                    class_id,
                    self._class_names[class_id],
                    float(score),
                    float(box[0]),
                    float(box[1]),
                    float(box[2]),
                    float(box[3]),
                )
            )
        return detections
