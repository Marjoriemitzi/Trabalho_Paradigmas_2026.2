import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.users.application.ports.token_blocklist import TokenBlocklist
from app.users.domain.value_objects.user_id import UserId

AGORA = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)


class TokenBlocklistContract:
    @pytest.fixture
    def blocklist(self) -> TokenBlocklist:
        raise NotImplementedError

    @pytest.fixture
    def usuario(self) -> UserId:
        raise NotImplementedError

    async def test_jti_desconhecido_nao_esta_bloqueado(
        self, blocklist: TokenBlocklist
    ) -> None:
        assert await blocklist.contains(uuid.uuid4()) is False

    async def test_jti_adicionado_passa_a_estar_bloqueado_e_so_ele(
        self, blocklist: TokenBlocklist, usuario: UserId
    ) -> None:
        bloqueado, livre = uuid.uuid4(), uuid.uuid4()

        await blocklist.add(bloqueado, usuario, AGORA + timedelta(minutes=15))

        assert await blocklist.contains(bloqueado) is True
        assert await blocklist.contains(livre) is False

    async def test_adicionar_o_mesmo_jti_duas_vezes_nao_da_erro(
        self, blocklist: TokenBlocklist, usuario: UserId
    ) -> None:
        jti = uuid.uuid4()

        await blocklist.add(jti, usuario, AGORA + timedelta(minutes=15))
        await blocklist.add(jti, usuario, AGORA + timedelta(minutes=15))

        assert await blocklist.contains(jti) is True

    async def test_delete_expired_apaga_so_os_ja_vencidos(
        self, blocklist: TokenBlocklist, usuario: UserId
    ) -> None:
        vencido, vigente = uuid.uuid4(), uuid.uuid4()
        await blocklist.add(vencido, usuario, AGORA - timedelta(minutes=1))
        await blocklist.add(vigente, usuario, AGORA + timedelta(minutes=1))

        await blocklist.delete_expired(AGORA)

        assert await blocklist.contains(vencido) is False
        assert await blocklist.contains(vigente) is True
