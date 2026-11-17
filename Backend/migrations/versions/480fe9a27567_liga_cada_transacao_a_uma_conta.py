"""liga cada transacao a uma conta"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '480fe9a27567'
down_revision: Union[str, Sequence[str], None] = '5c7c98d93b16'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transactions', sa.Column('account_id', sa.Uuid(), nullable=True))

    op.execute("""
        INSERT INTO accounts (id, owner_id, name, kind)
        SELECT gen_random_uuid(), owner_id, 'Carteira', 'wallet'
        FROM (SELECT DISTINCT owner_id FROM transactions) AS donos
        ON CONFLICT (owner_id, lower(name)) DO NOTHING
    """)
    op.execute("""
        UPDATE transactions AS t
        SET account_id = a.id
        FROM accounts AS a
        WHERE a.owner_id = t.owner_id AND lower(a.name) = 'carteira'
    """)

    op.alter_column('transactions', 'account_id', nullable=False)
    op.create_foreign_key('fk_transactions_account_id_owner_id_accounts', 'transactions', 'accounts', ['account_id', 'owner_id'], ['id', 'owner_id'], ondelete='RESTRICT')


def downgrade() -> None:
    op.drop_constraint('fk_transactions_account_id_owner_id_accounts', 'transactions', type_='foreignkey')
    op.drop_column('transactions', 'account_id')
