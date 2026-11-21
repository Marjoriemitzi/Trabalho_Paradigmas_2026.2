import ast
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Protocol, cast

from fastapi import FastAPI, Request
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.finance.application.use_cases.create_account import CreateAccountInteractor
from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceInteractor,
)
from app.finance.application.use_cases.create_transfer import CreateTransferInteractor
from app.finance.application.use_cases.delete_account import DeleteAccountInteractor
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceInteractor,
)
from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionInteractor,
)
from app.finance.application.use_cases.delete_transfer import DeleteTransferInteractor
from app.finance.application.use_cases.get_statement import GetStatementInteractor
from app.finance.application.use_cases.list_accounts import ListAccountsInteractor
from app.finance.application.use_cases.list_categories import ListCategoriesInteractor
from app.finance.application.use_cases.list_recurrences import ListRecurrencesInteractor
from app.finance.application.use_cases.list_transfers import ListTransfersInteractor
from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInteractor,
)
from app.finance.application.use_cases.rename_account import RenameAccountInteractor
from app.finance.application.use_cases.run_due_recurrences import (
    RunDueRecurrencesInteractor,
    RunReport,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceInteractor,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInteractor,
)
from app.finance.application.use_cases.update_transfer import UpdateTransferInteractor
from app.finance.composition import (
    create_account_factory,
    create_recurrence_factory,
    create_transfer_factory,
    delete_account_factory,
    delete_recurrence_factory,
    delete_transaction_factory,
    delete_transfer_factory,
    get_statement_factory,
    list_accounts_factory,
    list_categories_factory,
    list_recurrences_factory,
    list_transfers_factory,
    record_transaction_factory,
    rename_account_factory,
    run_due_recurrences_factory,
    update_recurrence_factory,
    update_transaction_factory,
    update_transfer_factory,
)
from app.finance.domain.value_objects.category import Category
from app.finance.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountController,
    DeleteAccountController,
    ListAccountsController,
    RenameAccountController,
)
from app.finance.presentation.api.v1.controllers.categories_controller import (
    ListCategoriesController,
)
from app.finance.presentation.api.v1.controllers.change_transaction_controllers import (
    DeleteTransactionController,
    UpdateTransactionController,
)
from app.finance.presentation.api.v1.controllers.get_statement_controller import (
    GetStatementController,
)
from app.finance.presentation.api.v1.controllers.record_transaction_controller import (
    RecordTransactionController,
)
from app.finance.presentation.api.v1.controllers.recurrences_controllers import (
    CreateRecurrenceController,
    DeleteRecurrenceController,
    ListRecurrencesController,
    UpdateRecurrenceController,
)
from app.finance.presentation.api.v1.controllers.transfers_controllers import (
    CreateTransferController,
    DeleteTransferController,
    ListTransfersController,
    UpdateTransferController,
)
from app.finance.presentation.api.v1.dependencies import (
    get_create_account_controller,
    get_create_recurrence_controller,
    get_create_transfer_controller,
    get_delete_account_controller,
    get_delete_recurrence_controller,
    get_delete_transaction_controller,
    get_delete_transfer_controller,
    get_list_accounts_controller,
    get_list_categories_controller,
    get_list_recurrences_controller,
    get_list_transfers_controller,
    get_record_transaction_controller,
    get_rename_account_controller,
    get_statement_controller,
    get_update_recurrence_controller,
    get_update_transaction_controller,
    get_update_transfer_controller,
)
from app.shared.infrastructure.config.settings import Settings
from app.wiring import Infra, install_finance
from tests.finance.fakes.change_transaction_presenter_spies import (
    DeleteTransactionPresenterSpy,
    UpdateTransactionPresenterSpy,
)
from tests.finance.fakes.create_account_presenter_spy import CreateAccountPresenterSpy
from tests.finance.fakes.delete_account_presenter_spy import DeleteAccountPresenterSpy
from tests.finance.fakes.fake_categorizer import FakeCategorizer
from tests.finance.fakes.fake_recurrence_rules import FakeRecurrenceRules
from tests.finance.fakes.fake_transaction_check import FakeTransactionCheck
from tests.finance.fakes.get_statement_presenter_spy import GetStatementPresenterSpy
from tests.finance.fakes.list_accounts_presenter_spy import ListAccountsPresenterSpy
from tests.finance.fakes.list_categories_presenter_spy import (
    ListCategoriesPresenterSpy,
)
from tests.finance.fakes.record_transaction_presenter_spy import (
    RecordTransactionPresenterSpy,
)
from tests.finance.fakes.recurrence_presenter_spies import (
    CreateRecurrencePresenterSpy,
    DeleteRecurrencePresenterSpy,
    ListRecurrencesPresenterSpy,
    UpdateRecurrencePresenterSpy,
)
from tests.finance.fakes.rename_account_presenter_spy import RenameAccountPresenterSpy
from tests.finance.fakes.transfer_presenter_spies import (
    CreateTransferPresenterSpy,
    DeleteTransferPresenterSpy,
    ListTransfersPresenterSpy,
    UpdateTransferPresenterSpy,
)
from tests.shared.fakes.fixed_clock import FixedClock
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy

APP_DIR = Path(__file__).resolve().parents[3] / "src" / "app"


class _InteractorComUow(Protocol):
    @property
    def uow(self) -> object: ...
    @property
    def presenter(self) -> object: ...


class _ControllerComFabrica(Protocol):
    @property
    def build_interactor(self) -> object: ...


class _RunReportPresenterSpy:
    def __init__(self) -> None:
        self.report: RunReport | None = None

    def present_report(self, report: RunReport) -> None:
        self.report = report


def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker[AsyncSession]()


def _fake_infra(sessions: async_sessionmaker[AsyncSession]) -> Infra:
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


def _chaves_lidas_em_dependencies(arquivo: Path) -> set[str]:
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


def test_todas_as_fabricas_de_finance_constroem_interactors_com_uow_sql() -> None:
    sessions = _session_factory()
    categorizer = FakeCategorizer(Category("mercado"))
    checks = (FakeTransactionCheck(),)
    rules = FakeRecurrenceRules()
    clock = FixedClock(date(2026, 11, 20))

    casos: list[tuple[Callable[[object], object], object, type[object]]] = [
        (
            cast(
                Callable[[object], object],
                record_transaction_factory(sessions, categorizer, checks),
            ),
            RecordTransactionPresenterSpy(),
            RecordTransactionInteractor,
        ),
        (
            cast(Callable[[object], object], get_statement_factory(sessions)),
            GetStatementPresenterSpy(),
            GetStatementInteractor,
        ),
        (
            cast(Callable[[object], object], create_account_factory(sessions)),
            CreateAccountPresenterSpy(),
            CreateAccountInteractor,
        ),
        (
            cast(Callable[[object], object], list_accounts_factory(sessions)),
            ListAccountsPresenterSpy(),
            ListAccountsInteractor,
        ),
        (
            cast(Callable[[object], object], list_categories_factory(sessions)),
            ListCategoriesPresenterSpy(),
            ListCategoriesInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                update_transaction_factory(sessions, categorizer, checks),
            ),
            UpdateTransactionPresenterSpy(),
            UpdateTransactionInteractor,
        ),
        (
            cast(Callable[[object], object], delete_transaction_factory(sessions)),
            DeleteTransactionPresenterSpy(),
            DeleteTransactionInteractor,
        ),
        (
            cast(Callable[[object], object], create_transfer_factory(sessions)),
            CreateTransferPresenterSpy(),
            CreateTransferInteractor,
        ),
        (
            cast(Callable[[object], object], delete_transfer_factory(sessions)),
            DeleteTransferPresenterSpy(),
            DeleteTransferInteractor,
        ),
        (
            cast(Callable[[object], object], rename_account_factory(sessions)),
            RenameAccountPresenterSpy(),
            RenameAccountInteractor,
        ),
        (
            cast(Callable[[object], object], delete_account_factory(sessions)),
            DeleteAccountPresenterSpy(),
            DeleteAccountInteractor,
        ),
        (
            cast(Callable[[object], object], update_transfer_factory(sessions)),
            UpdateTransferPresenterSpy(),
            UpdateTransferInteractor,
        ),
        (
            cast(Callable[[object], object], list_transfers_factory(sessions)),
            ListTransfersPresenterSpy(),
            ListTransfersInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                create_recurrence_factory(sessions, rules, clock),
            ),
            CreateRecurrencePresenterSpy(),
            CreateRecurrenceInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                update_recurrence_factory(sessions, rules, clock),
            ),
            UpdateRecurrencePresenterSpy(),
            UpdateRecurrenceInteractor,
        ),
        (
            cast(Callable[[object], object], delete_recurrence_factory(sessions)),
            DeleteRecurrencePresenterSpy(),
            DeleteRecurrenceInteractor,
        ),
        (
            cast(
                Callable[[object], object],
                list_recurrences_factory(sessions, rules, clock),
            ),
            ListRecurrencesPresenterSpy(),
            ListRecurrencesInteractor,
        ),
    ]

    for factory, presenter, esperado in casos:
        interactor = factory(presenter)
        assert isinstance(interactor, esperado)
        com_uow = cast(_InteractorComUow, interactor)
        assert isinstance(com_uow.uow, SqlAlchemyUnitOfWork)
        assert com_uow.presenter is presenter

    runner_presenter = _RunReportPresenterSpy()
    runner = run_due_recurrences_factory(sessions, categorizer, checks, rules)(
        runner_presenter
    )
    assert isinstance(runner, RunDueRecurrencesInteractor)
    assert isinstance(runner.uow_factory(), SqlAlchemyUnitOfWork)
    assert runner.presenter is runner_presenter


def test_dependencies_de_finance_leem_exatamente_o_que_wiring_e_main_registram() -> (
    None
):
    app = FastAPI()
    install_finance(app, _fake_infra(_session_factory()))
    request = Request({"type": "http", "app": app})

    resolvedores: list[tuple[Callable[[Request], object], str, type[object]]] = [
        (
            get_record_transaction_controller,
            "record_transaction",
            RecordTransactionController,
        ),
        (get_statement_controller, "get_statement", GetStatementController),
        (get_create_account_controller, "create_account", CreateAccountController),
        (get_list_accounts_controller, "list_accounts", ListAccountsController),
        (get_list_categories_controller, "list_categories", ListCategoriesController),
        (
            get_update_transaction_controller,
            "update_transaction",
            UpdateTransactionController,
        ),
        (
            get_delete_transaction_controller,
            "delete_transaction",
            DeleteTransactionController,
        ),
        (get_create_transfer_controller, "create_transfer", CreateTransferController),
        (get_delete_transfer_controller, "delete_transfer", DeleteTransferController),
        (get_rename_account_controller, "rename_account", RenameAccountController),
        (get_delete_account_controller, "delete_account", DeleteAccountController),
        (get_update_transfer_controller, "update_transfer", UpdateTransferController),
        (get_list_transfers_controller, "list_transfers", ListTransfersController),
        (
            get_create_recurrence_controller,
            "create_recurrence",
            CreateRecurrenceController,
        ),
        (
            get_update_recurrence_controller,
            "update_recurrence",
            UpdateRecurrenceController,
        ),
        (
            get_delete_recurrence_controller,
            "delete_recurrence",
            DeleteRecurrenceController,
        ),
        (
            get_list_recurrences_controller,
            "list_recurrences",
            ListRecurrencesController,
        ),
    ]

    for resolver, chave, controller_cls in resolvedores:
        controller = resolver(request)
        assert isinstance(controller, controller_cls)
        com_fabrica = cast(_ControllerComFabrica, controller)
        assert com_fabrica.build_interactor is getattr(app.state, chave)

    chaves_lidas = _chaves_lidas_em_dependencies(
        APP_DIR / "finance" / "presentation" / "api" / "v1" / "dependencies.py"
    )
    chaves_registradas = _chaves_registradas_em_wiring("install_finance")
    assert chaves_lidas <= chaves_registradas
    assert chaves_registradas - chaves_lidas == {"clock"}
    assert "install_finance(app, infra)" in (APP_DIR / "main.py").read_text(
        encoding="utf-8"
    )
