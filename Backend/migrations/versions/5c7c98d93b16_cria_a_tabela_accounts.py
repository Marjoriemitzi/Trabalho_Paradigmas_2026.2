"""cria a tabela accounts"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5c7c98d93b16'
down_revision: Union[str, Sequence[str], None] = '8fb35a663e3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('accounts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('owner_id', sa.Uuid(), nullable=False),
    sa.Column('name', sa.String(length=60), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], name=op.f('fk_accounts_owner_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounts')),
    sa.UniqueConstraint('id', 'owner_id', name='uq_accounts_id_owner_id')
    )
    op.create_index('uq_accounts_owner_id_lower_name', 'accounts', ['owner_id', sa.literal_column('lower(name)')], unique=True)


def downgrade() -> None:
    op.drop_index('uq_accounts_owner_id_lower_name', table_name='accounts')
    op.drop_table('accounts')
