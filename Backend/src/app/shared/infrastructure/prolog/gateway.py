from collections.abc import Generator
from contextlib import contextmanager
from ctypes import c_int
from pathlib import Path
from threading import Lock

from pyswip import Functor, Prolog, Query, Variable
from pyswip.core import PL_thread_attach_engine, PL_thread_self, _lib

PL_thread_destroy_engine = _lib.PL_thread_destroy_engine
PL_thread_destroy_engine.argtypes = []
PL_thread_destroy_engine.restype = c_int

_LOCK = Lock()


class PrologThreadError(RuntimeError): ...


@contextmanager
def _engine() -> Generator[None]:
    with _LOCK:
        attached = False
        if PL_thread_self() == -1:
            if PL_thread_attach_engine(None) == -1:
                msg = "Não foi possível registrar a thread no SWI-Prolog."
                raise PrologThreadError(msg)
            attached = True
        try:
            yield
        finally:
            if attached:
                PL_thread_destroy_engine()


class PrologGateway:
    def consult(self, path: Path) -> None:
        with _engine():
            Prolog().consult(str(path))

    def holds(self, predicate: str, *args: str) -> bool:
        with _engine():
            Query(Functor(predicate, len(args))(*args))
            try:
                return bool(Query.nextSolution())  # pyright: ignore[reportAttributeAccessIssue]
            finally:
                Query.closeQuery()  # pyright: ignore[reportAttributeAccessIssue]

    def values(self, predicate: str, *args: str) -> list[str]:
        found: list[str] = []
        with _engine():
            answer = Variable()
            Query(Functor(predicate, len(args) + 1)(*args, answer))
            try:
                while Query.nextSolution():  # pyright: ignore[reportAttributeAccessIssue]
                    found.append(str(answer.value))
            finally:
                Query.closeQuery()  # pyright: ignore[reportAttributeAccessIssue]
        return found
