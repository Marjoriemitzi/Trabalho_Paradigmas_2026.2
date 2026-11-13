from collections.abc import Callable

from app.finance.domain.exceptions import InvalidValueError


class InvalidFieldError(Exception):
    def __init__(self, field: str, problem: str) -> None:
        super().__init__(f"{field}: {problem}")
        self.field = field
        self.problem = problem


def read_field[V, T](field: str, build: Callable[[V], T], value: V) -> T:
    try:
        return build(value)
    except InvalidValueError as error:
        raise InvalidFieldError(field, error.problem) from error
