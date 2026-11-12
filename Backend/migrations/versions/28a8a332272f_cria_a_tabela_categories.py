"""cria a tabela categories"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '28a8a332272f'
down_revision: Union[str, Sequence[str], None] = '480fe9a27567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categories = op.create_table('categories',
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('name', sa.String(length=40), nullable=False),
    sa.Column('label', sa.String(length=40), nullable=False),
    sa.CheckConstraint("kind IN ('income', 'expense')", name=op.f('ck_categories_kind_known')),
    sa.PrimaryKeyConstraint('kind', 'name', name=op.f('pk_categories'))
    )

    op.bulk_insert(categories, [
        {'kind': 'expense', 'name': 'lazer', 'label': 'Lazer'},
        {'kind': 'expense', 'name': 'mercado', 'label': 'Mercado'},
        {'kind': 'expense', 'name': 'moradia', 'label': 'Moradia'},
        {'kind': 'expense', 'name': 'outros', 'label': 'Outros'},
        {'kind': 'expense', 'name': 'saude', 'label': 'Saúde'},
        {'kind': 'expense', 'name': 'transporte', 'label': 'Transporte'},
        {'kind': 'income', 'name': 'freelance', 'label': 'Freelance'},
        {'kind': 'income', 'name': 'outros', 'label': 'Outros'},
        {'kind': 'income', 'name': 'salario', 'label': 'Salário'},
    ])


def downgrade() -> None:
    op.drop_table('categories')
