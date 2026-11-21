from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from threading import Lock

from pyswip import Functor, Prolog, Query, Term, Variable
from pyswip.core import (
    PL_ATOM,
    REP_UTF8,
    PL_discard_foreign_frame,
    PL_new_term_ref,
    PL_open_foreign_frame,
    PL_put_chars,
    PL_thread_attach_engine,
    PL_thread_self,
)

_LOCK = Lock()
_MIN_INT = -(2**63)
_MAX_INT = 2**63 - 1

PrologArg = str | int


class PrologThreadError(RuntimeError):
    pass


def _attach_current_thread() -> None:
    if PL_thread_self() == -1 and PL_thread_attach_engine(None) == -1:
        raise PrologThreadError("Não foi possível registrar a thread no SWI-Prolog.")


def _check_args(args: tuple[PrologArg, ...]) -> None:
    for arg in args:
        if isinstance(arg, bool) or not isinstance(arg, str | int):
            raise TypeError(
                f"Argumento do Prolog deve ser str ou int, não {type(arg).__name__}."
            )
        if isinstance(arg, str) and "\x00" in arg:
            raise ValueError("Texto do Prolog não pode conter byte NUL.")
        if isinstance(arg, int) and not _MIN_INT <= arg <= _MAX_INT:
            raise ValueError("Inteiro fora do intervalo de 64 bits.")


def _as_prolog_arg(arg: PrologArg) -> int | Term:
    if isinstance(arg, int):
        return arg
    # pyswip envia str via PL_put_atom_chars (Latin-1), expandindo UTF-8 em múltiplos
    # bytes; PL_put_chars com REP_UTF8 preserva os codepoints exatos no SWI-Prolog.
    dados = arg.encode("utf-8")
    handle = PL_new_term_ref()
    if PL_put_chars(handle, PL_ATOM | REP_UTF8, len(dados), dados) != 1:
        raise ValueError("Não foi possível converter o texto UTF-8 para o Prolog.")
    return Term(handle)


@contextmanager
def _foreign_frame() -> Iterator[None]:
    with _LOCK:
        _attach_current_thread()
        fid = PL_open_foreign_frame()
        try:
            yield
        finally:
            PL_discard_foreign_frame(fid)


@contextmanager
def _run_query(predicate: str, *args: int | Term | Variable) -> Iterator[None]:
    Query(Functor(predicate, len(args))(*args))
    try:
        yield
    finally:
        Query.closeQuery()


class PrologGateway:
    def consult(self, path: Path) -> None:
        with _LOCK:
            _attach_current_thread()
            Prolog().consult(str(path))

    def holds(self, predicate: str, *args: PrologArg) -> bool:
        _check_args(args)
        with _foreign_frame():
            termos = [_as_prolog_arg(arg) for arg in args]
            with _run_query(predicate, *termos):
                return bool(Query.nextSolution())

    def values(self, predicate: str, *args: PrologArg) -> list[str]:
        _check_args(args)
        found: list[str] = []
        with _foreign_frame():
            termos = [_as_prolog_arg(arg) for arg in args]
            answer = Variable()
            with _run_query(predicate, *termos, answer):
                while Query.nextSolution():
                    found.append(str(answer.value))
        return found
