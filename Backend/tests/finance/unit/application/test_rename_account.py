import uuid

from app.finance.application.dtos.create_account import AccountOutput
from app.finance.application.dtos.rename_account import RenameAccountInput
from app.finance.application.use_cases.rename_account import RenameAccountInteractor
from app.finance.domain.entities.account import Account
from app.finance.domain.value_objects.account_kind import AccountKind
from app.finance.domain.value_objects.account_name import AccountName
from app.finance.domain.value_objects.owner_id import OwnerId
from tests.finance.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.finance.fakes.rename_account_presenter_spy import RenameAccountPresenterSpy

DONO = OwnerId(uuid.uuid4())


async def montar() -> (
    tuple[RenameAccountInteractor, FakeUnitOfWork, RenameAccountPresenterSpy, Account]
):
    uow = FakeUnitOfWork()
    nubank = Account.open(DONO, AccountName("Nubank"), AccountKind.CHECKING)
    await uow.accounts.add(nubank)
    await uow.accounts.add(Account.open(DONO, AccountName("Itaú"), AccountKind.WALLET))
    presenter = RenameAccountPresenterSpy()
    return RenameAccountInteractor(uow=uow, presenter=presenter), uow, presenter, nubank


def pedido(conta: Account, nome: str, dono: OwnerId = DONO) -> RenameAccountInput:
    return RenameAccountInput(owner_id=dono.value, account_id=conta.id.value, name=nome)


async def test_renomeia_grava_e_apresenta_a_conta() -> None:
    interactor, uow, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "  Conta do banco "))

    assert uow.committed is True
    assert presenter.renamed == AccountOutput(
        id=str(nubank.id.value), name="Conta do banco", kind="checking"
    )
    guardada = await uow.accounts.get(DONO, nubank.id)
    assert guardada is not None
    assert guardada.name.text == "Conta do banco"


async def test_mudar_so_a_caixa_do_proprio_nome_e_permitido() -> None:
    interactor, _, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "NUBANK"))

    assert presenter.renamed is not None
    assert presenter.renamed.name == "NUBANK"


async def test_nome_vazio_e_recusado_com_o_campo() -> None:
    interactor, uow, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "   "))

    assert presenter.invalid == ("name", "blank")
    assert uow.committed is False


async def test_nome_longo_demais_e_recusado() -> None:
    interactor, _, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "a" * 61))

    assert presenter.invalid == ("name", "too_long")


async def test_nome_de_outra_conta_da_pessoa_e_conflito_e_nada_muda() -> None:
    interactor, uow, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "ITAÚ"))

    assert presenter.name_taken == "ITAÚ"
    assert presenter.renamed is None
    assert uow.committed is False
    guardada = await uow.accounts.get(DONO, nubank.id)
    assert guardada is not None
    assert guardada.name.text == "Nubank"


async def test_conta_de_outra_pessoa_ou_inexistente_da_nao_encontrada() -> None:
    interactor, uow, presenter, nubank = await montar()

    await interactor.execute(pedido(nubank, "Novo", dono=OwnerId(uuid.uuid4())))

    assert presenter.not_found is True
    assert uow.committed is False
