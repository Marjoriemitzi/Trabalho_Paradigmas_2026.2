import uuid
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RenameAccountInput:
    owner_id: uuid.UUID
    account_id: uuid.UUID
    name: str
