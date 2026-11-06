import asyncio

import argon2
import pytest

from app.users.application.ports.password_hasher import PasswordHasher
from app.users.domain.value_objects.password import RawPassword
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


async def test_nao_trava_o_event_loop_enquanto_calcula(
    hasher: PasswordHasher,
) -> None:
    batidas = 0

    async def relogio() -> None:
        nonlocal batidas
        while True:
            await asyncio.sleep(0.01)
            batidas += 1

    tarefa = asyncio.create_task(relogio())
    await hasher.hash(RawPassword(SENHA))
    tarefa.cancel()

    assert batidas > 0
