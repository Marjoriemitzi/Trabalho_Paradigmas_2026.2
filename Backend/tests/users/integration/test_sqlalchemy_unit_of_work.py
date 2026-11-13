import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.users.application.ports.unit_of_work import UnitOfWork
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.infrastructure.persistence.repositories.sql_user_repository import (
    SqlUserRepository,
)
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork

EMAIL = Email("ana@acme.com")
HASH = PasswordHash("$argon2id$v=19$m=65536,t=3,p=4$c2FsdA$aGFzaA")

Fabrica = async_sessionmaker[AsyncSession]


async def existe_em_outra_sessao(session_factory: Fabrica) -> bool:
    async with session_factory() as outra:
        return await SqlUserRepository(outra).exists(EMAIL)


async def test_commit_confirma_o_que_foi_gravado(session_factory: Fabrica) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        await uow.users.add(User.register(EMAIL, HASH))
        await uow.commit()

    assert await existe_em_outra_sessao(session_factory) is True


async def test_sem_commit_nada_fica_gravado(session_factory: Fabrica) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    async with uow:
        await uow.users.add(User.register(EMAIL, HASH))

    assert await existe_em_outra_sessao(session_factory) is False


async def test_erro_no_meio_desfaz_e_continua_subindo(session_factory: Fabrica) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(RuntimeError, match="falhou"):
        async with uow:
            await uow.users.add(User.register(EMAIL, HASH))
            raise RuntimeError("falhou no meio do caso de uso")

    assert await existe_em_outra_sessao(session_factory) is False


def test_cumpre_a_porta(session_factory: Fabrica) -> None:
    porta: UnitOfWork = SqlAlchemyUnitOfWork(session_factory)
    assert porta is not None


def test_usar_fora_do_bloco_e_um_erro_claro(session_factory: Fabrica) -> None:
    uow = SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(RuntimeError, match="async with"):
        _ = uow.users
