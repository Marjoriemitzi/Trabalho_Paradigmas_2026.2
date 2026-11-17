"""cria a tabela transfers"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ac99355965ba'
down_revision: Union[str, Sequence[str], None] = '3cc72aadfc32'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('transfers',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('from_account_id', sa.Uuid(), nullable=False),
    sa.Column('to_account_id', sa.Uuid(), nullable=False),
    sa.Column('amount_cents', sa.BigInteger(), nullable=False),
    sa.Column('description', sa.String(length=200), nullable=False),
    sa.Column('occurred_on', sa.Date(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('amount_cents > 0', name=op.f('ck_transfers_amount_positive')),
    sa.CheckConstraint('from_account_id <> to_account_id', name=op.f('ck_transfers_different_accounts')),
    sa.ForeignKeyConstraint(['from_account_id', 'owner_id'], ['accounts.id', 'accounts.owner_id'], name='fk_transfers_from_account_id_owner_id_accounts', ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_transfers_owner_id_users'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['to_account_id', 'owner_id'], ['accounts.id', 'accounts.owner_id'], name='fk_transfers_to_account_id_owner_id_accounts', ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_transfers'))
    )
    op.create_index('ix_transfers_owner_id_occurred_on', 'transfers', ['owner_id', 'occurred_on'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_transfers_owner_id_occurred_on', table_name='transfers')
    op.drop_table('transfers')
