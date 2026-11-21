from app.finance.domain.entities.recurrence import Recurrence
from app.finance.domain.value_objects.account_id import AccountId
from app.finance.domain.value_objects.active_range import ActiveRange
from app.finance.domain.value_objects.category import Category
from app.finance.domain.value_objects.description import Description
from app.finance.domain.value_objects.frequency import Frequency
from app.finance.domain.value_objects.money import Money
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.domain.value_objects.recurrence_id import RecurrenceId
from app.finance.domain.value_objects.schedule import Schedule
from app.finance.domain.value_objects.transaction_kind import TransactionKind
from app.finance.infrastructure.persistence.models.recurrence_model import (
    RecurrenceModel,
)


def to_model(recurrence: Recurrence) -> RecurrenceModel:
    return RecurrenceModel(
        id=recurrence.id.value,
        owner_id=recurrence.owner.value,
        account_id=recurrence.account.value,
        kind=recurrence.kind.value,
        amount_cents=recurrence.amount.cents,
        description=recurrence.description.text,
        category=None if recurrence.category is None else recurrence.category.name,
        frequency=recurrence.schedule.frequency.value,
        day=recurrence.schedule.day,
        starts_on=recurrence.starts_on,
        ends_on=recurrence.ends_on,
        last_run_on=recurrence.last_run_on,
    )


def to_entity(model: RecurrenceModel) -> Recurrence:
    return Recurrence(
        id=RecurrenceId(model.id),
        owner=OwnerId(model.owner_id),
        account=AccountId(model.account_id),
        kind=TransactionKind(model.kind),
        amount=Money(model.amount_cents),
        description=Description(model.description),
        category=None if model.category is None else Category(model.category),
        schedule=Schedule(Frequency(model.frequency), model.day),
        window=ActiveRange(model.starts_on, model.ends_on),
        last_run_on=model.last_run_on,
    )
