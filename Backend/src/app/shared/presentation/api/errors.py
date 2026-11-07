from collections.abc import Mapping

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
