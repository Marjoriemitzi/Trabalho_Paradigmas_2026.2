from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.use_cases.create_account import (
    CreateAccountInputPort,
    CreateAccountInteractor,
    CreateAccountOutputPort,
)
from app.finance.application.use_cases.create_recurrence import (
    CreateRecurrenceInputPort,
    CreateRecurrenceInteractor,
    CreateRecurrenceOutputPort,
)
from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferInteractor,
    CreateTransferOutputPort,
)
from app.finance.application.use_cases.delete_account import (
    DeleteAccountInputPort,
    DeleteAccountInteractor,
    DeleteAccountOutputPort,
)
from app.finance.application.use_cases.delete_recurrence import (
    DeleteRecurrenceInputPort,
    DeleteRecurrenceInteractor,
    DeleteRecurrenceOutputPort,
)
from app.finance.application.use_cases.delete_transaction import (
    DeleteTransactionInputPort,
    DeleteTransactionInteractor,
    DeleteTransactionOutputPort,
)
from app.finance.application.use_cases.delete_transfer import (
    DeleteTransferInputPort,
    DeleteTransferInteractor,
    DeleteTransferOutputPort,
)
from app.finance.application.use_cases.get_statement import (
    GetStatementInputPort,
    GetStatementInteractor,
    GetStatementOutputPort,
)
from app.finance.application.use_cases.list_accounts import (
    ListAccountsInputPort,
    ListAccountsInteractor,
    ListAccountsOutputPort,
)
from app.finance.application.use_cases.list_categories import (
    ListCategoriesInputPort,
    ListCategoriesInteractor,
    ListCategoriesOutputPort,
)
from app.finance.application.use_cases.list_recurrences import (
    ListRecurrencesInputPort,
    ListRecurrencesInteractor,
    ListRecurrencesOutputPort,
)
from app.finance.application.use_cases.list_transfers import (
    ListTransfersInputPort,
    ListTransfersInteractor,
    ListTransfersOutputPort,
)
from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInputPort,
    RecordTransactionInteractor,
    RecordTransactionOutputPort,
)
from app.finance.application.use_cases.rename_account import (
    RenameAccountInputPort,
    RenameAccountInteractor,
    RenameAccountOutputPort,
)
from app.finance.application.use_cases.update_recurrence import (
    UpdateRecurrenceInputPort,
    UpdateRecurrenceInteractor,
    UpdateRecurrenceOutputPort,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInputPort,
    UpdateTransactionInteractor,
    UpdateTransactionOutputPort,
)
from app.finance.application.use_cases.update_transfer import (
    UpdateTransferInputPort,
    UpdateTransferInteractor,
    UpdateTransferOutputPort,
)
from app.finance.domain.services.categorizer import Categorizer
from app.finance.domain.services.recurrence_rules import RecurrenceRules
from app.finance.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountFactory,
    DeleteAccountFactory,
    ListAccountsFactory,
    RenameAccountFactory,
)
from app.finance.presentation.api.v1.controllers.categories_controller import (
    ListCategoriesFactory,
)
from app.finance.presentation.api.v1.controllers.change_transaction_controllers import (
    DeleteTransactionFactory,
    UpdateTransactionFactory,
)
from app.finance.presentation.api.v1.controllers.get_statement_controller import (
    GetStatementFactory,
)
from app.finance.presentation.api.v1.controllers.record_transaction_controller import (
    RecordTransactionFactory,
)
from app.finance.presentation.api.v1.controllers.recurrences_controllers import (
    CreateRecurrenceFactory,
    DeleteRecurrenceFactory,
    ListRecurrencesFactory,
    UpdateRecurrenceFactory,
)
from app.finance.presentation.api.v1.controllers.transfers_controllers import (
    CreateTransferFactory,
    DeleteTransferFactory,
    ListTransfersFactory,
    UpdateTransferFactory,
)
from app.shared.domain.clock import Clock


def record_transaction_factory(
    session_factory: async_sessionmaker[AsyncSession],
    categorizer: Categorizer,
    checks: tuple[TransactionCheck, ...] = (),
) -> RecordTransactionFactory:
    def build(presenter: RecordTransactionOutputPort) -> RecordTransactionInputPort:
        return RecordTransactionInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            categorizer=categorizer,
            presenter=presenter,
            checks=checks,
        )

    return build


def get_statement_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> GetStatementFactory:
    def build(presenter: GetStatementOutputPort) -> GetStatementInputPort:
        return GetStatementInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def create_account_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> CreateAccountFactory:
    def build(presenter: CreateAccountOutputPort) -> CreateAccountInputPort:
        return CreateAccountInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def list_accounts_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> ListAccountsFactory:
    def build(presenter: ListAccountsOutputPort) -> ListAccountsInputPort:
        return ListAccountsInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def list_categories_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> ListCategoriesFactory:
    def build(presenter: ListCategoriesOutputPort) -> ListCategoriesInputPort:
        return ListCategoriesInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def update_transaction_factory(
    session_factory: async_sessionmaker[AsyncSession],
    categorizer: Categorizer,
    checks: tuple[TransactionCheck, ...] = (),
) -> UpdateTransactionFactory:
    def build(presenter: UpdateTransactionOutputPort) -> UpdateTransactionInputPort:
        return UpdateTransactionInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            categorizer=categorizer,
            presenter=presenter,
            checks=checks,
        )

    return build


def delete_transaction_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> DeleteTransactionFactory:
    def build(presenter: DeleteTransactionOutputPort) -> DeleteTransactionInputPort:
        return DeleteTransactionInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def create_transfer_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> CreateTransferFactory:
    def build(presenter: CreateTransferOutputPort) -> CreateTransferInputPort:
        return CreateTransferInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def delete_transfer_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> DeleteTransferFactory:
    def build(presenter: DeleteTransferOutputPort) -> DeleteTransferInputPort:
        return DeleteTransferInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def rename_account_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> RenameAccountFactory:
    def build(presenter: RenameAccountOutputPort) -> RenameAccountInputPort:
        return RenameAccountInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def delete_account_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> DeleteAccountFactory:
    def build(presenter: DeleteAccountOutputPort) -> DeleteAccountInputPort:
        return DeleteAccountInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def update_transfer_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> UpdateTransferFactory:
    def build(presenter: UpdateTransferOutputPort) -> UpdateTransferInputPort:
        return UpdateTransferInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def list_transfers_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> ListTransfersFactory:
    def build(presenter: ListTransfersOutputPort) -> ListTransfersInputPort:
        return ListTransfersInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def create_recurrence_factory(
    session_factory: async_sessionmaker[AsyncSession],
    rules: RecurrenceRules,
    clock: Clock,
) -> CreateRecurrenceFactory:
    def build(presenter: CreateRecurrenceOutputPort) -> CreateRecurrenceInputPort:
        return CreateRecurrenceInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            rules=rules,
            clock=clock,
            presenter=presenter,
        )

    return build


def update_recurrence_factory(
    session_factory: async_sessionmaker[AsyncSession],
    rules: RecurrenceRules,
    clock: Clock,
) -> UpdateRecurrenceFactory:
    def build(presenter: UpdateRecurrenceOutputPort) -> UpdateRecurrenceInputPort:
        return UpdateRecurrenceInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            rules=rules,
            clock=clock,
            presenter=presenter,
        )

    return build


def delete_recurrence_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> DeleteRecurrenceFactory:
    def build(presenter: DeleteRecurrenceOutputPort) -> DeleteRecurrenceInputPort:
        return DeleteRecurrenceInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory), presenter=presenter
        )

    return build


def list_recurrences_factory(
    session_factory: async_sessionmaker[AsyncSession],
    rules: RecurrenceRules,
    clock: Clock,
) -> ListRecurrencesFactory:
    def build(presenter: ListRecurrencesOutputPort) -> ListRecurrencesInputPort:
        return ListRecurrencesInteractor(
            uow=SqlAlchemyUnitOfWork(session_factory),
            rules=rules,
            clock=clock,
            presenter=presenter,
        )

    return build
