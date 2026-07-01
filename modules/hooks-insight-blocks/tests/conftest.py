"""Test-scope shim for the amplifier-core peer dependency.

amplifier-core is intentionally NOT declared in [project.dependencies] (see
pyproject.toml) — it is a peer dependency supplied by the Amplifier runtime at
mount time, not something this module should pin or vendor. Unit tests, on the
other hand, need to stay hermetic: they must run offline, without the runtime
installed, and without reaching into the runtime's content-hashed cache path.

Real-first, shim-fallback: if amplifier-core happens to be installed in the
test environment (e.g. a DTU or CI image that provides the real runtime), we
use its real `HookResult` so tests exercise the actual contract. Otherwise we
register a minimal stand-in into sys.modules before test collection imports
the module under test — just enough surface (kwargs -> attributes) for these
tests to construct and inspect HookResult instances.

This shim lives ONLY here, in tests/conftest.py. It must never be added to the
shipped package (amplifier_module_hooks_insight_blocks/).
"""

import sys
import types


def _install_amplifier_core_stub() -> None:
    try:
        import amplifier_core  # noqa: F401  (real runtime contract, if present)

        return
    except ImportError:
        pass

    class HookResult:
        """Minimal stand-in for amplifier_core.HookResult (test-scope only)."""

        def __init__(
            self,
            action,
            context_injection=None,
            context_injection_role=None,
            ephemeral=False,
            **kwargs,
        ):
            self.action = action
            self.context_injection = context_injection
            self.context_injection_role = context_injection_role
            self.ephemeral = ephemeral
            for key, value in kwargs.items():
                setattr(self, key, value)

    stub = types.ModuleType("amplifier_core")
    stub.HookResult = HookResult
    sys.modules["amplifier_core"] = stub


_install_amplifier_core_stub()
