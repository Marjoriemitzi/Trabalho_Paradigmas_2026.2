from collections.abc import Awaitable, Callable
from typing import override

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

PREFIXO = "/api/v1/"
SEM_NO_STORE = frozenset({"/api/v1/categories"})


class CacheControlMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        resposta = await call_next(request)
        caminho = request.url.path
        if (
            caminho.startswith(PREFIXO)
            and caminho not in SEM_NO_STORE
            and "cache-control" not in resposta.headers
        ):
            resposta.headers["Cache-Control"] = "no-store"
        return resposta
