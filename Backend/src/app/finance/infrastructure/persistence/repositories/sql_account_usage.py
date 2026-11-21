from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.models.recurrence_model import (
    RecurrenceModel,
)
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)
from app.finance.infrastructure.persistence.models.transfer_model import TransferModel


class SqlAccountUsage:
    """Diz se algo segura a conta no banco.

    Ao criar uma tabela que aponta para `accounts` (metas), some a
    consulta dela aqui, senão a conta passa a poder ser apagada com dados ligados.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def in_use(self, owner: OwnerId, account: Account) -> bool:
        conta = account.id.value
        com_transacao = exists().where(
            TransactionModel.owner_id == owner.value,
            TransactionModel.account_id == conta,
        )
        com_transferencia = exists().where(
            TransferModel.owner_id == owner.value,
            or_(
                TransferModel.from_account_id == conta,
                TransferModel.to_account_id == conta,
            ),
        )
        com_recorrencia = exists().where(
            RecurrenceModel.owner_id == owner.value,
            RecurrenceModel.account_id == conta,
        )
        return bool(
            await self._session.scalar(
                select(com_transacao | com_transferencia | com_recorrencia)
            )
        )
