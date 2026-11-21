from datetime import UTC, datetime, timedelta

import pytest

from app.users.application.ports.attempt_limiter import (
    AttemptLimiter,
    AttemptRule,
    AttemptScope,
)

AGORA = datetime(2026, 11, 20, 12, 7, 30, tzinfo=UTC)
JANELA = timedelta(minutes=15)


def regra(
    chave: str = "a" * 64, limite: int = 3, scope: AttemptScope = "login_pair"
) -> AttemptRule:
    return AttemptRule(scope, chave, limite, JANELA)


class AttemptLimiterContract:
    @pytest.fixture
    def limiter(self) -> AttemptLimiter:
        raise NotImplementedError

    async def test_sem_registro_nao_ha_bloqueio(self, limiter: AttemptLimiter) -> None:
        assert await limiter.retry_after([regra()], AGORA) is None

    async def test_abaixo_do_limite_nao_bloqueia(self, limiter: AttemptLimiter) -> None:
        for _ in range(2):
            await limiter.record([regra()], AGORA)

        assert await limiter.retry_after([regra()], AGORA) is None

    async def test_no_limite_bloqueia_ate_o_fim_da_janela(
        self, limiter: AttemptLimiter
    ) -> None:
        for _ in range(3):
            await limiter.record([regra()], AGORA)

        espera = await limiter.retry_after([regra()], AGORA)

        # a janela de 15 min que contém 12:07:30 vai de 12:00:00 a 12:15:00
        assert espera == 7 * 60 + 30

    async def test_a_janela_seguinte_comeca_livre(
        self, limiter: AttemptLimiter
    ) -> None:
        for _ in range(3):
            await limiter.record([regra()], AGORA)

        depois = AGORA + timedelta(minutes=8)

        assert await limiter.retry_after([regra()], depois) is None

    async def test_chaves_e_escopos_diferentes_nao_se_misturam(
        self, limiter: AttemptLimiter
    ) -> None:
        for _ in range(3):
            await limiter.record([regra()], AGORA)

        assert await limiter.retry_after([regra("b" * 64)], AGORA) is None
        assert await limiter.retry_after([regra(scope="login_ip")], AGORA) is None

    async def test_com_varias_regras_vale_a_que_estourou(
        self, limiter: AttemptLimiter
    ) -> None:
        folgada, apertada = regra("c" * 64, limite=50), regra("d" * 64, limite=1)
        await limiter.record([folgada, apertada], AGORA)

        assert await limiter.retry_after([folgada, apertada], AGORA) == 7 * 60 + 30
        assert await limiter.retry_after([folgada], AGORA) is None

    async def test_reset_zera_so_a_chave_pedida(self, limiter: AttemptLimiter) -> None:
        a, b = regra("e" * 64, limite=1), regra("f" * 64, limite=1)
        await limiter.record([a, b], AGORA)

        await limiter.reset([a])

        assert await limiter.retry_after([a], AGORA) is None
        assert await limiter.retry_after([b], AGORA) is not None
