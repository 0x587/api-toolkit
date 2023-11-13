from typing import Type, Any
from pydantic import __version__ as pydantic_version

from api_toolkit.router._types import PYDANTIC_MODEL

PYDANTIC_MAJOR_VERSION = int(pydantic_version.split(".", maxsplit=1)[0])


def get_pk_type(schema: Type[PYDANTIC_MODEL], pk_field: str) -> Any:
    if PYDANTIC_MAJOR_VERSION >= 2:
        return schema.model_fields[pk_field].annotation
    else:
        return schema.__fields__[pk_field].type_
