class BaseService:
    """Base service class for shared service-layer behavior."""

    def normalize_label(self, label: str | None) -> str:
        if not label:
            return ""
        return "_".join(label.strip().lower().replace("-", "_").split())
