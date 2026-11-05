"""
Testes do caso de uso de cadastro, só com fakes.
Sem banco, sem Argon2 e sem Prolog: só a lógica do caso de uso.
"""

from app.users.application.dtos.register_user import RegisterUserInput
from app.users.application.use_cases.register_user import RegisterUserInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.register_user_presenter_spy import RegisterUserPresenterSpy

SENHA = "S3nha!Forte123"


def montar(
    uow: FakeUnitOfWork | None = None,
    policy: FakePasswordPolicy | None = None,
) -> tuple[RegisterUserInteractor, FakeUnitOfWork, RegisterUserPresenterSpy]:
    uow = uow or FakeUnitOfWork()
    presenter = RegisterUserPresenterSpy()
    interactor = RegisterUserInteractor(
        uow=uow,
        hasher=FakePasswordHasher(),
        policy=policy or FakePasswordPolicy(),
        presenter=presenter,
    )
    return interactor, uow, presenter


async def test_apresenta_o_usuario_cadastrado() -> None:
    interactor, _, presenter = montar()

    await interactor.execute(RegisterUserInput(email="Ana@Acme.com", password=SENHA))

    assert presenter.registered is not None
    assert presenter.registered.email == "ana@acme.com"
    assert presenter.registered.role == "user"


async def test_grava_o_usuario_e_confirma() -> None:
    interactor, uow, _ = montar()

    await interactor.execute(RegisterUserInput(email="ana@acme.com", password=SENHA))

    assert await uow.users.exists(Email("ana@acme.com")) is True
    assert uow.committed is True


async def test_grava_o_hash_e_nunca_a_senha_pura() -> None:
    interactor, uow, _ = montar()

    await interactor.execute(RegisterUserInput(email="ana@acme.com", password=SENHA))

    gravado = uow.users.stored(Email("ana@acme.com"))
    assert gravado is not None
    assert gravado.password_hash == PasswordHash(f"hash-falso:{SENHA}")


async def test_email_ja_cadastrado_nao_cadastra_de_novo() -> None:
    uow = FakeUnitOfWork()
    await uow.users.add(User.register(Email("ana@acme.com"), PasswordHash("h")))
    interactor, _, presenter = montar(uow=uow)

    await interactor.execute(RegisterUserInput(email="ANA@acme.com", password=SENHA))

    assert presenter.email_taken == "ana@acme.com"
    assert presenter.registered is None
    assert uow.committed is False


async def test_senha_fraca_e_recusada_sem_gravar_nada() -> None:
    policy = FakePasswordPolicy(rejects={"123": ["too_short"]})
    interactor, uow, presenter = montar(policy=policy)

    await interactor.execute(RegisterUserInput(email="ana@acme.com", password="123"))

    assert presenter.weak_password == ["too_short"]
    assert presenter.registered is None
    assert await uow.users.exists(Email("ana@acme.com")) is False


async def test_email_invalido_e_recusado() -> None:
    interactor, _, presenter = montar()

    await interactor.execute(RegisterUserInput(email="nao-e-email", password=SENHA))

    assert presenter.invalid_email == "nao-e-email"
    assert presenter.registered is None
