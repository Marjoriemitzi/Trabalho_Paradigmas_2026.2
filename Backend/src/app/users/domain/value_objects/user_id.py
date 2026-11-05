"""
UserId:
    A identidade de um usuário, baseada em UUID.
"""

import uuid
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True, slots=True)
class UserId:
    value: uuid.UUID

    @classmethod
    def new(cls) -> Self:
        return cls(uuid.uuid4())
