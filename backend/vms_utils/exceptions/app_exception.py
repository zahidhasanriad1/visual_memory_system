class AppException(Exception):
    """Base application exception safe for frontend response mapping."""

    def __init__(self, message: str, status_code: int = 400, data: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.data = data or {}
