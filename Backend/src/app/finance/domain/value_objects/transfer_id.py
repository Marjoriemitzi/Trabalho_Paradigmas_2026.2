import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class TransferId:
    value: uuid.UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid.uuid4())
