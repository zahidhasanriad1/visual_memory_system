from pathlib import Path
from fastapi.responses import FileResponse
from vms_api.appsettings import get_settings
from vms_utils.storage.safe_path_resolver import SafePathResolver

class MediaService:
    """Secure generated media access service."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._resolver = SafePathResolver()

    def get_video_file(self, filename: str) -> FileResponse:
        path = self._resolver.resolve_child(self._settings.output_dir / "video_memory_videos", filename, {".mp4", ".m4v", ".avi", ".mov", ".mkv", ".webm"})
        return FileResponse(path)

    def get_report_file(self, filename: str) -> FileResponse:
        path = self._resolver.resolve_child(self._settings.output_dir / "video_memory_reports", filename, {".json"})
        return FileResponse(path, media_type="application/json")
