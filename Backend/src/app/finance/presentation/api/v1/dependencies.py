from fastapi import Request

from app.finance.presentation.api.v1.controllers.accounts_controllers import (
    CreateAccountController,
    CreateAccountFactory,
    ListAccountsController,
    ListAccountsFactory,
)
from app.finance.presentation.api.v1.controllers.categories_controller import (
    ListCategoriesController,
    ListCategoriesFactory,
)
from app.finance.presentation.api.v1.controllers.change_transaction_controllers import (
    DeleteTransactionController,
    DeleteTransactionFactory,
    UpdateTransactionController,
    UpdateTransactionFactory,
)
from app.finance.presentation.api.v1.controllers.get_statement_controller import (
    GetStatementController,
    GetStatementFactory,
)
from app.finance.presentation.api.v1.controllers.record_transaction_controller import (
    RecordTransactionController,
    RecordTransactionFactory,
)
from app.finance.presentation.api.v1.controllers.transfers_controllers import (
    CreateTransferController,
    CreateTransferFactory,
    DeleteTransferController,
    DeleteTransferFactory,
)


def get_record_transaction_controller(request: Request) -> RecordTransactionController:
    factory: RecordTransactionFactory = request.app.state.record_transaction
    return RecordTransactionController(factory)


def get_statement_controller(request: Request) -> GetStatementController:
    factory: GetStatementFactory = request.app.state.get_statement
    return GetStatementController(factory)


def get_create_account_controller(request: Request) -> CreateAccountController:
    factory: CreateAccountFactory = request.app.state.create_account
    return CreateAccountController(factory)


def get_list_accounts_controller(request: Request) -> ListAccountsController:
    factory: ListAccountsFactory = request.app.state.list_accounts
    return ListAccountsController(factory)


def get_list_categories_controller(request: Request) -> ListCategoriesController:
    factory: ListCategoriesFactory = request.app.state.list_categories
    return ListCategoriesController(factory)


def get_update_transaction_controller(request: Request) -> UpdateTransactionController:
    factory: UpdateTransactionFactory = request.app.state.update_transaction
    return UpdateTransactionController(factory)


def get_delete_transaction_controller(request: Request) -> DeleteTransactionController:
    factory: DeleteTransactionFactory = request.app.state.delete_transaction
    return DeleteTransactionController(factory)


def get_create_transfer_controller(request: Request) -> CreateTransferController:
    factory: CreateTransferFactory = request.app.state.create_transfer
    return CreateTransferController(factory)


def get_delete_transfer_controller(request: Request) -> DeleteTransferController:
    factory: DeleteTransferFactory = request.app.state.delete_transfer
    return DeleteTransferController(factory)
