from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.owner_id import OwnerId
from app.finance.infrastructure.persistence.models.transaction_model import (
    TransactionModel,
)
from app.finance.infrastructure.persistence.models.transfer_model import TransferModel


class SqlAccountUsage:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def in_use(self, owner: OwnerId, account: Account) -> bool:
        # NOTA: Quando issues #27 (Metas) e #28 (Recorrências) forem implementadas, adicionar as tabelas aqui
        q_trans = select(
            exists().where(
                TransactionModel.account_id == account.id.value,
                TransactionModel.owner_id == owner.value,
            )
        )
        q_transf_out = select(
            exists().where(
                TransferModel.from_account_id == account.id.value,
                TransferModel.owner_id == owner.value,
            )
        )
        q_transf_in = select(
            exists().where(
                TransferModel.to_account_id == account.id.value,
                TransferModel.owner_id == owner.value,
            )
        )

        return bool(
            await self._session.scalar(q_trans)
            or await self._session.scalar(q_transf_out)
            or await self._session.scalar(q_transf_in)
        )
