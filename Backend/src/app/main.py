from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.finance.presentation.api.v1.routers import (
    accounts,
    categories,
    transactions,
    transfers,
)
from app.shared.infrastructure.config.settings import Settings
from app.shared.presentation.api.error_handlers import install_error_handlers
from app.shared.presentation.api.middleware import CacheControlMiddleware
from app.users.presentation.api.v1.routers import auth, users
from app.wiring import build_infra, install_finance, install_users


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    docs = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(
            settings.database_url.get_secret_value(), pool_pre_ping=True
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        infra = build_infra(settings, session_factory)
        install_users(app, infra)
        install_finance(app, infra)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Gerenciador de Finanças Pessoais",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    install_error_handlers(app)
    app.add_middleware(CacheControlMiddleware)
    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
            allow_credentials=False,
            expose_headers=["Retry-After"],
            max_age=600,
        )
    app.include_router(users.router)
    app.include_router(auth.router)
    app.include_router(accounts.router)
    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(transfers.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
