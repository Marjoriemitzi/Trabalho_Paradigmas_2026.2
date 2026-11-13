from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.composition import (
    create_account_factory,
    create_transfer_factory,
    delete_transaction_factory,
    delete_transfer_factory,
    get_statement_factory,
    list_accounts_factory,
    list_categories_factory,
    record_transaction_factory,
    update_transaction_factory,
)
from app.finance.infrastructure.prolog.prolog_categorizer import PrologCategorizer
from app.finance.presentation.api.v1.routers import (
    accounts,
    categories,
    transactions,
    transfers,
)
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
    settings = settings or Settings()
    docs = settings.enable_docs

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
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

        checks: tuple[TransactionCheck, ...] = ()
        categorizer = PrologCategorizer(prolog, settings.prolog_rules_dir)
        app.state.record_transaction = record_transaction_factory(
            session_factory=session_factory, categorizer=categorizer, checks=checks
        )
        app.state.update_transaction = update_transaction_factory(
            session_factory=session_factory, categorizer=categorizer, checks=checks
        )
        app.state.delete_transaction = delete_transaction_factory(session_factory)
        app.state.create_transfer = create_transfer_factory(session_factory)
        app.state.delete_transfer = delete_transfer_factory(session_factory)
        app.state.get_statement = get_statement_factory(session_factory)
        app.state.create_account = create_account_factory(session_factory)
        app.state.list_accounts = list_accounts_factory(session_factory)
        app.state.list_categories = list_categories_factory(session_factory)
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
    app.include_router(accounts.router)
    app.include_router(categories.router)
    app.include_router(transactions.router)
    app.include_router(transfers.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
