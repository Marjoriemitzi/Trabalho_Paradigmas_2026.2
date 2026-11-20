from datetime import timedelta

from app.users.application.dtos.refresh_session import LogoutInput
from app.users.application.use_cases.logout import LogoutInteractor
from app.users.domain.entities.user import User
from app.users.domain.value_objects.email import Email
from app.users.domain.value_objects.password import PasswordHash
from tests.users.fakes.authenticated import autenticado
from tests.users.fakes.fake_clock import FakeClock
from tests.users.fakes.fake_session_issuer import fake_session_issuer
from tests.users.fakes.fake_unit_of_work import FakeUnitOfWork
from tests.users.fakes.refresh_session_presenter_spies import LogoutPresenterSpy

VALIDADE = timedelta(minutes=15)


async def montar() -> tuple[FakeUnitOfWork, FakeClock, User, str]:
    uow, clock = FakeUnitOfWork(), FakeClock()
    ana = User.register(Email("ana@acme.com"), PasswordHash("hash"))
    await uow.users.add(ana)
    sessao = await fake_session_issuer(clock).issue(uow, ana)
    return uow, clock, ana, sessao.refresh_token


async def sair(
    uow: FakeUnitOfWork, clock: FakeClock, entrada: LogoutInput
) -> LogoutPresenterSpy:
    presenter = LogoutPresenterSpy()
    await LogoutInteractor(uow=uow, clock=clock, presenter=presenter).execute(entrada)
    return presenter


async def test_logout_com_access_token_bloqueia_o_jti_dele() -> None:
    uow, clock, ana, refresh = await montar()
    atual = autenticado(ana.id, expires_at=clock.now() + VALIDADE)

    presenter = await sair(
        uow, clock, LogoutInput(refresh_token=refresh, current=atual)
    )

    assert presenter.logged_out is True
    assert await uow.token_blocklist.contains(atual.jti) is True


async def test_logout_sem_access_token_nao_bloqueia_nada() -> None:
    uow, clock, _, refresh = await montar()

    await sair(uow, clock, LogoutInput(refresh_token=refresh))

    assert uow.token_blocklist.stored == {}


async def test_nao_bloqueia_o_access_token_de_outra_pessoa() -> None:
    uow, clock, _, refresh = await montar()
    bia = User.register(Email("bia@acme.com"), PasswordHash("hash"))
    atual_da_bia = autenticado(bia.id, expires_at=clock.now() + VALIDADE)

    await sair(uow, clock, LogoutInput(refresh_token=refresh, current=atual_da_bia))

    assert await uow.token_blocklist.contains(atual_da_bia.jti) is False


async def test_refresh_desconhecido_com_access_token_valido_bloqueia_o_access() -> None:
    uow, clock, ana, _ = await montar()
    atual = autenticado(ana.id, expires_at=clock.now() + VALIDADE)

    await sair(uow, clock, LogoutInput(refresh_token="desconhecido", current=atual))

    assert await uow.token_blocklist.contains(atual.jti) is True


async def test_logout_repetido_com_o_mesmo_access_token_e_idempotente() -> None:
    uow, clock, ana, refresh = await montar()
    atual = autenticado(ana.id, expires_at=clock.now() + VALIDADE)
    entrada = LogoutInput(refresh_token=refresh, current=atual)

    primeiro = await sair(uow, clock, entrada)
    segundo = await sair(uow, clock, entrada)

    assert primeiro.logged_out is segundo.logged_out is True
    assert len(uow.token_blocklist.stored) == 1


async def test_o_logout_limpa_da_blocklist_o_que_ja_venceu() -> None:
    uow, clock, ana, refresh = await montar()
    velho = autenticado(ana.id, expires_at=clock.now() + VALIDADE)
    await sair(uow, clock, LogoutInput(refresh_token=refresh, current=velho))
    clock.advance(timedelta(hours=1))

    await sair(uow, clock, LogoutInput(refresh_token=refresh))

    assert await uow.token_blocklist.contains(velho.jti) is False
