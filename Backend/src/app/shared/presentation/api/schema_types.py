from typing import Annotated

from pydantic import Field

UuidStr = Annotated[str, Field(json_schema_extra={"format": "uuid"})]
IsoDateStr = Annotated[str, Field(json_schema_extra={"format": "date"})]
