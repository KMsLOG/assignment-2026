"""Application-level custom exceptions with HTTP status mapping."""

class AppException(Exception):
    """Base exception carrying status code, error code, and details."""

    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        """Initialize a structured exception payload."""
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class NotFoundException(AppException):
    """Exception for missing resources."""

    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize a 404 not-found exception."""
        super().__init__(status_code=404, code=code, message=message, details=details)


class ConflictException(AppException):
    """Exception for business rule conflicts."""

    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize a 409 conflict exception."""
        super().__init__(status_code=409, code=code, message=message, details=details)


class BadRequestException(AppException):
    """Exception for invalid client requests."""

    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize a 400 bad-request exception."""
        super().__init__(status_code=400, code=code, message=message, details=details)


class ServiceUnavailableException(AppException):
    """Exception for temporary service unavailability."""

    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        """Initialize a 503 service-unavailable exception."""
        super().__init__(status_code=503, code=code, message=message, details=details)
