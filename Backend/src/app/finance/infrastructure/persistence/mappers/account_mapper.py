from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.models.account_model import AccountModel


def to_model(account: Account) -> AccountModel:
    return AccountModel(
        id=account.id.value,
        owner_id=account.owner.value,
        name=account.name.text,
        kind=account.kind.value,
    )


def to_entity(model: AccountModel) -> Account:
    return Account(
        id=AccountId(model.id),
        owner=OwnerId(model.owner_id),
        name=AccountName(model.name),
        kind=AccountKind(model.kind),
    )
