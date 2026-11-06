from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.shared.infrastructure.config.settings import Settings
from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.users.composition import register_user_factory
from app.users.infrastructure.prolog.prolog_password_policy import (
    PrologPasswordPolicy,
)
from app.users.infrastructure.security.argon2_hasher import Argon2Hasher
from app.users.presentation.api.v1.routers import users


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    docs = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
        engine = create_async_engine(
            settings.database_url.get_secret_value(), pool_pre_ping=True
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        prolog = PrologGateway()

        app.state.register_user = register_user_factory(
            session_factory=session_factory,
            hasher=Argon2Hasher(),
            policy=PrologPasswordPolicy(prolog, settings.prolog_rules_dir),
        )
        yield
        await engine.dispose()

    app = FastAPI(
        title="Gerenciador de Finanças Pessoais",
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )
    app.include_router(users.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
