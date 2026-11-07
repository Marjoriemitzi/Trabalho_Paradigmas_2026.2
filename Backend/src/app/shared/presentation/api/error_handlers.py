import re
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.shared.presentation.api.errors import ApiError, error_response


def _code_for_status(status_code: int) -> str:
    return re.sub(r"[^a-z]+", "_", HTTPStatus(status_code).phrase.lower())


def _field_problem(error: Mapping[str, Any]) -> dict[str, str | None]:
    problema: str = error["type"]
    local: Sequence[str | int] = error["loc"]
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
