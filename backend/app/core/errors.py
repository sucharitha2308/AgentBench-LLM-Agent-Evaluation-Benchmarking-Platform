from typing import Any, Dict, Optional
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class AgentBenchException(HTTPException):
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str = "ERROR",
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.extra = extra or {}


class NotFoundException(AgentBenchException):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{resource} with ID '{identifier}' not found.",
            error_code="RESOURCE_NOT_FOUND",
            extra={"resource": resource, "id": str(identifier)}
        )


class UnauthorizedException(AgentBenchException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="UNAUTHORIZED"
        )


class ForbiddenException(AgentBenchException):
    def __init__(self, detail: str = "You do not have permission to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="FORBIDDEN"
        )


class BadRequestException(AgentBenchException):
    def __init__(self, detail: str, error_code: str = "BAD_REQUEST", extra: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code=error_code,
            extra=extra
        )


class ProviderException(AgentBenchException):
    def __init__(self, provider: str, detail: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Provider '{provider}' error: {detail}",
            error_code="PROVIDER_ERROR",
            extra={"provider": provider}
        )


async def agentbench_exception_handler(request: Request, exc: AgentBenchException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "extra": exc.extra
            }
        }
    )
