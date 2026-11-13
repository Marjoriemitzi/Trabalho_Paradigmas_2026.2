from app.finance.domain.entities.transfer import Transfer
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.transfer_id import TransferId
from app.finance.infrastructure.persistence.models.transfer_model import TransferModel


def to_model(transfer: Transfer) -> TransferModel:
    return TransferModel(
        id=transfer.id.value,
        owner_id=transfer.owner.value,
        from_account_id=transfer.source.value,
        to_account_id=transfer.destination.value,
        amount_cents=transfer.amount.cents,
        description=transfer.description.text,
        occurred_on=transfer.occurred_on,
    )


def to_entity(model: TransferModel) -> Transfer:
    return Transfer(
        id=TransferId(model.id),
        owner=OwnerId(model.owner_id),
        source=AccountId(model.from_account_id),
        destination=AccountId(model.to_account_id),
        amount=Money(model.amount_cents),
        description=Description(model.description),
        occurred_on=model.occurred_on,
    )
