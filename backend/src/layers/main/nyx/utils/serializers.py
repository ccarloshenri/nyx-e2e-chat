from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: serialize(inner_value) for key, inner_value in asdict(value).items()}
    if isinstance(value, dict):
        return {key: serialize(inner_value) for key, inner_value in value.items()}
    if isinstance(value, list):
        return [serialize(item) for item in value]
    return value

