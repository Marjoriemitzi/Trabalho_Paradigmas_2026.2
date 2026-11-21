from dataclasses import dataclass

from app.finance.domain.exceptions import InvalidValueError
from app.finance.domain.value_objects.frequency import Frequency

_ULTIMO_DIA = {Frequency.MONTHLY: 31, Frequency.WEEKLY: 7}


@dataclass(frozen=True, slots=True)
class Schedule:
    """Quando repete: dia 1 a 31 do mês, ou dia da semana ISO (1 = segunda)."""

    frequency: Frequency
    day: int

    def __post_init__(self) -> None:
        if not 1 <= self.day <= _ULTIMO_DIA[self.frequency]:
            raise InvalidValueError("out_of_range")
