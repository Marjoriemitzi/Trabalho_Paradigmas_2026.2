from app.finance.domain.entities.transaction import Transaction
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transaction_id import TransactionId
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)


def to_model(transaction: Transaction) -> TransactionModel:
    return TransactionModel(
        id=transaction.id.value,
        owner_id=transaction.owner.value,
        account_id=transaction.account.value,
        kind=transaction.kind.value,
        amount_cents=transaction.amount.cents,
        description=transaction.description.text,
        category=transaction.category.name,
        occurred_on=transaction.occurred_on,
    )


def to_entity(model: TransactionModel) -> Transaction:
    return Transaction(
        id=TransactionId(model.id),
        owner=OwnerId(model.owner_id),
        account=AccountId(model.account_id),
        kind=TransactionKind(model.kind),
        amount=Money(model.amount_cents),
        description=Description(model.description),
        category=Category(model.category),
        occurred_on=model.occurred_on,
    )
