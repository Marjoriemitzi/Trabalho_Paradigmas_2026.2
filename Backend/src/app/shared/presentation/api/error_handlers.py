import re
from collections.abc import Sequence
from http import HTTPStatus
from typing import TypedDict

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.presentation.api.errors import ApiError, error_response


def _code_for_status(status_code: int) -> str:
    return re.sub(r"[^a-z]+", "_", HTTPStatus(status_code).phrase.lower())


class _ValidationDetail(TypedDict):
    """Só os campos que usamos de cada erro do pydantic (o dicionário traz mais)."""

    type: str
    loc: Sequence[str | int]


def _field_problem(error: _ValidationDetail) -> dict[str, str | None]:
    problema = error["type"]
    local = error["loc"]
    campo = None if problema == "json_invalid" else ".".join(map(str, local[1:]))
    return {"field": campo or None, "problem": problema}


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        if isinstance(exc, ApiError):
            code = exc.code
        else:
            code = _code_for_status(exc.status_code)
        return error_response(exc.status_code, code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_request",
            fields=[_field_problem(erro) for erro in exc.errors()],
        )

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        return error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "internal_error")
