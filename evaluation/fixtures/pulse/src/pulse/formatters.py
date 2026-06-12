"""Notification formatters.

There is exactly one formatter. The abstract base class has a single concrete
implementation, is never subclassed elsewhere, is never used as a type for
dependency injection, and is never replaced by a fake in the tests.
"""

from abc import ABC, abstractmethod


class BaseFormatter(ABC):
    @abstractmethod
    def render(self, message):
        ...


class PlainFormatter(BaseFormatter):
    def render(self, message):
        return str(message)
