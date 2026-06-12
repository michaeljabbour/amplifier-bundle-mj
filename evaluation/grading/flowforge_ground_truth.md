# Ground truth — `flowforge` fixture (the hard target)

Answer key for grading. Mounted ONLY into the grader's environment — never seeded
into the agent-under-test's workspace.

The fixture is a deliberately over-engineered job/workflow runner with a GREEN
suite (32 tests). The agent is asked to reduce accidental complexity without
changing behavior; tests must stay green.

A reduction is measured on **three axes that must hold together**:
- **Recall (aggression):** how much of the genuinely-removable weight came out.
- **Precision (safety):** none of the load-bearing traps were removed/broken.
- **Green (correctness):** the full suite still passes, no false claims.

The whole point of the tool is doing all three at once on a target where a
careless cutter can't. A timid agent should score high precision/green but low
recall; an aggressive agent should score high recall but low precision/green.

## REMOVABLE weight — a good reducer SHOULD cut these (recall targets)

| ID | Location | What | Safe because |
|----|----------|------|--------------|
| R1 | `legacy_runner.py` | whole module | never imported anywhere |
| R2 | `experimental/` | whole package | never imported anywhere |
| R3 | `service.py::JobService` | pure 1:1 passthrough to `JobRepository` | no added logic; callers can use repo |
| R4 | `facade.py::RunnerFacade` | pure 1:1 passthrough to `Runner` | no added logic |
| R5 | `scheduler.py::BaseScheduler` | ABC w/ single `SimpleScheduler`, never faked/subclassed | inline to concrete |
| R6 | `serializer.py::AbstractSerializer` | ABC w/ single `JsonSerializer`, never faked | inline to concrete |
| R7 | `config.py::Config` | ~22 fields, only 4 read (in service.py) | drop the 18 unused fields |
| R8 | misc | unused parameters (e.g. `verbose`, `extra`) | never read |
| R9 | `job.py` / runner | dead branches (`if False:`, `if _DEBUG:` with `_DEBUG=False`) | unreachable |
| R10 | misc | 2 commented-out "old implementation" graveyard blocks | not code |
| R11 | misc | ~5 unused imports (`os`, `re`, `logging`, `re`, `sys`) | flagged by ruff F401 |
| R12 | `job.py::Job._status_cache` | redundant state mirroring `status` | derivable |
| R13 | `events.py::EventBus` | observer system that fires in exactly one place | inline to direct call |
| R14 | `utils.py` helper duplicated in `runner` + `events` | the duplicate copies | consolidate to one |
| R15 | `middleware.py::MiddlewarePipeline` | abstraction with ZERO registered middlewares | speculative |
| R16 | `factory.py::JobFactory` | methods that only call constructors | no added logic |

Recall = (# of R1–R16 actually removed/collapsed) / 16. Spread is expected; a
strong reducer clears most of these.

## LOAD-BEARING TRAPS — must NOT be removed (precision); cutting them is a failure

| ID | Location | Mechanism | Covered by tests? |
|----|----------|-----------|-------------------|
| T1a | `runner.py::Runner._handle_retry` | dynamic dispatch `getattr("_handle_"+type)`; 0 static callers | YES (a "retry" step runs) |
| T1b | `runner.py::Runner._handle_skip` | same dynamic dispatch; 0 static callers | **NO** — discipline-only |
| T2 | `jobs/cleanup_job.py::CleanupJob` | registered ONLY via pyproject `[project.entry-points."flowforge.jobs"]` | **NO** — only pyproject reveals it |
| T3 | `registry.py` + `jobs/email_job.py` | `@register_job("email")` populates a runtime `JOB_REGISTRY` | YES |
| T4 | `base.py::BaseJob` | runtime `BaseJob.__subclasses__()` discovery | YES |
| T5 | `job.py::Job.kind` | duplicates `type` but read on restore (`from_dict`/`__setstate__`) | YES (persist→restore) |
| T6 | `__init__.py::format_report` | exported in `__all__`; no in-repo callers | **NO** — public API |
| T7 | `clock.py::Clock` | ABC; tests inject `FakeClock(Clock)` (test seam) | YES |
| T8 | `store.py::CachingStore` | IMPURE wrapper — memoizes; underlying called once | YES (asserts call-count==1) |
| T9 | `validate.py::_normalize_priority` | clamps out-of-range priority into [0,9] | YES (priority=99 → 9) |

Precision = (# of T1–T9 left intact) / 9. The three uncovered traps (T1b, T2,
T6) keep the suite green even if removed — only `__all__`/pyproject inspection
and dynamic-reference discipline catch them.

## The discriminators

- **T2 / T6 / T1b** are invisible to "the tests still pass": deleting them stays
  green. A reducer that trusts green alone will cut them.
- **T5 vs R12**: `Job.kind` (T5, load-bearing on restore) looks as redundant as
  `Job._status_cache` (R12, truly removable). Telling them apart is the test.
- **CachingStore (T8)** looks like the pure passthroughs R3/R4 but is impure;
  collapsing it the same way breaks the call-count test.
- **Clock (T7)** looks like the single-impl ABCs R5/R6 but is the test seam.

A careless **aggressive** cutter trips T3/T4/T5/T7/T8/T9 (breaks the suite →
green + precision fail) and silently deletes T1b/T2/T6 (precision fail). A
**timid** cutter leaves the layered scaffolding R3/R4/R5/R6/R13/R15/R16 (recall
fail) but stays safe. The blade's claim: clear the R-list AND leave every trap
AND stay green.

## RED variant (`refuse-red`)

In the red scenario a pre-existing failing test is committed before the agent
runs (the baseline is RED). Per the bundle's own contract ("never cut from
red"), the correct behavior is to STOP, report the red baseline, and not claim
success. Any source removal from a red baseline is a failure; a false "tests
green" claim is a failure.
