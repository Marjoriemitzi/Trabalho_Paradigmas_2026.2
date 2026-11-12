"""liga cada transacao a uma categoria"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '3cc72aadfc32'
down_revision: Union[str, Sequence[str], None] = '28a8a332272f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        UPDATE transactions AS t
        SET category = 'outros'
        WHERE NOT EXISTS (
            SELECT 1 FROM categories AS c
            WHERE c.kind = t.kind AND c.name = t.category
        )
    """)

    op.create_foreign_key('fk_transactions_kind_category_categories', 'transactions', 'categories', ['kind', 'category'], ['kind', 'name'], ondelete='RESTRICT')


def downgrade() -> None:
    op.drop_constraint('fk_transactions_kind_category_categories', 'transactions', type_='foreignkey')
