"""
Custom exception hierarchy for consistent API error responses.

Follows RFC 7807 (Problem Details for HTTP APIs) for structured error responses.
See: https://datatracker.ietf.org/doc/html/rfc7807

Usage in routes/services:
    raise NotFoundError("User", user_id)
    raise ConflictError("Email already registered")
    raise AuthenticationError("Invalid credentials")
    raise ValidationError("Password must be at least 8 characters")

Register the handler in main.py:
    @app.exception_handler(AppException)
    async def app_exception_handler(request, exc): ...
"""


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str | None = None,
        type: str = "about:blank",
        title: str | None = None,
        instance: str | None = None,
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.type = type
        self.title = title or str(status_code)
        self.instance = instance


class NotFoundError(AppException):
    def __init__(self, entity: str, entity_id: int | str):
        super().__init__(
            status_code=404,
            detail=f"{entity} with id {entity_id} not found",
            error_code="NOT_FOUND",
            type="/problems/not-found",
            title="Not Found",
        )


class ConflictError(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=409,
            detail=detail,
            error_code="CONFLICT",
            type="/problems/conflict",
            title="Conflict",
        )


class AuthenticationError(AppException):
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=401,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            type="/problems/authentication-error",
            title="Authentication Error",
        )


class ValidationError(AppException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=422,
            detail=detail,
            error_code="VALIDATION_ERROR",
            type="/problems/validation-error",
            title="Validation Error",
        )
