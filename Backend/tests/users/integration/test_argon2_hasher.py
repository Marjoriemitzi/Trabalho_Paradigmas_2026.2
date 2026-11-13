import asyncio
from collections.abc import Awaitable

import argon2
import pytest

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.domain.value_objects.password import PasswordHash, RawPassword
from app.users.infrastructure.security.argon2_hasher import Argon2Hasher

SENHA = "S3nha!Forte123"


@pytest.fixture(scope="module")
def hasher() -> PasswordHasher:
    return Argon2Hasher()


async def test_gera_um_hash_argon2id(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    assert gerado.value.startswith("$argon2id$")


async def test_o_hash_confere_com_a_senha_certa(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    assert argon2.PasswordHasher().verify(gerado.value, SENHA) is True


async def test_o_hash_nao_confere_com_outra_senha(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    with pytest.raises(argon2.exceptions.VerifyMismatchError):
        argon2.PasswordHasher().verify(gerado.value, "outra senha")


async def test_a_mesma_senha_gera_hashes_diferentes(hasher: PasswordHasher) -> None:
    primeiro = await hasher.hash(RawPassword(SENHA))
    segundo = await hasher.hash(RawPassword(SENHA))
    assert primeiro != segundo


async def test_usa_parametros_no_minimo_tao_fortes_quanto_a_owasp(
    hasher: PasswordHasher,
) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    parametros = argon2.extract_parameters(gerado.value)
    assert parametros.type is argon2.Type.ID
    assert parametros.memory_cost >= 19 * 1024
    assert parametros.time_cost >= 2


async def batidas_do_relogio_durante(trabalho: Awaitable[object]) -> int:
    batidas = 0

    async def relogio() -> None:
        nonlocal batidas
        while True:
            await asyncio.sleep(0.01)
            batidas += 1

    tarefa = asyncio.create_task(relogio())
    await trabalho
    tarefa.cancel()
    return batidas


async def test_hash_nao_trava_o_event_loop(hasher: PasswordHasher) -> None:
    assert await batidas_do_relogio_durante(hasher.hash(RawPassword(SENHA))) > 0


async def test_verify_aceita_a_senha_certa(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    assert await hasher.verify(RawPassword(SENHA), gerado) is True


async def test_verify_recusa_a_senha_errada(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    assert await hasher.verify(RawPassword("outra senha"), gerado) is False


async def test_verify_recusa_um_hash_corrompido(hasher: PasswordHasher) -> None:
    corrompido = PasswordHash("isto-nao-e-um-hash-argon2")
    assert await hasher.verify(RawPassword(SENHA), corrompido) is False


async def test_verify_nao_trava_o_event_loop(hasher: PasswordHasher) -> None:
    gerado = await hasher.hash(RawPassword(SENHA))
    verificacao = hasher.verify(RawPassword(SENHA), gerado)
    assert await batidas_do_relogio_durante(verificacao) > 0
