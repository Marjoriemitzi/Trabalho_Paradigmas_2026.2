"""cria a tabela transactions"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5e0db07ff832'
down_revision: Union[str, Sequence[str], None] = 'af8100314025'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('transactions',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('amount_cents', sa.BigInteger(), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('category', sa.String(length=40), nullable=False),
    sa.Column('occurred_on', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('income', 'expense')", name=op.f('ck_transactions_kind_known')),
    sa.CheckConstraint('amount_cents > 0', name=op.f('ck_transactions_amount_positive')),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_transactions_owner_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_transactions'))
    )
    op.create_index(op.f('ix_transactions_owner_id'), 'transactions', ['owner_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_owner_id'), table_name='transactions')
    op.drop_table('transactions')
