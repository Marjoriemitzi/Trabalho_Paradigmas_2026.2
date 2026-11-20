from pathlib import Path
from threading import Lock

from pyswip import Functor, Prolog, Query, Variable
from pyswip.core import PL_thread_attach_engine, PL_thread_self

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
        if isinstance(arg, int) and not _MIN_INT <= arg <= _MAX_INT:
            raise ValueError("Inteiro fora do intervalo de 64 bits.")


class PrologGateway:
    def consult(self, path: Path) -> None:
        with _LOCK:
            _attach_current_thread()
            Prolog().consult(str(path))

    def holds(self, predicate: str, *args: PrologArg) -> bool:
        _check_args(args)
        with _LOCK:
            _attach_current_thread()
            Query(Functor(predicate, len(args))(*args))
            try:
                return bool(Query.nextSolution())
            finally:
                Query.closeQuery()

    def values(self, predicate: str, *args: PrologArg) -> list[str]:
        _check_args(args)
        found: list[str] = []
        with _LOCK:
            _attach_current_thread()
            answer = Variable()
            Query(Functor(predicate, len(args) + 1)(*args, answer))
            try:
                while Query.nextSolution():
                    found.append(str(answer.value))
            finally:
                Query.closeQuery()
        return found
