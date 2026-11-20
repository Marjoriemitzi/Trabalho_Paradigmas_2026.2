import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.users.domain.entities.refresh_token import RefreshToken
from app.users.domain.repositories.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.users.domain.value_objects.user_id import UserId

AGORA = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
HASH_A = "a" * 64
HASH_B = "b" * 64
HASH_C = "c" * 64


def token(
    usuario: UserId, familia: uuid.UUID, hash_: str, vence_em: datetime | None = None
) -> RefreshToken:
    return RefreshToken.issue(
        user_id=usuario,
        family_id=familia,
        token_hash=hash_,
        expires_at=vence_em or AGORA + timedelta(days=30),
    )


class RefreshTokenRepositoryContract:
    @pytest.fixture
    def repository(self) -> RefreshTokenRepository:
        raise NotImplementedError

    @pytest.fixture
    def usuario(self) -> UserId:
        raise NotImplementedError

    @pytest.fixture
    def outro_usuario(self) -> UserId:
        raise NotImplementedError

    async def test_guarda_e_busca_pelo_hash_com_todos_os_dados(
        self, repository: RefreshTokenRepository, usuario: UserId
    ) -> None:
        guardado = token(usuario, uuid.uuid4(), HASH_A)
        await repository.add(guardado)

        lido = await repository.get_by_hash(HASH_A)

        assert lido == guardado
        assert lido is not None
        assert lido.used_at is None
        assert lido.revoked_at is None

    async def test_hash_desconhecido_nao_acha_nada(
        self, repository: RefreshTokenRepository
    ) -> None:
        assert await repository.get_by_hash(HASH_A) is None

    async def test_mark_used_marca_uma_vez_so(
        self, repository: RefreshTokenRepository, usuario: UserId
    ) -> None:
        guardado = token(usuario, uuid.uuid4(), HASH_A)
        await repository.add(guardado)

        primeira = await repository.mark_used(guardado.id, AGORA)
        segunda = await repository.mark_used(guardado.id, AGORA)

        assert (primeira, segunda) == (True, False)
        lido = await repository.get_by_hash(HASH_A)
        assert lido is not None
        assert lido.used_at == AGORA

    async def test_mark_used_nao_marca_token_revogado(
        self, repository: RefreshTokenRepository, usuario: UserId
    ) -> None:
        familia = uuid.uuid4()
        guardado = token(usuario, familia, HASH_A)
        await repository.add(guardado)
        await repository.revoke_family(familia, AGORA)

        assert await repository.mark_used(guardado.id, AGORA) is False

    async def test_revoke_family_revoga_so_a_familia_pedida(
        self,
        repository: RefreshTokenRepository,
        usuario: UserId,
        outro_usuario: UserId,
    ) -> None:
        familia, outra = uuid.uuid4(), uuid.uuid4()
        await repository.add(token(usuario, familia, HASH_A))
        await repository.add(token(usuario, familia, HASH_B))
        await repository.add(token(outro_usuario, outra, HASH_C))

        await repository.revoke_family(familia, AGORA)

        a = await repository.get_by_hash(HASH_A)
        b = await repository.get_by_hash(HASH_B)
        c = await repository.get_by_hash(HASH_C)
        assert a is not None and a.revoked_at == AGORA
        assert b is not None and b.revoked_at == AGORA
        assert c is not None and c.revoked_at is None

    async def test_delete_expired_before_apaga_so_os_vencidos_antes_do_limite(
        self, repository: RefreshTokenRepository, usuario: UserId
    ) -> None:
        familia = uuid.uuid4()
        await repository.add(
            token(usuario, familia, HASH_A, AGORA - timedelta(days=10))
        )
        await repository.add(token(usuario, familia, HASH_B, AGORA - timedelta(days=1)))
        await repository.add(token(usuario, familia, HASH_C, AGORA + timedelta(days=1)))

        await repository.delete_expired_before(AGORA - timedelta(days=7))

        assert await repository.get_by_hash(HASH_A) is None
        assert await repository.get_by_hash(HASH_B) is not None
        assert await repository.get_by_hash(HASH_C) is not None
