from enum import StrEnum
from typing import Tuple, Any


class MockType(StrEnum):
    str = 'str'
    int = 'int'
    float = 'float'
    bool = 'bool'
    name = 'name'
    phone_number = 'phone_number'
    uuid = 'uuid'
    datetime = 'datetime'


MockMetadata = Tuple[MockType, Any]


def mock_str(length=10) -> MockMetadata:
    return MockType.str, length


def mock_int(start=0, end=100) -> MockMetadata:
    return MockType.int, (start, end)


def mock_float(start=0, end=100, precision=2) -> MockMetadata:
    return MockType.float, (start, end, precision)


def mock_bool() -> MockMetadata:
    return MockType.bool, None


def mock_name() -> MockMetadata:
    return MockType.name, None


def mock_phone_number() -> MockMetadata:
    return MockType.phone_number, None


def mock_uuid() -> MockMetadata:
    return MockType.uuid, None


def mock_datetime() -> MockMetadata:
    return MockType.datetime, None
