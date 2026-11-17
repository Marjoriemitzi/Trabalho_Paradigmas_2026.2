import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OwnerId:
    value: uuid.UUID
