import uuid
from collections.abc import Awaitable, Callable

import pytest

from app.users.application.ports.access_token_check import AccessTokenCheck
from app.users.domain.value_objects.user_id import UserId
from tests.users.fakes.authenticated import autenticado

Bloquear = Callable[[uuid.UUID, UserId], Awaitable[None]]


class AccessTokenCheckContract:
    """O que todo AccessTokenCheck precisa cumprir, seja o fake ou o SQL.

    A classe concreta entrega um `check`, um `usuario` já gravado e um `bloquear`
    que coloca um jti na blocklist daquele usuário.
    """

    @pytest.fixture
    def check(self) -> AccessTokenCheck:
        raise NotImplementedError

    @pytest.fixture
    def usuario(self) -> UserId:
        raise NotImplementedError

    @pytest.fixture
    def bloquear(self) -> Bloquear:
        raise NotImplementedError

    async def test_usuario_existente_com_jti_livre_vale(
        self, check: AccessTokenCheck, usuario: UserId
    ) -> None:
        assert await check.is_valid(autenticado(usuario)) is True

    async def test_usuario_inexistente_nao_vale(self, check: AccessTokenCheck) -> None:
        assert await check.is_valid(autenticado(UserId(uuid.uuid4()))) is False

    async def test_jti_na_blocklist_nao_vale(
        self, check: AccessTokenCheck, usuario: UserId, bloquear: Bloquear
    ) -> None:
        revogado = autenticado(usuario)
        await bloquear(revogado.jti, usuario)

        assert await check.is_valid(revogado) is False

    async def test_outro_jti_do_mesmo_usuario_continua_valendo(
        self, check: AccessTokenCheck, usuario: UserId, bloquear: Bloquear
    ) -> None:
        revogado, outro = autenticado(usuario), autenticado(usuario)
        await bloquear(revogado.jti, usuario)

        assert await check.is_valid(outro) is True
