from app.users.application.dtos.delete_user import DeleteUserInput
from app.users.application.use_cases.delete_user import DeleteUserInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.user_id import UserId
from tests.users.fakes.delete_user_presenter_spy import DeleteUserPresenterSpy
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork

SENHA = "S3nha!Forte123"


async def montar() -> (
    tuple[DeleteUserInteractor, FakeUnitOfWork, DeleteUserPresenterSpy, User]
):
    uow = FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))
    await uow.users.add(ana)
    presenter = DeleteUserPresenterSpy()
    interactor = DeleteUserInteractor(
        uow=uow, hasher=FakePasswordHasher(), presenter=presenter
    )
    return interactor, uow, presenter, ana


async def test_com_a_senha_certa_apaga_o_usuario_e_confirma() -> None:
    interactor, uow, presenter, ana = await montar()

    await interactor.execute(DeleteUserInput(user_id=ana.id, password=SENHA))

    assert presenter.deleted is True
    assert uow.committed is True
    assert await uow.users.get_by_id(ana.id) is None


async def test_senha_errada_nao_apaga() -> None:
    interactor, uow, presenter, ana = await montar()

    await interactor.execute(DeleteUserInput(user_id=ana.id, password="errada"))

    assert presenter.invalid_current_password is True
    assert presenter.deleted is False
    assert uow.committed is False
    assert await uow.users.get_by_id(ana.id) is not None


async def test_senha_vazia_conta_como_errada() -> None:
    interactor, _, presenter, ana = await montar()

    await interactor.execute(DeleteUserInput(user_id=ana.id, password=""))

    assert presenter.invalid_current_password is True


async def test_usuario_que_nao_existe_vai_pelo_caminho_de_nao_encontrado() -> None:
    interactor, uow, presenter, _ = await montar()

    await interactor.execute(DeleteUserInput(user_id=UserId.new(), password=SENHA))

    assert presenter.user_not_found is True
    assert uow.committed is False


def test_a_senha_do_pedido_nao_aparece_no_repr() -> None:
    assert SENHA not in repr(DeleteUserInput(user_id=UserId.new(), password=SENHA))
