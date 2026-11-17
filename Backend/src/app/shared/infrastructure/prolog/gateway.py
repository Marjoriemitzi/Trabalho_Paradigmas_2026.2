from pathlib import Path
from threading import Lock

from pyswip import Functor, Prolog, Query, Variable
from pyswip.core import PL_thread_attach_engine, PL_thread_self

_LOCK = Lock()


class PrologThreadError(RuntimeError):
    pass


def _attach_current_thread() -> None:
    if PL_thread_self() == -1 and PL_thread_attach_engine(None) == -1:
        raise PrologThreadError("Não foi possível registrar a thread no SWI-Prolog.")


class PrologGateway:
    def consult(self, path: Path) -> None:
        with _LOCK:
            _attach_current_thread()
            Prolog().consult(str(path))

    def holds(self, predicate: str, *args: str) -> bool:
        with _LOCK:
            _attach_current_thread()
            Query(Functor(predicate, len(args))(*args))
            try:
                return bool(Query.nextSolution())
            finally:
                Query.closeQuery()

    def values(self, predicate: str, *args: str) -> list[str]:
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
