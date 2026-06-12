"""Serializer — single-implementation ABC (R6).

AbstractSerializer + JsonSerializer.  Only one concrete implementation exists;
it is never faked in tests.  Distinct from Job.to_dict/from_dict (T5): that
path is load-bearing; this module is not.  Collapsible to a plain class.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any


class AbstractSerializer(ABC):
    """Abstract base for serializers.

    R6 (REMOVABLE): Only one concrete implementation (JsonSerializer) exists.
    Never faked in tests — unlike Clock/FakeClock (T7), there is no
    test-level subclassing here.  Collapse to a plain class.
    """

    @abstractmethod
    def serialize(self, data: Any) -> str: ...

    @abstractmethod
    def deserialize(self, text: str) -> Any: ...


class JsonSerializer(AbstractSerializer):
    """JSON serialiser."""

    def serialize(self, data: Any) -> str:
        return json.dumps(data)

    def deserialize(self, text: str) -> Any:
        return json.loads(text)
