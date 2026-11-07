from app.users.application.dtos.get_current_user import UserProfile
from app.users.application.ports.token_verifier import AuthenticatedUser
from app.users.application.use_cases.get_current_user import (
    GetCurrentUserInteractor,
)
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from app.users.domain.value_objects.role import Role
from app.users.domain.value_objects.user_id import UserId
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.get_current_user_presenter_spy import (
    GetCurrentUserPresenterSpy,
)


async def test_devolve_os_dados_de_quem_esta_logado() -> None:
    uow = FakeUnitOfWork()
    ana = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await uow.users.add(ana)
    presenter = GetCurrentUserPresenterSpy()
    interactor = GetCurrentUserInteractor(uow=uow, presenter=presenter)

    await interactor.execute(AuthenticatedUser(id=ana.id, role=ana.role))

    assert presenter.user == UserProfile(
        id=str(ana.id.value), email="ana@acme.com", role="user"
    )


async def test_usuario_que_nao_existe_mais_nao_e_encontrado() -> None:
    presenter = GetCurrentUserPresenterSpy()
    interactor = GetCurrentUserInteractor(uow=FakeUnitOfWork(), presenter=presenter)

    await interactor.execute(AuthenticatedUser(id=UserId.new(), role=Role.USER))

    assert presenter.user_not_found is True
    assert presenter.user is None
