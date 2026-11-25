"""indexa consultas por conta e expiracao de tokens"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b7d41e9c2f60'
down_revision: Union[str, Sequence[str], None] = '2011a5220856'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index('ix_transactions_owner_id_account_id_occurred_on', 'transactions', ['owner_id', 'account_id', 'occurred_on'], unique=False)
    op.create_index('ix_transfers_owner_id_from_account_id', 'transfers', ['owner_id', 'from_account_id'], unique=False)
    op.create_index('ix_transfers_owner_id_to_account_id', 'transfers', ['owner_id', 'to_account_id'], unique=False)
    op.create_index('ix_recurrences_owner_id_account_id', 'recurrences', ['owner_id', 'account_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_user_id'), 'refresh_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_refresh_tokens_expires_at'), 'refresh_tokens', ['expires_at'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_user_id'), 'revoked_tokens', ['user_id'], unique=False)
    op.create_index(op.f('ix_revoked_tokens_expires_at'), 'revoked_tokens', ['expires_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_revoked_tokens_expires_at'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_revoked_tokens_user_id'), table_name='revoked_tokens')
    op.drop_index(op.f('ix_refresh_tokens_expires_at'), table_name='refresh_tokens')
    op.drop_index(op.f('ix_refresh_tokens_user_id'), table_name='refresh_tokens')
    op.drop_index('ix_recurrences_owner_id_account_id', table_name='recurrences')
    op.drop_index('ix_transfers_owner_id_to_account_id', table_name='transfers')
    op.drop_index('ix_transfers_owner_id_from_account_id', table_name='transfers')
    op.drop_index('ix_transactions_owner_id_account_id_occurred_on', table_name='transactions')
