import ast
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Protocol, cast

from fastapi import FastAPI, Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.shared.infrastructure.config.settings import Settings
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInteractor,
)
from app.users.application.use_cases.change_password import ChangePasswordInteractor
from app.users.application.use_cases.delete_user import DeleteUserInteractor
from app.users.application.use_cases.get_current_user import GetCurrentUserInteractor
from app.users.application.use_cases.logout import LogoutInteractor
from app.users.application.use_cases.refresh_session import RefreshSessionInteractor
from app.users.application.use_cases.register_user import RegisterUserInteractor
from app.users.composition import (
    authenticate_user_factory,
    change_password_factory,
    delete_user_factory,
    get_current_user_factory,
    logout_factory,
    refresh_session_factory,
    register_user_factory,
)
from app.users.infrastructure.persistence.access_token_check import SqlAccessTokenCheck
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.users.infrastructure.security.jwt_token_verifier import JwtTokenVerifier
from app.users.presentation.api.v1.controllers.authenticate_user_controller import (
    AuthenticateUserController,
)
from app.users.presentation.api.v1.controllers.change_password_controller import (
    ChangePasswordController,
)
from app.users.presentation.api.v1.controllers.delete_user_controller import (
    DeleteUserController,
)
from app.users.presentation.api.v1.controllers.get_current_user_controller import (
    GetCurrentUserController,
)
from app.users.presentation.api.v1.controllers.logout_controller import LogoutController
from app.users.presentation.api.v1.controllers.refresh_session_controller import (
    RefreshSessionController,
)
from app.users.presentation.api.v1.controllers.register_user_controller import (
    RegisterUserController,
)
from app.users.presentation.api.v1.dependencies import (
    get_authenticate_user_controller,
    get_change_password_controller,
    get_current_user_controller,
    get_delete_user_controller,
    get_logout_controller,
    get_refresh_session_controller,
    get_register_user_controller,
)
from app.wiring import Infra, install_users
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules
from tests.shared.fakes.fixed_clock import FixedClock
from tests.users.fakes.authenticate_user_presenter_spy import (
    AuthenticateUserPresenterSpy,
)
from tests.users.fakes.change_password_presenter_spy import ChangePasswordPresenterSpy
from tests.users.fakes.delete_user_presenter_spy import DeleteUserPresenterSpy
from tests.users.fakes.fake_attempt_guard import fake_attempt_guard
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.get_current_user_presenter_spy import GetCurrentUserPresenterSpy
from tests.users.fakes.refresh_session_presenter_spies import (
    LogoutPresenterSpy,
    RefreshSessionPresenterSpy,
)
from tests.users.fakes.register_user_presenter_spy import RegisterUserPresenterSpy

APP_DIR = Path(__file__).resolve().parents[3] / "src" / "app"


class _InteractorComUow(Protocol):
    @property
    def uow(self) -> object: ...
    @property
    def presenter(self) -> object: ...


class _ControllerComFabrica(Protocol):
    @property
    def build_interactor(self) -> object: ...


def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker[AsyncSession]()


def _fake_infra(sessions: async_sessionmaker[AsyncSession]) -> Infra:
    from app.finance.domain.value_objects.category import Category

    settings = Settings(
        database_url=SecretStr("postgresql+asyncpg://u:s@localhost/finance"),
        prolog_rules_dir=Path("rules"),
        jwt_secret=SecretStr("s" * 32),
    )
    return Infra(
        settings=settings,
        session_factory=sessions,
        hasher=FakePasswordHasher(),
        password_policy=FakePasswordPolicy(),
        instant_clock=FakeClock(),
        day_clock=FixedClock(date(2026, 11, 20)),
        categorizer=FakeCategorizer(Category("outros")),
        recurrence_rules=FakeRecurrenceRules(),
        checks=(),
    )


def _chaves_lidas(arquivo: Path) -> set[str]:
    arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
    chaves: set[str] = set()
    for no in ast.walk(arvore):
        if (
            isinstance(no, ast.Attribute)
            and isinstance(no.value, ast.Attribute)
            and no.value.attr == "state"
            and isinstance(no.value.value, ast.Attribute)
            and no.value.value.attr == "app"
        ):
            chaves.add(no.attr)
    return chaves


def _chaves_registradas_em_wiring(funcao: str) -> set[str]:
    arvore = ast.parse((APP_DIR / "wiring.py").read_text(encoding="utf-8"))
    chaves: set[str] = set()
    for no in arvore.body:
        if isinstance(no, ast.FunctionDef) and no.name == funcao:
            for filho in ast.walk(no):
                if (
                    isinstance(filho, ast.Assign)
                    and len(filho.targets) == 1
                    and isinstance(filho.targets[0], ast.Attribute)
                    and isinstance(filho.targets[0].value, ast.Attribute)
                    and filho.targets[0].value.attr == "state"
                ):
                    chaves.add(filho.targets[0].attr)
    return chaves


def test_todas_as_fabricas_de_users_constroem_interactors_com_uow_sql() -> None:
    sessions = _session_factory()
    hasher = FakePasswordHasher()
    policy = FakePasswordPolicy()
    attempts = fake_attempt_guard()
    issuer = fake_session_issuer()
    clock = FakeClock()

    casos: list[tuple[Callable[[object], object], object, type[object]]] = [
        (
            cast(
                Callable[[object], object],
                register_user_factory(sessions, hasher, policy, attempts),
            ),
            RegisterUserPresenterSpy(),
            RegisterUserInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                authenticate_user_factory(sessions, hasher, issuer, attempts),
            ),
            AuthenticateUserPresenterSpy(),
            AuthenticateUserInteractor,
        ),
        (
            cast(Callable[[object], object], get_current_user_factory(sessions)),
            GetCurrentUserPresenterSpy(),
            GetCurrentUserInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                change_password_factory(sessions, hasher, policy),
            ),
            ChangePasswordPresenterSpy(),
            ChangePasswordInteractor,
        ),
        (
            cast(Callable[[object], object], delete_user_factory(sessions, hasher)),
            DeleteUserPresenterSpy(),
            DeleteUserInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                refresh_session_factory(sessions, issuer, clock),
            ),
            RefreshSessionPresenterSpy(),
            RefreshSessionInteractor,
        ),
        (
            cast(Callable[[object], object], logout_factory(sessions, clock)),
            LogoutPresenterSpy(),
            LogoutInteractor,
        ),
    ]

    for factory, presenter, esperado in casos:
        interactor = factory(presenter)
        assert isinstance(interactor, esperado)
        com_uow = cast(_InteractorComUow, interactor)
        assert isinstance(com_uow.uow, SqlAlchemyUnitOfWork)
        assert com_uow.presenter is presenter


def test_dependencies_de_users_leem_exatamente_o_que_wiring_e_main_registram() -> None:
    app = FastAPI()
    install_users(app, _fake_infra(_session_factory()))
    request = Request({"type": "http", "app": app})

    resolvedores: list[tuple[Callable[[Request], object], str, type[object]]] = [
        (get_register_user_controller, "register_user", RegisterUserController),
        (
            get_authenticate_user_controller,
            "authenticate_user",
            AuthenticateUserController,
        ),
        (get_current_user_controller, "get_current_user", GetCurrentUserController),
        (get_change_password_controller, "change_password", ChangePasswordController),
        (get_delete_user_controller, "delete_user", DeleteUserController),
        (get_refresh_session_controller, "refresh_session", RefreshSessionController),
        (get_logout_controller, "logout", LogoutController),
    ]

    for resolver, chave, controller_cls in resolvedores:
        controller = resolver(request)
        assert isinstance(controller, controller_cls)
        com_fabrica = cast(_ControllerComFabrica, controller)
        assert com_fabrica.build_interactor is getattr(app.state, chave)

    assert isinstance(app.state.token_verifier, JwtTokenVerifier)
    assert isinstance(app.state.access_token_check, SqlAccessTokenCheck)

    users_api_dir = APP_DIR / "users" / "presentation" / "api" / "v1"
    chaves_lidas = _chaves_lidas(users_api_dir / "dependencies.py") | _chaves_lidas(
        users_api_dir / "security.py"
    )
    chaves_registradas = _chaves_registradas_em_wiring("install_users")
    assert chaves_lidas == chaves_registradas
    assert "install_users(app, infra)" in (APP_DIR / "main.py").read_text(
        encoding="utf-8"
    )
