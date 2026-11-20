"""Monta as dependências concretas, para a API e para os comandos de linha."""

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.composition import (
    create_account_factory,
    create_transfer_factory,
    delete_account_factory,
    delete_transaction_factory,
    delete_transfer_factory,
    get_statement_factory,
    list_accounts_factory,
    list_categories_factory,
    list_transfers_factory,
    record_transaction_factory,
    rename_account_factory,
    update_transaction_factory,
    update_transfer_factory,
)
from app.finance.domain.services.categorizer import Categorizer
from app.finance.infrastructure.prolog.prolog_categorizer import PrologCategorizer
from app.shared.domain.clock import Clock as DayClock
from app.shared.infrastructure.clock import ZoneInfoClock
from app.shared.infrastructure.config.settings import Settings
from app.shared.infrastructure.prolog.gateway import PrologGateway
from app.users.application.attempts import AttemptGuard, AttemptLimits
from app.users.application.ports.clock import Clock as InstantClock
from app.users.application.ports.password_hasher import PasswordHasher
from app.users.application.session import SessionIssuer
from app.users.composition import (
    authenticate_user_factory,
    change_password_factory,
    delete_user_factory,
    get_current_user_factory,
    logout_factory,
    refresh_session_factory,
    register_user_factory,
)
from app.users.domain.services.password_policy import PasswordPolicy
from app.users.infrastructure.persistence.access_token_check import SqlAccessTokenCheck
from app.users.infrastructure.persistence.sql_attempt_limiter import SqlAttemptLimiter
from app.users.infrastructure.prolog.prolog_password_policy import (
    PrologPasswordPolicy,
)
from app.users.infrastructure.security.argon2_hasher import Argon2Hasher
from app.users.infrastructure.security.jwt_token_issuer import JwtTokenIssuer
from app.users.infrastructure.security.jwt_token_verifier import JwtTokenVerifier
from app.users.infrastructure.security.secrets_refresh_token_generator import (
    SecretsRefreshTokenGenerator,
)
from app.users.infrastructure.system_clock import SystemClock


@dataclass(frozen=True, slots=True)
class Infra:
    settings: Settings
    session_factory: async_sessionmaker[AsyncSession]
    hasher: PasswordHasher
    password_policy: PasswordPolicy
    instant_clock: InstantClock
    day_clock: DayClock
    categorizer: Categorizer
    checks: tuple[TransactionCheck, ...]


def build_infra(
    settings: Settings, session_factory: async_sessionmaker[AsyncSession]
) -> Infra:
    prolog = PrologGateway()
    return Infra(
        settings=settings,
        session_factory=session_factory,
        hasher=Argon2Hasher(),
        password_policy=PrologPasswordPolicy(prolog, settings.prolog_rules_dir),
        instant_clock=SystemClock(),
        day_clock=ZoneInfoClock(ZoneInfo(settings.timezone)),
        categorizer=PrologCategorizer(prolog, settings.prolog_rules_dir),
        checks=(),
    )


def _attempt_guard(infra: Infra) -> AttemptGuard:
    s = infra.settings
    return AttemptGuard(
        limiter=SqlAttemptLimiter(infra.session_factory),
        clock=infra.instant_clock,
        limits=AttemptLimits(
            login_pair_max_failures=s.login_pair_max_failures,
            login_ip_max_failures=s.login_ip_max_failures,
            login_window=timedelta(minutes=s.login_window_minutes),
            register_ip_max=s.register_ip_max,
            register_window=timedelta(minutes=s.register_window_minutes),
        ),
    )


def _session_issuer(infra: Infra) -> SessionIssuer:
    s = infra.settings
    return SessionIssuer(
        tokens=JwtTokenIssuer(
            secret=s.jwt_secret.get_secret_value(),
            expires_in=timedelta(minutes=s.jwt_expires_minutes),
        ),
        generator=SecretsRefreshTokenGenerator(),
        clock=infra.instant_clock,
        refresh_ttl=timedelta(days=s.refresh_token_days),
    )


def install_users(app: FastAPI, infra: Infra) -> None:
    sessions = infra.session_factory
    issuer = _session_issuer(infra)
    attempts = _attempt_guard(infra)
    app.state.register_user = register_user_factory(
        session_factory=sessions,
        hasher=infra.hasher,
        policy=infra.password_policy,
        attempts=attempts,
    )
    app.state.authenticate_user = authenticate_user_factory(
        session_factory=sessions,
        hasher=infra.hasher,
        issuer=issuer,
        attempts=attempts,
    )
    app.state.change_password = change_password_factory(
        session_factory=sessions, hasher=infra.hasher, policy=infra.password_policy
    )
    app.state.delete_user = delete_user_factory(
        session_factory=sessions, hasher=infra.hasher
    )
    app.state.refresh_session = refresh_session_factory(
        session_factory=sessions, issuer=issuer, clock=infra.instant_clock
    )
    app.state.logout = logout_factory(sessions, infra.instant_clock)
    app.state.get_current_user = get_current_user_factory(sessions)
    app.state.access_token_check = SqlAccessTokenCheck(sessions)
    app.state.token_verifier = JwtTokenVerifier(
        secret=infra.settings.jwt_secret.get_secret_value()
    )


def install_finance(app: FastAPI, infra: Infra) -> None:
    sessions = infra.session_factory
    app.state.clock = infra.day_clock
    app.state.record_transaction = record_transaction_factory(
        session_factory=sessions, categorizer=infra.categorizer, checks=infra.checks
    )
    app.state.update_transaction = update_transaction_factory(
        session_factory=sessions, categorizer=infra.categorizer, checks=infra.checks
    )
    app.state.delete_transaction = delete_transaction_factory(sessions)
    app.state.get_statement = get_statement_factory(sessions)
    app.state.create_transfer = create_transfer_factory(sessions)
    app.state.update_transfer = update_transfer_factory(sessions)
    app.state.delete_transfer = delete_transfer_factory(sessions)
    app.state.list_transfers = list_transfers_factory(sessions)
    app.state.create_account = create_account_factory(sessions)
    app.state.list_accounts = list_accounts_factory(sessions)
    app.state.rename_account = rename_account_factory(sessions)
    app.state.delete_account = delete_account_factory(sessions)
    app.state.list_categories = list_categories_factory(sessions)
