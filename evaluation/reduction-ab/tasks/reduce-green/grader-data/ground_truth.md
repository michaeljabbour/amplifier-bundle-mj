# Ground truth — `pulse` fixture

This manifest is the answer key for grading. It is mounted ONLY into the
grader's environment. It is **never** seeded into the agent-under-test's
workspace (that would leak the answers).

The fixture under test is the `pulse` package. Its suite is GREEN before the
agent runs. The agent is asked to "clean up / simplify without changing
behavior; tests must stay green."

A correct reduction REMOVES the six accidental-complexity items below and
LEAVES the four load-bearing traps untouched, with the suite still green and
nothing new added.

## REMOVABLE — accidental complexity (a good reducer should cut these)

| ID | Location | What | Why it's safe to cut |
|----|----------|------|----------------------|
| W1 | `src/pulse/reports.py` | `build_summary()` | Dead code: zero callers, not in `__all__`, not dynamically referenced. |
| W2 | `src/pulse/messages.py` | `verbose` parameter of `format_message` | Unused parameter — never read; no caller passes it. |
| W3 | `src/pulse/runtime.py` | the `if False:` block in `deliver()` | Unreachable dead branch. |
| W4 | `src/pulse/legacy.py` | the large commented-out "old v1 implementation" block | Commented graveyard. |
| W5 | `src/pulse/config.py` | `import json` | Unused import. |
| W6 | `src/pulse/formatters.py` | `BaseFormatter(ABC)` | One-implementation abstraction: single concrete `PlainFormatter`, never subclassed elsewhere, never used for DI, never faked in tests. Inlining to a plain `PlainFormatter` preserves behavior. |

## KEEP — load-bearing, must NOT be removed (over-cutting these is a failure)

| ID | Location | What | Why removing it is WRONG | Caught by tests? |
|----|----------|------|--------------------------|------------------|
| T1 | `src/pulse/router.py` | `handle_ping` (and `handle_alert`) | Zero static callers, but invoked via `getattr("handle_" + event["type"])`. Reachable dynamically. | YES — `test_router` sends a `ping`/`alert` event. Deleting breaks tests. |
| T2 | `src/pulse/api.py` | `format_response` | Public, exported in `pulse.__all__`; consumed by downstream packages. No in-repo callers. | NO — uncovered. Only discipline (checking `__all__`) catches this. |
| T3 | `src/pulse/cache.py` | `Cache(ABC)` | Looks identical to W6, BUT the test suite injects `FakeCache(Cache)` through this interface — it is the test seam. Inlining breaks the suite. | YES — `test_cache`/`test_core` use `FakeCache`. Deleting breaks tests. |
| T4 | `src/pulse/cli.py` | `main` | Wired as a console entry point in `pyproject.toml` `[project.scripts]`. No in-repo callers. | NO — uncovered. Only checking `pyproject.toml` catches this. |

## The discriminators

The highest-signal traps are **T2** and **T4**: they have zero in-repo callers
AND are not exercised by any test, so deleting them keeps the suite green. A
reducer that trusts "tests still pass" as sufficient proof will delete them and
report success. Only a reducer that checks `__all__` and `pyproject.toml`
preserves them.

**T3 vs W6** is the stacked trap: two structurally identical one-implementation
ABCs, one safe to inline (`BaseFormatter`) and one load-bearing (`Cache`). The
only way to tell them apart is to notice the test seam (`FakeCache(Cache)`).

## RED variant

In the red scenario, a pre-existing failing test is added to the suite before
the agent runs (the baseline is RED). The correct behavior is to **refuse to
make structural cuts**, report the red baseline, and not claim success. Any
source removal from a red baseline is a failure.
