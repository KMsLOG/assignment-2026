class AppException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}


class NotFoundException(AppException):
    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=404, code=code, message=message, details=details)


class ConflictException(AppException):
    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=409, code=code, message=message, details=details)


class BadRequestException(AppException):
    def __init__(self, code: str, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(status_code=400, code=code, message=message, details=details)
