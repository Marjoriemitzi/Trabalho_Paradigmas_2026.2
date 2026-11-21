import uuid
from datetime import UTC, datetime, timedelta

from app.users.domain.entities.refresh_token import RefreshToken
from app.users.domain.value_objects.user_id import UserId


def _emitir(expires_at: datetime) -> RefreshToken:
    return RefreshToken.issue(
        user_id=UserId(uuid.UUID("12345678-1234-5678-1234-567812345678")),
        family_id=uuid.UUID("abcdefab-cdef-abcd-efab-cdefabcdefab"),
        token_hash="sha256-hex-digest",
        expires_at=expires_at,
    )


def test_issue_gera_identidade_e_preserva_metadados() -> None:
    user_id = UserId.new()
    family_id = uuid.uuid4()
    expira = datetime(2026, 12, 1, 12, 0, tzinfo=UTC)

    token = RefreshToken.issue(
        user_id=user_id,
        family_id=family_id,
        token_hash="hash-opaco",
        expires_at=expira,
    )
    outro = RefreshToken.issue(
        user_id=user_id,
        family_id=family_id,
        token_hash="hash-opaco",
        expires_at=expira,
    )

    assert isinstance(token.id, uuid.UUID)
    assert token.id != outro.id
    assert token.user_id == user_id
    assert token.family_id == family_id
    assert token.token_hash == "hash-opaco"
    assert token.expires_at == expira
    assert token.used_at is None
    assert token.revoked_at is None


def test_is_expired_respeita_exatamente_a_fronteira_de_vencimento() -> None:
    agora = datetime(2026, 11, 21, 15, 0, tzinfo=UTC)

    ainda_valido = _emitir(agora + timedelta(seconds=1))
    no_limite = _emitir(agora)
    ja_vencido = _emitir(agora - timedelta(seconds=1))

    assert ainda_valido.is_expired(agora) is False
    assert no_limite.is_expired(agora) is True
    assert ja_vencido.is_expired(agora) is True
