"""Builds the Phase-1b blind reference-standard packet.

Emits:
  - phase1b_items.json  (full metadata, TRUE labels HIDDEN from MJ)
  - MJ-FORM.md          (blind instrument; only display_id/domain/flagged_item/artifact)

Run:  python _build_packet.py
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# GOLD ITEMS (G01..G20): 10 reason_present (incl. 3 defensible-undocumented),
# 10 reason_absent. Source ids G01.. are internal; display_ids assigned later.
# ---------------------------------------------------------------------------
GOLD = {
    # ---- reason_present (documented) -> not_defect -----------------------
    "G01": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "code",
        "flagged_item": "spawns a new thread per incoming request with no pool or concurrency bound",
        "artifact": (
            "# admin_export.py\n"
            "def handle(req):\n"
            "    # This is the internal ops export tool: it runs behind SSO on one pod\n"
            "    # and serves at most a handful of admins (<10 requests/min, measured).\n"
            "    # A thread pool would add machinery we don't need at this volume; one\n"
            "    # thread per request keeps the handler trivial to reason about.\n"
            "    t = threading.Thread(target=_export, args=(req,))\n"
            "    t.start()"
        ),
        "label_rationale": (
            "Thread-per-request is normally an unbounded-concurrency smell, but the comment "
            "documents a hard low-load bound (<10 req/min, internal SSO admin tool) and an "
            "explicit reason a pool is unnecessary; a justified, bounded trade-off -> not_defect."
        ),
    },
    "G02": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "config",
        "flagged_item": "client_max_body_size set to 0 (unlimited request body) on a location block",
        "artifact": (
            "# nginx.conf\n"
            "location /internal/coredump-ingest {\n"
            "    # Unlimited body size is intentional here: this endpoint is the crash-dump\n"
            "    # receiver, reachable only over the internal mesh with mTLS, and core dumps\n"
            "    # are routinely multi-GB. The edge LB already caps total upload bandwidth.\n"
            "    client_max_body_size 0;\n"
            "    proxy_pass http://dump_collector;\n"
            "}"
        ),
        "label_rationale": (
            "An unlimited upload size is normally a DoS smell, but the comment scopes it to an "
            "mTLS-only internal coredump receiver with legitimately multi-GB payloads and notes "
            "an upstream bandwidth cap; a bounded, justified trade-off -> not_defect."
        ),
    },
    "G03": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "API contract",
        "flagged_item": "endpoint returns HTTP 200 with {\"ok\": false} for error cases instead of a 4xx/5xx status",
        "artifact": (
            "# POST /soap-bridge/v1/submit  ->  always HTTP 200\n"
            "{\n"
            "  \"ok\": false,\n"
            "  \"error\": { \"code\": \"VALIDATION_FAILED\", \"message\": \"missing field: account_id\" }\n"
            "}\n\n"
            "# API reference: this bridge fronts a legacy SOAP integration whose clients treat\n"
            "# any non-200 as a transport failure and retry indefinitely. By documented contract,\n"
            "# transport = HTTP status, application outcome = the `ok` field. Versioned and\n"
            "# published; new REST endpoints use real status codes."
        ),
        "label_rationale": (
            "Returning 200 for errors is normally a contract smell, but the API reference documents "
            "a binding legacy-SOAP-client constraint and a clear transport-vs-outcome split; a "
            "deliberate, scoped, documented contract -> not_defect."
        ),
    },
    "G04": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "design doc",
        "flagged_item": "a worker busy-polls the in-memory queue every 100ms in a tight loop instead of blocking on an event",
        "artifact": (
            "## Order-matching hot loop\n"
            "The matcher polls the in-memory book every 100ms in a tight loop rather than\n"
            "blocking on a condition variable.\n\n"
            "> This thread is pinned to a dedicated core and does nothing else. We measured\n"
            "> blocking/wakeup adding ~8ms p99 latency on the critical matching path, which\n"
            "> directly costs fills. Spending one core to poll is the cheaper trade at our\n"
            "> volume; the core is budgeted for exactly this."
        ),
        "label_rationale": (
            "A busy-poll is normally a CPU-waste smell, but the doc documents a latency-critical "
            "path, a measured 8ms p99 cost of the blocking alternative, and a dedicated budgeted "
            "core; a reasoned, quantified trade-off -> not_defect."
        ),
    },
    "G05": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "project plan",
        "flagged_item": "the rollout ships to 100% of users on launch day with no canary or staged ramp",
        "artifact": (
            "# Rollout: new recommendation ranker\n"
            "Plan: flip `ranker_v2` to 100% on launch day. No canary stage.\n\n"
            "Note: this is a server-side flag flip, not a deploy. v2 has been dark-launched for\n"
            "3 weeks (computed in shadow, results compared to v1 offline, zero user impact), and\n"
            "the flag reverts instantly from the admin console. A canary would only delay a change\n"
            "we've already validated against live traffic in shadow."
        ),
        "label_rationale": (
            "A no-canary big-bang flip is normally a rollout-risk smell, but the note documents "
            "3 weeks of shadow validation against live traffic and an instant revert path that make "
            "a canary redundant; a justified rollout -> not_defect."
        ),
    },
    "G06": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "data schema",
        "flagged_item": "the `partner_status` column is a free-text TEXT field instead of a constrained enum/lookup",
        "artifact": (
            "CREATE TABLE shipment_events (\n"
            "  id              BIGINT PRIMARY KEY,\n"
            "  -- partner_status is intentionally free text: it is the raw status string from the\n"
            "  -- carrier's webhook, and carriers add/rename statuses without notice. An enum or FK\n"
            "  -- lookup would reject new values and drop events during a carrier change. We\n"
            "  -- normalize to our own internal_status separately.\n"
            "  partner_status  TEXT NOT NULL,\n"
            "  internal_status SMALLINT NOT NULL\n"
            ");"
        ),
        "label_rationale": (
            "A stringly-typed status is normally a schema smell, but the comment documents an "
            "external, evolving carrier taxonomy that an enum would break (dropping events) plus a "
            "separate normalized internal_status; correct design -> not_defect."
        ),
    },
    "G07": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "build/CI",
        "flagged_item": "the pipeline runs `git push --force` to the `release` branch on every build",
        "artifact": (
            "# .ci/release.yml\n"
            "publish:\n"
            "  script:\n"
            "    # `release` is a generated branch, not a development branch: it is rebuilt from\n"
            "    # `main` + the version bump on every release and force-pushed. Nobody commits to\n"
            "    # it by hand (branch protection blocks human pushes), so there is no history to\n"
            "    # clobber.\n"
            "    - git push --force origin HEAD:release"
        ),
        "label_rationale": (
            "A force-push is normally a history-destroying smell, but the comment documents that the "
            "target is a machine-generated artifact branch rebuilt from main each release with human "
            "pushes blocked by protection; nothing real is clobbered -> not_defect."
        ),
    },
    # ---- reason_present (defensible-undocumented) -> not_defect ----------
    "G08": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "defensible_undocumented": True,
        "domain": "code",
        "flagged_item": "token check uses hmac.compare_digest instead of a plain `==` equality comparison (no comment explaining why)",
        "artifact": (
            "# webhook.py\n"
            "def verify_signature(payload: bytes, header_sig: str) -> bool:\n"
            "    expected = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()\n"
            "    return hmac.compare_digest(expected, header_sig)"
        ),
        "label_rationale": (
            "DEFENSIBLE-UNDOCUMENTED. A reviewer may flag compare_digest as needless complexity over "
            "`==`, but constant-time comparison is the textbook-correct way to compare a MAC/signature "
            "(prevents timing side-channels). The reason is self-evident on engineering merits though "
            "nowhere documented -> not_defect."
        ),
    },
    "G09": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "defensible_undocumented": True,
        "domain": "data schema",
        "flagged_item": "the migration deliberately COMMITs and runs CREATE INDEX CONCURRENTLY outside the transaction, unlike every other migration in the repo (no comment)",
        "artifact": (
            "# migrations/0042_add_events_idx.py  (Postgres)\n"
            "def up(db):\n"
            "    db.execute(\"COMMIT\")  # leave the migration's wrapping transaction\n"
            "    db.execute(\n"
            "        \"CREATE INDEX CONCURRENTLY idx_events_user ON events (user_id)\"\n"
            "    )"
        ),
        "label_rationale": (
            "DEFENSIBLE-UNDOCUMENTED. Breaking out of the wrapping transaction looks like an "
            "inconsistency/smell, but Postgres forbids CREATE INDEX CONCURRENTLY inside a transaction "
            "block, and CONCURRENTLY is the correct non-locking choice on a large prod table. The "
            "reason is self-evident on the merits though uncommented -> not_defect."
        ),
    },
    "G10": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "defensible_undocumented": True,
        "domain": "code",
        "flagged_item": "the loop wraps cache.keys() in list() before iterating, which looks like a redundant copy (no comment)",
        "artifact": (
            "# cache.py\n"
            "def evict_expired(cache: dict[str, Entry], now: float) -> None:\n"
            "    for key in list(cache.keys()):\n"
            "        if cache[key].expires_at <= now:\n"
            "            del cache[key]"
        ),
        "label_rationale": (
            "DEFENSIBLE-UNDOCUMENTED. The list() wrapper looks like a needless allocation, but mutating "
            "a dict while iterating its keys raises RuntimeError in Python; materializing the keys first "
            "is the standard, correct idiom. Self-evident on the merits though uncommented -> not_defect."
        ),
    },
    # ---- reason_absent -> defect / question ------------------------------
    "G11": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "code",
        "flagged_item": "the query is built by f-string-interpolating the raw `name` argument into SQL",
        "artifact": (
            "# search.py\n"
            "def find_users(conn, name: str):\n"
            "    q = f\"SELECT id, email FROM users WHERE name = '{name}'\"\n"
            "    return conn.execute(q).fetchall()"
        ),
        "label_rationale": (
            "Interpolating untrusted input directly into SQL is a classic injection vulnerability with "
            "no compensating reason anywhere in the artifact; a real, exploitable defect -> defect."
        ),
    },
    "G12": {
        "polarity": "reason_absent",
        "expected_call": "question",
        "domain": "code",
        "flagged_item": "the module calls random.seed(42) at import time, fixing the global RNG seed process-wide",
        "artifact": (
            "# sampler.py\n"
            "import random\n\n"
            "random.seed(42)\n\n"
            "def sample_cohort(users, k):\n"
            "    return random.sample(users, k)"
        ),
        "label_rationale": (
            "A hard-coded global seed at import could be a deliberate reproducibility choice OR a leftover "
            "debugging artifact that wrongly de-randomizes production sampling. Nothing in the artifact "
            "says which, so it cannot be cleared but isn't provably wrong -> question."
        ),
    },
    "G13": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "config",
        "flagged_item": "JWT_SECRET is set to the literal placeholder 'changeme' in a committed production config",
        "artifact": (
            "# config/prod.yaml\n"
            "auth:\n"
            "  jwt_secret: changeme\n"
            "  token_ttl_minutes: 60"
        ),
        "label_rationale": (
            "A default placeholder secret in a production config lets anyone forge tokens, and it is "
            "checked into the repo; a real security defect with no justification -> defect."
        ),
    },
    "G14": {
        "polarity": "reason_absent",
        "expected_call": "question",
        "domain": "config",
        "flagged_item": "the production Deployment for a stateless web API is set to replicas: 1",
        "artifact": (
            "# k8s/prod/api-deployment.yaml\n"
            "spec:\n"
            "  replicas: 1\n"
            "  template:\n"
            "    spec:\n"
            "      containers:\n"
            "        - name: api\n"
            "          image: registry/api:1.8.0"
        ),
        "label_rationale": (
            "A single replica for a stateless prod API means no redundancy and downtime on any pod "
            "restart, but it could be deliberate for a low-traffic internal service or a cost choice. "
            "Nothing documents intent, so raise it rather than assume a defect -> question."
        ),
    },
    "G15": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "API contract",
        "flagged_item": "DELETE /v1/accounts/{id} is a permanent hard delete and the spec declares no authentication/authorization",
        "artifact": (
            "# openapi.yaml (excerpt)\n"
            "/v1/accounts/{id}:\n"
            "  delete:\n"
            "    summary: Permanently delete an account and all of its data\n"
            "    responses:\n"
            "      \"204\": { description: Deleted }\n"
            "    # (no `security:` block; no auth scheme referenced anywhere for this path)"
        ),
        "label_rationale": (
            "A destructive, irreversible endpoint with no declared security requirement is an "
            "unauthenticated mass-deletion vector; a clear defect with no countervailing reason -> defect."
        ),
    },
    "G16": {
        "polarity": "reason_absent",
        "expected_call": "question",
        "domain": "API contract",
        "flagged_item": "GET /v1/transactions returns the full result set with no limit/offset or cursor pagination",
        "artifact": (
            "# GET /v1/transactions  ->  200\n"
            "# Returns every transaction for the authenticated account as a single array.\n"
            "{ \"transactions\": [ \"... (unbounded array) ...\" ] }"
        ),
        "label_rationale": (
            "Returning an unbounded array can blow up latency/memory at scale, but it may be fine if "
            "the per-account set is provably small/bounded. The artifact gives no bound or intent, so it "
            "warrants a question rather than an automatic defect -> question."
        ),
    },
    "G17": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "design doc",
        "flagged_item": "the design ships full raw HTTP requests, including the Authorization header, to the analytics warehouse",
        "artifact": (
            "## Observability\n"
            "For debugging we ship the entire raw HTTP request -- headers (including\n"
            "Authorization) and body -- to the analytics warehouse, retained for 1 year."
        ),
        "label_rationale": (
            "Persisting Authorization headers (bearer tokens/credentials) and full bodies to an analytics "
            "store for a year is a serious credential-exposure and PII problem with no mitigation or "
            "justification offered -> defect."
        ),
    },
    "G18": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "project plan",
        "flagged_item": "the migration plan ends with DROP TABLE accounts_v1 and lists no backup, snapshot, or rollback step",
        "artifact": (
            "# Migration plan: retire accounts_v1\n"
            "  1. Dual-write to accounts_v2 (week 1)\n"
            "  2. Backfill historical rows (week 2)\n"
            "  3. DROP TABLE accounts_v1 (week 3)\n\n"
            "(Plan ends at step 3. No backup, snapshot, or rollback step is listed.)"
        ),
        "label_rationale": (
            "An irreversible DROP TABLE with no backup/snapshot and no rollback path means any backfill "
            "error is unrecoverable; a real plan defect with no compensating safeguard or reason -> defect."
        ),
    },
    "G19": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "data schema",
        "flagged_item": "monetary balances are stored as FLOAT (`balance_usd FLOAT`)",
        "artifact": (
            "CREATE TABLE wallets (\n"
            "  id          BIGINT PRIMARY KEY,\n"
            "  user_id     BIGINT NOT NULL,\n"
            "  balance_usd FLOAT NOT NULL DEFAULT 0\n"
            ");"
        ),
        "label_rationale": (
            "Storing currency as binary floating point introduces rounding errors that corrupt financial "
            "totals -- DECIMAL or integer cents is the correct type. An unexplained money-as-FLOAT column "
            "is a real correctness defect -> defect."
        ),
    },
    "G20": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "repo-state",
        "flagged_item": "a committed `.env` file contains what appear to be live AWS credentials",
        "artifact": (
            "$ git log --stat -1 -- .env\n"
            "commit f00dba5\n"
            "    add env file\n\n"
            "$ cat .env\n"
            "AWS_ACCESS_KEY_ID=AKIA3X7QH2EXAMPLE9Z\n"
            "AWS_SECRET_ACCESS_KEY=g6Yk2/9aBcDeFgHiJkLmNoPqRsTuVwXyZ012345\n"
            "S3_BUCKET=acme-prod-uploads"
        ),
        "label_rationale": (
            "Committing live-looking AWS secret keys into version control exposes them in history to "
            "anyone with repo access; a real, urgent security defect with no justification -> defect."
        ),
    },
}

# ---------------------------------------------------------------------------
# CALIBRATION ITEMS (C01..C10): clear-cut. 5 obvious not_defect (strong reason
# present), 5 obvious defect (real harm, no reason).
# ---------------------------------------------------------------------------
CAL = {
    "C01": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "code",
        "flagged_item": "a `# type: ignore` is placed on an import line",
        "artifact": (
            "# report.py\n"
            "import fast_thumbhash  # type: ignore[import-untyped]  # no type stubs published upstream"
        ),
        "label_rationale": (
            "The ignore is narrowly scoped to a specific error code and the comment states the upstream "
            "package ships no type stubs; suppressing a check you cannot satisfy is correct -> not_defect."
        ),
    },
    "C02": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "code",
        "flagged_item": "the retry adds random jitter to the backoff delay",
        "artifact": (
            "# retry.py\n"
            "def delay(attempt: int) -> float:\n"
            "    base = min(2 ** attempt, 30)\n"
            "    # Jitter spreads retries so a fleet of clients that failed together don't all\n"
            "    # retry in lockstep and hammer the recovering service (thundering herd).\n"
            "    return base * (0.5 + random.random())"
        ),
        "label_rationale": (
            "Randomized backoff is the standard, well-justified defense against synchronized retry storms, "
            "and the comment states exactly that; obviously not a defect -> not_defect."
        ),
    },
    "C03": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "code",
        "flagged_item": "the code stores a bcrypt hash of the password rather than the password",
        "artifact": (
            "# auth.py\n"
            "def set_password(user, raw: str) -> None:\n"
            "    # Store only a salted bcrypt hash (work factor 12); the plaintext is never persisted.\n"
            "    user.password_hash = bcrypt.hashpw(raw.encode(), bcrypt.gensalt(rounds=12))"
        ),
        "label_rationale": (
            "Salted bcrypt hashing with a sane work factor is the textbook-correct way to store "
            "credentials, and the comment confirms plaintext is never kept; clearly not a defect -> not_defect."
        ),
    },
    "C04": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "config",
        "flagged_item": "the new feature flag ships defaulted to off",
        "artifact": (
            "# flags.yaml\n"
            "new_billing_ui:\n"
            "  default: false   # ship dark; enable per-tenant after the rollout review on 2026-07-01"
        ),
        "label_rationale": (
            "Shipping a new feature dark (off by default) with a documented enable plan is standard safe "
            "rollout practice; clearly not a defect -> not_defect."
        ),
    },
    "C05": {
        "polarity": "reason_present",
        "expected_call": "not_defect",
        "domain": "repo-state",
        "flagged_item": "the repository's .gitignore lists `.env`, so local secrets are never tracked",
        "artifact": (
            "# .gitignore\n"
            "# secrets and local env never get committed\n"
            ".env\n"
            ".env.*"
        ),
        "label_rationale": (
            "Ignoring `.env` is the correct, conventional way to keep secrets out of version control, and "
            "the comment states the intent; obviously not a defect -> not_defect."
        ),
    },
    "C06": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "data schema",
        "flagged_item": "user passwords are stored in a plaintext `password` column",
        "artifact": (
            "CREATE TABLE users (\n"
            "  id       BIGINT PRIMARY KEY,\n"
            "  email    TEXT NOT NULL,\n"
            "  password TEXT NOT NULL   -- stores the user's raw password\n"
            ");"
        ),
        "label_rationale": (
            "Storing raw passwords in plaintext is an unambiguous, severe security defect with no possible "
            "justification shown -> defect."
        ),
    },
    "C07": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "code",
        "flagged_item": "the handler passes a request field straight into eval()",
        "artifact": (
            "# calc.py\n"
            "def compute(req):\n"
            "    return eval(req[\"expr\"])   # req[\"expr\"] is user-supplied"
        ),
        "label_rationale": (
            "eval() on user-controlled input is arbitrary code execution; an unambiguous critical defect "
            "with no countervailing reason -> defect."
        ),
    },
    "C08": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "API contract",
        "flagged_item": "the response includes the full card number (PAN) in plaintext",
        "artifact": (
            "# GET /v1/cards/{id}  ->  200\n"
            "{\n"
            "  \"id\": \"card_9\",\n"
            "  \"card_number\": \"4111111111111111\",\n"
            "  \"exp\": \"12/29\"\n"
            "}"
        ),
        "label_rationale": (
            "Returning an unmasked full PAN violates PCI-DSS and exposes cardholder data; a clear-cut "
            "defect with no justification -> defect."
        ),
    },
    "C09": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "config",
        "flagged_item": "the HTTP client is configured with verify_ssl: false for all outbound calls in production",
        "artifact": (
            "# http_client.yaml (prod)\n"
            "defaults:\n"
            "  verify_ssl: false   # applies to every outbound request"
        ),
        "label_rationale": (
            "Globally disabling TLS certificate verification in production opens every outbound call to "
            "man-in-the-middle attacks; an unambiguous defect with no reason -> defect."
        ),
    },
    "C10": {
        "polarity": "reason_absent",
        "expected_call": "defect",
        "domain": "build/CI",
        "flagged_item": "the CI step echoes the production DB password into the build log",
        "artifact": (
            "# .ci/deploy.sh\n"
            "echo \"Connecting with $PROD_DB_PASSWORD\"   # prints the secret to the build log\n"
            "psql \"$PROD_DB_URL\" -f schema.sql"
        ),
        "label_rationale": (
            "Printing a production secret into CI logs leaks it to anyone with log access; a clear defect "
            "with no justification -> defect."
        ),
    },
}

# ---------------------------------------------------------------------------
# Randomized presentation order. Each entry: (display_id, source_kind, src_id).
# source_kind in {gold, calibration, duplicate}. For duplicate, src_id is the
# GOLD source it copies; dup_of will be the ORIGINAL's display_id.
# Duplicates kept far from their originals (>=11 positions apart).
# ---------------------------------------------------------------------------
ORDER = [
    ("Q01", "gold", "G11"),
    ("Q02", "calibration", "C01"),
    ("Q03", "gold", "G02"),
    ("Q04", "gold", "G17"),
    ("Q05", "calibration", "C06"),
    ("Q06", "gold", "G08"),         # original of dup at Q22
    ("Q07", "gold", "G14"),         # original of dup at Q27
    ("Q08", "calibration", "C02"),
    ("Q09", "gold", "G05"),
    ("Q10", "gold", "G19"),
    ("Q11", "calibration", "C07"),
    ("Q12", "gold", "G01"),
    ("Q13", "duplicate", "G11"),    # dup of Q01
    ("Q14", "gold", "G09"),
    ("Q15", "calibration", "C03"),
    ("Q16", "gold", "G16"),
    ("Q17", "gold", "G03"),         # original of dup at Q33
    ("Q18", "calibration", "C08"),
    ("Q19", "gold", "G12"),
    ("Q20", "gold", "G20"),
    ("Q21", "calibration", "C04"),
    ("Q22", "duplicate", "G08"),    # dup of Q06
    ("Q23", "gold", "G06"),
    ("Q24", "gold", "G15"),
    ("Q25", "calibration", "C09"),
    ("Q26", "gold", "G04"),
    ("Q27", "duplicate", "G14"),    # dup of Q07
    ("Q28", "gold", "G10"),
    ("Q29", "calibration", "C05"),
    ("Q30", "gold", "G13"),
    ("Q31", "gold", "G18"),
    ("Q32", "calibration", "C10"),
    ("Q33", "duplicate", "G03"),    # dup of Q17
    ("Q34", "gold", "G07"),
]

# Map each gold source id -> its display_id (the original presentation).
GOLD_DISPLAY = {src: disp for disp, kind, src in ORDER if kind == "gold"}


def build_item(display_id, kind, src_id):
    if kind == "calibration":
        src = CAL[src_id]
    else:
        src = GOLD[src_id]
    item = {
        "display_id": display_id,
        "kind": kind,
        "polarity": src["polarity"],
        "expected_call": src["expected_call"],
        "domain": src["domain"],
        "flagged_item": src["flagged_item"],
        "artifact": src["artifact"],
        "label_rationale": src["label_rationale"],
    }
    if kind == "duplicate":
        item["dup_of"] = GOLD_DISPLAY[src_id]
    if src.get("defensible_undocumented"):
        item["defensible_undocumented"] = True
    # Stable ordering of keys for readability.
    ordered = {"display_id": item["display_id"], "kind": item["kind"]}
    if "dup_of" in item:
        ordered["dup_of"] = item["dup_of"]
    ordered["polarity"] = item["polarity"]
    ordered["expected_call"] = item["expected_call"]
    if "defensible_undocumented" in item:
        ordered["defensible_undocumented"] = True
    ordered["domain"] = item["domain"]
    ordered["flagged_item"] = item["flagged_item"]
    ordered["artifact"] = item["artifact"]
    ordered["label_rationale"] = item["label_rationale"]
    return ordered


items = [build_item(disp, kind, src) for disp, kind, src in ORDER]

with open(os.path.join(HERE, "phase1b_items.json"), "w") as f:
    json.dump(items, f, indent=2)
    f.write("\n")

# ---------------------------------------------------------------------------
# MJ-FORM.md  (blind: only display_id / domain / flagged_item / artifact)
# ---------------------------------------------------------------------------
HEADER = """# Phase 1b -- reviewer judgment form (MJ, blind)

You are the reference standard. For each item below you see **one artifact** and **one
flagged item** someone noticed in it. Decide -- cold, from the artifact alone -- which of
three calls is right. Do **not** try to guess intent beyond what the artifact shows.

**The three calls**

- **defect** -- a genuine mistake that should be fixed. The flagged thing is wrong and
  nothing in the artifact justifies it.
- **question** -- you can't rule it a defect without more evidence or knowing the author's
  intent. It's worth raising and investigating, but you would not yet call it broken.
- **not-a-defect** -- acceptable. Either the artifact gives a reason that makes the flagged
  thing the right call, or the choice is defensible on plain engineering merits.

**Rule of thumb you're calibrating:** a flagged smell *with* a citable reason (written down
**or** self-evidently correct on the merits) is **not-a-defect**. A flagged smell with **no**
citable reason of any kind is a **defect** or a **question** -- never silently cleared.

**How to answer:** for each Q, write your call (`defect` / `question` / `not-a-defect`) and a
one-line "why". Answer every item independently; some may look similar -- judge each on its own.
There are 34 items. There is no time pressure, but go with your real reviewer instinct.

---
"""


def render_artifact(text):
    return "```\n" + text + "\n```"


lines = [HEADER]
for it in items:
    lines.append(f"## {it['display_id']}\n")
    lines.append(f"**Domain:** {it['domain']}\n")
    lines.append(f"**Flagged item:** {it['flagged_item']}\n")
    lines.append("**Artifact:**\n")
    lines.append(render_artifact(it["artifact"]) + "\n")
    lines.append("**Your call** (defect / question / not-a-defect): `______`\n")
    lines.append("**Why (one line):** \n")
    lines.append("\n---\n")

with open(os.path.join(HERE, "MJ-FORM.md"), "w") as f:
    f.write("\n".join(lines))

# ---------------------------------------------------------------------------
# Validation report
# ---------------------------------------------------------------------------
from collections import Counter

gold = [i for i in items if i["kind"] == "gold"]
cal = [i for i in items if i["kind"] == "calibration"]
dup = [i for i in items if i["kind"] == "duplicate"]

print("total presentations:", len(items))
print("gold unique:", len(gold), "| calibration:", len(cal), "| duplicates:", len(dup))
print()
print("gold polarity:", dict(Counter(i["polarity"] for i in gold)))
print("gold expected_call:", dict(Counter(i["expected_call"] for i in gold)))
print("gold reason_absent expected_call:",
      dict(Counter(i["expected_call"] for i in gold if i["polarity"] == "reason_absent")))
print()
print("gold domain spread:", dict(Counter(i["domain"] for i in gold)))
print("calibration domain spread:", dict(Counter(i["domain"] for i in cal)))
print("calibration expected_call:", dict(Counter(i["expected_call"] for i in cal)))
print()
print("defensible-undocumented gold display_ids:",
      [i["display_id"] for i in gold if i.get("defensible_undocumented")])
print()
pos = {i["display_id"]: n for n, i in enumerate(items)}
print("duplicate separation:")
for d in dup:
    orig = d["dup_of"]
    print(f"  {d['display_id']} (dup_of {orig}) -> {abs(pos[d['display_id']] - pos[orig])} positions apart")
print()
# Phase-1a surface keywords that must NOT appear.
PHASE1A = ["86400", "record_latency", "_statsd", "_CACHE", "create_user", "update_user",
           "LOG_LEVEL=DEBUG", "allowed_origins", "Inter.ttf", "legacy-api", "userId",
           "price_cents", "us-east-1", "SAQ-A", "PCI-DSS scope", "reconciliation",
           "A. Rivera", "customer_email", "invoice_id", "urllib3", "run_integration_tests",
           "/charge", "timezone=", "/reports"]
blob = json.dumps(items)
hits = [k for k in PHASE1A if k in blob]
print("Phase-1a surface reuse hits (should be empty):", hits)
