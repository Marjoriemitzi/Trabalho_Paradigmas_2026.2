import re
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.presentation.api.errors import ApiError, error_response


def _code_for_status(status_code: int) -> str:
    return re.sub(r"[^a-z]+", "_", HTTPStatus(status_code).phrase.lower())


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if isinstance(exc, ApiError):
            code = exc.code
        else:
            code = _code_for_status(exc.status_code)
        return error_response(exc.status_code, code, headers=exc.headers)
