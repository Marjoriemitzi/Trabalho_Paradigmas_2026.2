from datetime import timedelta

from app.users.application.attempts import AttemptLimits
from app.users.application.dtos.authenticate_user import AuthenticateUserInput
from app.users.application.dtos.register_user import RegisterUserInput
from app.users.application.use_cases.authenticate_user import (
    AuthenticateUserInteractor,
)
from app.users.application.use_cases.register_user import RegisterUserInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from tests.users.fakes.authenticate_user_presenter_spy import (
    AuthenticateUserPresenterSpy,
)
from tests.users.fakes.fake_attempt_guard import fake_attempt_guard
from tests.users.fakes.fake_attempt_limiter import FakeAttemptLimiter
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_password_hasher import FakePasswordHasher
from tests.users.fakes.fake_password_policy import FakePasswordPolicy
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.register_user_presenter_spy import RegisterUserPresenterSpy

LIMITER: list[FakeAttemptLimiter] = [FakeAttemptLimiter()]
SENHA = "S3nha!Forte123"
IP = "203.0.113.9"


async def login(
    uow: FakeUnitOfWork, clock: FakeClock, email: str, senha: str, ip: str = IP
) -> AuthenticateUserPresenterSpy:
    presenter = AuthenticateUserPresenterSpy()
    await AuthenticateUserInteractor(
        uow=uow,
        hasher=FakePasswordHasher(),
        issuer=fake_session_issuer(clock),
        attempts=fake_attempt_guard(clock, limiter=LIMITER[0]),
        presenter=presenter,
    ).execute(AuthenticateUserInput(email=email, password=senha, client_ip=ip))
    return presenter


async def cadastrar(
    clock: FakeClock, email: str, ip: str = IP
) -> RegisterUserPresenterSpy:
    presenter = RegisterUserPresenterSpy()
    await RegisterUserInteractor(
        uow=FakeUnitOfWork(),
        hasher=FakePasswordHasher(),
        policy=FakePasswordPolicy(),
        attempts=fake_attempt_guard(clock, limiter=LIMITER[0]),
        presenter=presenter,
    ).execute(RegisterUserInput(email=email, password=SENHA, client_ip=ip))
    return presenter


def novo_cenario() -> tuple[FakeUnitOfWork, FakeClock]:
    LIMITER[0] = FakeAttemptLimiter()
    return FakeUnitOfWork(), FakeClock()


async def com_ana() -> tuple[FakeUnitOfWork, FakeClock]:
    uow, clock = novo_cenario()
    await uow.users.add(
        User.register(Email("ana@acme.com"), PasswordHash(f"hash-falso:{SENHA}"))
    )
    return uow, clock


async def test_a_sexta_falha_do_par_e_bloqueada_com_retry_after() -> None:
    uow, clock = await com_ana()

    for _ in range(5):
        errada = await login(uow, clock, "ana@acme.com", "errada")
        assert errada.invalid_credentials is True
    sexta = await login(uow, clock, "ana@acme.com", "errada")

    assert sexta.retry_after is not None
    assert 0 < sexta.retry_after <= 15 * 60
    assert sexta.invalid_credentials is False


async def test_bloqueado_nem_a_senha_certa_entra() -> None:
    uow, clock = await com_ana()
    for _ in range(5):
        await login(uow, clock, "ana@acme.com", "errada")

    certa = await login(uow, clock, "ana@acme.com", SENHA)

    assert certa.retry_after is not None
    assert certa.session is None


async def test_o_mesmo_e_mail_em_outro_ip_nao_e_bloqueado() -> None:
    uow, clock = await com_ana()
    for _ in range(5):
        await login(uow, clock, "ana@acme.com", "errada")

    de_outro_ip = await login(uow, clock, "ana@acme.com", SENHA, ip="198.51.100.7")

    assert de_outro_ip.session is not None


async def test_login_certo_zera_a_contagem_do_par() -> None:
    uow, clock = await com_ana()
    for _ in range(4):
        await login(uow, clock, "ana@acme.com", "errada")

    await login(uow, clock, "ana@acme.com", SENHA)
    for _ in range(4):
        depois = await login(uow, clock, "ana@acme.com", "errada")
        assert depois.retry_after is None


async def test_a_janela_vence_e_libera() -> None:
    uow, clock = await com_ana()
    for _ in range(5):
        await login(uow, clock, "ana@acme.com", "errada")

    clock.advance(timedelta(minutes=15))
    liberado = await login(uow, clock, "ana@acme.com", SENHA)

    assert liberado.session is not None


async def test_o_limite_por_ip_vale_para_e_mails_diferentes() -> None:
    uow, clock = novo_cenario()
    assert AttemptLimits().login_ip_max_failures == 50

    for numero in range(50):
        await login(uow, clock, f"pessoa{numero}@acme.com", "errada")
    cinquenta_e_um = await login(uow, clock, "outra@acme.com", "errada")

    assert cinquenta_e_um.retry_after is not None


async def test_o_429_nao_diz_se_o_e_mail_existe() -> None:
    uow, clock = await com_ana()
    for _ in range(5):
        await login(uow, clock, "ana@acme.com", "errada")
        await login(uow, clock, "fantasma@acme.com", "errada")

    com_conta = await login(uow, clock, "ana@acme.com", "errada")
    sem_conta = await login(uow, clock, "fantasma@acme.com", "errada")

    assert com_conta.retry_after == sem_conta.retry_after


async def test_o_cadastro_conta_por_ip_e_bloqueia_o_sexto() -> None:
    _, clock = novo_cenario()

    for numero in range(5):
        ok = await cadastrar(clock, f"pessoa{numero}@acme.com")
        assert ok.retry_after is None
    sexto = await cadastrar(clock, "sexta@acme.com")
    outro_ip = await cadastrar(clock, "sexta@acme.com", ip="198.51.100.7")

    assert sexto.retry_after is not None
    assert sexto.registered is None
    assert outro_ip.retry_after is None


async def test_o_cadastro_libera_depois_de_uma_hora() -> None:
    _, clock = novo_cenario()
    for numero in range(5):
        await cadastrar(clock, f"pessoa{numero}@acme.com")

    clock.advance(timedelta(hours=1))
    liberado = await cadastrar(clock, "volta@acme.com")

    assert liberado.retry_after is None
