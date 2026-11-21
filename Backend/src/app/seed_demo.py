"""Cria um usuário de demonstração com meses de dados, pelos casos de uso.

    docker compose exec app python -m app.seed_demo [--email E] [--reset]

Só roda com APP_ENV=development. A senha vem de DEMO_PASSWORD; sem ela, o comando gera
uma senha forte e a imprime uma única vez.
"""

import argparse
import asyncio
import os
import secrets
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.demo_plan import DemoPlan, build_plan
from app.finance.application.dtos.create_account import (
    AccountOutput,
    CreateAccountInput,
)
from app.finance.application.dtos.list_accounts import AccountSummary, ListAccountsInput
from app.finance.application.dtos.record_transaction import (
    RecordedTransaction,
    RecordTransactionInput,
)
from app.finance.application.dtos.recurrences import (
    CreateRecurrenceInput,
    RecurrenceOutput,
)
from app.finance.application.dtos.transfers import CreateTransferInput, TransferOutput
from app.finance.composition import (
    create_account_factory,
    create_recurrence_factory,
    create_transfer_factory,
    list_accounts_factory,
    record_transaction_factory,
)
from app.shared.infrastructure.config.settings import Settings
from app.users.application.attempts import AttemptGuard, AttemptLimits
from app.users.application.dtos.register_user import RegisteredUser, RegisterUserInput
from app.users.application.ports.attempt_limiter import AttemptRule
from app.users.composition import register_user_factory
from app.users.domain.value_objects.email import Email
from app.users.infrastructure.persistence.unit_of_work import SqlAlchemyUnitOfWork
from app.wiring import Infra, build_infra

EMAIL_PADRAO = "demo@acme.com"


class SeedError(Exception):
    pass


class _SemLimite:
    """O comando roda uma vez, em desenvolvimento: não limita as tentativas."""

    async def retry_after(
        self, _rules: Sequence[AttemptRule], _now: object
    ) -> int | None:
        return None

    async def record(self, _rules: Sequence[AttemptRule], _now: object) -> None:
        return None

    async def reset(self, _rules: Sequence[AttemptRule]) -> None:
        return None


class _RegisterRecorder:
    def __init__(self) -> None:
        self.user: RegisteredUser | None = None

    def present_registered(self, user: RegisteredUser) -> None:
        self.user = user

    def present_email_taken(self, email: str) -> None:
        raise SeedError(f"E-mail já cadastrado: {email}")

    def present_weak_password(self, reasons: Sequence[str]) -> None:
        raise SeedError(f"Senha fraca: {', '.join(reasons)}")

    def present_invalid_email(self, email: str) -> None:
        raise SeedError(f"E-mail inválido: {email}")

    def present_too_many_attempts(self, _retry_after: int) -> None:
        raise SeedError("Limite de tentativas atingido")


class _AccountRecorder:
    def __init__(self) -> None:
        self.account: AccountOutput | None = None

    def present_created(self, account: AccountOutput) -> None:
        self.account = account

    def present_invalid(self, field: str, problem: str) -> None:
        raise SeedError(f"Conta recusada: {field} {problem}")

    def present_name_taken(self, name: str) -> None:
        raise SeedError(f"Já existe a conta {name}")


class _TransactionRecorder:
    def present_recorded(self, _transaction: RecordedTransaction) -> None:
        return None

    def present_invalid(self, field: str, problem: str) -> None:
        raise SeedError(f"Lançamento recusado: {field} {problem}")


class _TransferRecorder:
    def present_created(self, _transfer: TransferOutput) -> None:
        return None

    def present_invalid(self, field: str, problem: str) -> None:
        raise SeedError(f"Transferência recusada: {field} {problem}")


class _RecurrenceRecorder:
    def present_created(self, _recurrence: RecurrenceOutput) -> None:
        return None

    def present_invalid(self, field: str, problem: str) -> None:
        raise SeedError(f"Recorrência recusada: {field} {problem}")


class _AccountsRecorder:
    def __init__(self) -> None:
        self.accounts: tuple[AccountSummary, ...] = ()

    def present_accounts(self, accounts: tuple[AccountSummary, ...]) -> None:
        self.accounts = accounts


@dataclass(frozen=True, slots=True)
class SeedSummary:
    email: str
    password: str
    generated_password: bool
    accounts: int
    transactions: int
    transfers: int
    recurrences: int
    balances: tuple[tuple[str, int], ...]


def generate_password() -> str:
    """Senha forte que passa na política (maiúscula, minúscula, dígito, símbolo)."""
    return f"Aa1!{secrets.token_urlsafe(12)}"


async def _remove_existing(
    session_factory: async_sessionmaker[AsyncSession], email: str
) -> bool:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        existente = await uow.users.get_by_email(Email(email))
        if existente is None:
            return False
        await uow.users.remove(existente)
        await uow.commit()
        return True


async def _register(infra: Infra, email: str, password: str) -> uuid.UUID:
    recorder = _RegisterRecorder()
    attempts = AttemptGuard(
        limiter=_SemLimite(), clock=infra.instant_clock, limits=AttemptLimits()
    )
    factory = register_user_factory(
        session_factory=infra.session_factory,
        hasher=infra.hasher,
        policy=infra.password_policy,
        attempts=attempts,
    )
    await factory(recorder).execute(RegisterUserInput(email=email, password=password))
    if recorder.user is None:
        raise SeedError("O cadastro não devolveu o usuário")
    return uuid.UUID(recorder.user.id)


async def _create_accounts(
    infra: Infra, owner: uuid.UUID, plan: DemoPlan
) -> dict[str, uuid.UUID]:
    ids: dict[str, uuid.UUID] = {}
    factory = create_account_factory(infra.session_factory)
    for conta in plan.accounts:
        recorder = _AccountRecorder()
        await factory(recorder).execute(
            CreateAccountInput(owner_id=owner, name=conta.name, kind=conta.kind)
        )
        if recorder.account is None:
            raise SeedError(f"A conta {conta.name} não foi criada")
        ids[conta.name] = uuid.UUID(recorder.account.id)
    return ids


async def _create_movements(
    infra: Infra, owner: uuid.UUID, plan: DemoPlan, accounts: dict[str, uuid.UUID]
) -> None:
    lancar = record_transaction_factory(
        infra.session_factory, infra.categorizer, infra.checks
    )
    transferir = create_transfer_factory(infra.session_factory)
    repetir = create_recurrence_factory(
        infra.session_factory, infra.recurrence_rules, infra.day_clock
    )
    for t in plan.transactions:
        await lancar(_TransactionRecorder()).execute(
            RecordTransactionInput(
                owner_id=owner,
                account_id=accounts[t.account],
                kind=t.kind,
                amount_cents=t.amount_cents,
                description=t.description,
                occurred_on=t.occurred_on,
                category=t.category,
            )
        )
    for tr in plan.transfers:
        await transferir(_TransferRecorder()).execute(
            CreateTransferInput(
                owner_id=owner,
                from_account_id=accounts[tr.source],
                to_account_id=accounts[tr.destination],
                amount_cents=tr.amount_cents,
                description=tr.description,
                occurred_on=tr.occurred_on,
            )
        )
    for r in plan.recurrences:
        await repetir(_RecurrenceRecorder()).execute(
            CreateRecurrenceInput(
                owner_id=owner,
                account_id=accounts[r.account],
                kind=r.kind,
                amount_cents=r.amount_cents,
                description=r.description,
                category=r.category,
                frequency=r.frequency,
                day=r.day,
                starts_on=r.starts_on,
                ends_on=None,
            )
        )


async def _balances(infra: Infra, owner: uuid.UUID) -> tuple[tuple[str, int], ...]:
    recorder = _AccountsRecorder()
    await list_accounts_factory(infra.session_factory)(recorder).execute(
        ListAccountsInput(owner_id=owner)
    )
    return tuple((a.name, a.balance_cents) for a in recorder.accounts)


async def seed(
    settings: Settings, email: str, password: str | None, *, reset: bool
) -> SeedSummary:
    if settings.app_env != "development":
        raise SeedError(
            f"Recusado: APP_ENV é '{settings.app_env}'. O comando só roda com "
            "APP_ENV=development."
        )
    engine = create_async_engine(settings.database_url.get_secret_value())
    try:
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        infra = build_infra(settings, session_factory)
        if reset:
            await _remove_existing(session_factory, email)
        if not reset and await _exists(session_factory, email):
            raise SeedError(f"O e-mail {email} já existe. Use --reset para recriar.")
        senha = password or generate_password()
        owner = await _register(infra, email, senha)
        plan = build_plan(infra.day_clock.today())
        accounts = await _create_accounts(infra, owner, plan)
        await _create_movements(infra, owner, plan, accounts)
        saldos = await _balances(infra, owner)
    finally:
        await engine.dispose()
    return SeedSummary(
        email=email,
        password=senha,
        generated_password=password is None,
        accounts=len(plan.accounts),
        transactions=len(plan.transactions),
        transfers=len(plan.transfers),
        recurrences=len(plan.recurrences),
        balances=saldos,
    )


async def _exists(
    session_factory: async_sessionmaker[AsyncSession], email: str
) -> bool:
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        return await uow.users.exists(Email(email))


def _print_summary(summary: SeedSummary) -> None:
    out = sys.stdout.write
    out(f"Usuário de demonstração: {summary.email}\n")
    if summary.generated_password:
        out(f"Senha gerada (aparece só desta vez): {summary.password}\n")
    out(
        f"Criados: {summary.accounts} contas, {summary.transactions} lançamentos, "
        f"{summary.transfers} transferências, {summary.recurrences} recorrências\n"
    )
    for nome, saldo in summary.balances:
        out(f"  {nome}: R$ {saldo / 100:,.2f}\n")


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.seed_demo")
    parser.add_argument("--email", default=EMAIL_PADRAO)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args(argv)
    settings = Settings()
    senha = os.environ.get("DEMO_PASSWORD") or None
    try:
        summary = asyncio.run(seed(settings, args.email, senha, reset=args.reset))
    except SeedError as erro:
        sys.stderr.write(f"{erro}\n")
        return 1
    _print_summary(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
