"""indexa transactions por dono e data"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8fb35a663e3e'
down_revision: Union[str, Sequence[str], None] = '5e0db07ff832'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_transactions_owner_id_occurred_on', 'transactions', ['owner_id', 'occurred_on'], unique=False)
    op.drop_index(op.f('ix_transactions_owner_id'), table_name='transactions')


def downgrade() -> None:
    op.create_index(op.f('ix_transactions_owner_id'), 'transactions', ['owner_id'], unique=False)
    op.drop_index('ix_transactions_owner_id_occurred_on', table_name='transactions')
