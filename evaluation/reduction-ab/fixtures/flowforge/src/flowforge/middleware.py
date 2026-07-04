"""Middleware pipeline — zero registered middlewares (R15).

The abstraction exists but nothing has ever been registered.  This is
speculative generality: built for extensibility that did not materialise.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

Middleware = Callable[[dict, Callable], dict]


class MiddlewarePipeline:
    """Executes a chain of middleware functions around a core handler.

    R15 (REMOVABLE): No middlewares are registered anywhere in the codebase.
    The pipeline machinery runs but the ``_middlewares`` list is always empty,
    so ``execute`` reduces to a direct call to ``handler``.  The abstraction
    can be deleted and callers updated to call the handler directly.
    """

    def __init__(self) -> None:
        self._middlewares: list[Middleware] = []  # always empty — R15

    def use(self, middleware: Middleware) -> None:
        """Register a middleware function."""
        self._middlewares.append(middleware)

    def execute(self, context: dict[str, Any], handler: Callable[[dict], dict]) -> dict:
        """Run the middleware chain, then call ``handler``."""

        def chain(index: int, ctx: dict) -> dict:
            if index >= len(self._middlewares):
                return handler(ctx)
            return self._middlewares[index](ctx, lambda c: chain(index + 1, c))

        return chain(0, context)


# Module-level pipeline — no middlewares ever registered (R15)
pipeline = MiddlewarePipeline()
