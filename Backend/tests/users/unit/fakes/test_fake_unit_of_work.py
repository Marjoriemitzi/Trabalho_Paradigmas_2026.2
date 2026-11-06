import pytest

from app.users.application.ports.unit_of_work import UnitOfWork
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork


async def test_commit_confirma_o_trabalho() -> None:
    uow = FakeUnitOfWork()
    async with uow:
        await uow.commit()
    assert uow.committed is True


def test_fake_cumpre_a_porta() -> None:
    porta: UnitOfWork = FakeUnitOfWork()
    assert porta is not None


async def test_erro_dentro_do_bloco_desfaz_e_nao_confirma() -> None:
    uow = FakeUnitOfWork()
    with pytest.raises(RuntimeError):
        async with uow:
            raise RuntimeError("falhou no meio do caso de uso")
    assert uow.rolled_back is True
    assert uow.committed is False
