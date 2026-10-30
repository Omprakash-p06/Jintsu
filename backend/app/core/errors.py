class JintruError(Exception):
    """Base domain exception for Reality Check AI."""

    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        detail: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.detail = detail


class ProviderTimeoutError(JintruError):
    """Raised when an external search or model provider times out or SLA budget expires."""

    def __init__(
        self,
        message: str = "External provider timed out",
        code: str = "PROVIDER_TIMEOUT",
        detail: str | None = None,
    ):
        super().__init__(message, code=code, detail=detail)


class ProviderUnavailableError(JintruError):
    """Raised when an external search or model provider encounters an HTTP or connection error."""

    def __init__(
        self,
        message: str = "External provider unavailable",
        code: str = "PROVIDER_UNAVAILABLE",
        detail: str | None = None,
    ):
        super().__init__(message, code=code, detail=detail)


class RequestConstraintError(JintruError):
    """Raised when input validation fails (e.g., compound claims or length > 500 chars)."""

    def __init__(
        self,
        message: str = "Request constraint violated",
        code: str = "REQUEST_CONSTRAINT_ERROR",
        detail: str | None = None,
    ):
        super().__init__(message, code=code, detail=detail)
