from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.finance.application.ports.transaction_check import TransactionCheck
from app.finance.application.use_cases.create_account import (
    CreateAccountInputPort,
    CreateAccountInteractor,
    CreateAccountOutputPort,
)
from app.finance.application.use_cases.create_transfer import (
    CreateTransferInputPort,
    CreateTransferInteractor,
    CreateTransferOutputPort,
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
from app.finance.application.use_cases.record_transaction import (
    RecordTransactionInputPort,
    RecordTransactionInteractor,
    RecordTransactionOutputPort,
)
from app.finance.application.use_cases.update_transaction import (
    UpdateTransactionInputPort,
    UpdateTransactionInteractor,
    UpdateTransactionOutputPort,
)
from app.finance.domain.services.categorizer import Categorizer
from app.finance.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountFactory,
    ListAccountsFactory,
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
from app.finance.presentation.api.v1.controllers.transfers_controllers import (
    CreateTransferFactory,
    DeleteTransferFactory,
)


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
