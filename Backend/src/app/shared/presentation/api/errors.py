from collections.abc import Mapping

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def error_response(
    status_code: int,
    code: str,
    *,
    headers: Mapping[str, str] | None = None,
    **extra: object,
) -> JSONResponse:
    return JSONResponse(
        {"error": code, **extra}, status_code=status_code, headers=headers
    )


class ApiError(HTTPException):
    def __init__(
        self, status_code: int, code: str, *, headers: Mapping[str, str] | None = None
    ) -> None:
        super().__init__(status_code=status_code, detail=code, headers=headers)
        self.code = code
