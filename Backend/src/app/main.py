from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.shared.infrastructure.config.settings import Settings
from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.shared.presentation.api.error_handlers import install_error_handlers
from app.users.composition import (
    authenticate_user_factory,
    get_current_user_factory,
    register_user_factory,
)
from app.users.infrastructure.prolog.prolog_password_policy import (
    PrologPasswordPolicy,
)
from app.users.infrastructure.security.argon2_hasher import Argon2Hasher
from app.users.infrastructure.security.jwt_token_issuer import JwtTokenIssuer
from app.users.infrastructure.security.jwt_token_verifier import JwtTokenVerifier
from app.users.presentation.api.v1.routers import auth, users


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
        hasher = Argon2Hasher()

        app.state.register_user = register_user_factory(
            session_factory=session_factory,
            hasher=hasher,
            policy=PrologPasswordPolicy(prolog, settings.prolog_rules_dir),
        )

        jwt_secret = settings.jwt_secret.get_secret_value()

        app.state.authenticate_user = authenticate_user_factory(
            session_factory=session_factory,
            hasher=hasher,
            tokens=JwtTokenIssuer(
                secret=jwt_secret,
                expires_in=timedelta(minutes=settings.jwt_expires_minutes),
            ),
        )

        app.state.token_verifier = JwtTokenVerifier(secret=jwt_secret)
        app.state.get_current_user = get_current_user_factory(session_factory)

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
    app.include_router(users.router)
    app.include_router(auth.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
