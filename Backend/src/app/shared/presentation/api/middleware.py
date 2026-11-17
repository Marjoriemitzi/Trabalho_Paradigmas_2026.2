from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        if (
            request.url.path.startswith("/api/v1/")
            and request.url.path != "/api/v1/categories"
        ):
            if "cache-control" not in (k.lower() for k in response.headers.keys()):
                response.headers["Cache-Control"] = "no-store"
        return response
