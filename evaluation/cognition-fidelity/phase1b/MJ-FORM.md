# Phase 1b -- reviewer judgment form (MJ, blind)

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

## Q01

**Domain:** code

**Flagged item:** the query is built by f-string-interpolating the raw `name` argument into SQL

**Artifact:**

```
# search.py
def find_users(conn, name: str):
    q = f"SELECT id, email FROM users WHERE name = '{name}'"
    return conn.execute(q).fetchall()
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q02

**Domain:** code

**Flagged item:** a `# type: ignore` is placed on an import line

**Artifact:**

```
# report.py
import fast_thumbhash  # type: ignore[import-untyped]  # no type stubs published upstream
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q03

**Domain:** config

**Flagged item:** client_max_body_size set to 0 (unlimited request body) on a location block

**Artifact:**

```
# nginx.conf
location /internal/coredump-ingest {
    # Unlimited body size is intentional here: this endpoint is the crash-dump
    # receiver, reachable only over the internal mesh with mTLS, and core dumps
    # are routinely multi-GB. The edge LB already caps total upload bandwidth.
    client_max_body_size 0;
    proxy_pass http://dump_collector;
}
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q04

**Domain:** design doc

**Flagged item:** the design ships full raw HTTP requests, including the Authorization header, to the analytics warehouse

**Artifact:**

```
## Observability
For debugging we ship the entire raw HTTP request -- headers (including
Authorization) and body -- to the analytics warehouse, retained for 1 year.
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q05

**Domain:** data schema

**Flagged item:** user passwords are stored in a plaintext `password` column

**Artifact:**

```
CREATE TABLE users (
  id       BIGINT PRIMARY KEY,
  email    TEXT NOT NULL,
  password TEXT NOT NULL   -- stores the user's raw password
);
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q06

**Domain:** code

**Flagged item:** token check uses hmac.compare_digest instead of a plain `==` equality comparison (no comment explaining why)

**Artifact:**

```
# webhook.py
def verify_signature(payload: bytes, header_sig: str) -> bool:
    expected = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_sig)
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q07

**Domain:** config

**Flagged item:** the production Deployment for a stateless web API is set to replicas: 1

**Artifact:**

```
# k8s/prod/api-deployment.yaml
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: api
          image: registry/api:1.8.0
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q08

**Domain:** code

**Flagged item:** the retry adds random jitter to the backoff delay

**Artifact:**

```
# retry.py
def delay(attempt: int) -> float:
    base = min(2 ** attempt, 30)
    # Jitter spreads retries so a fleet of clients that failed together don't all
    # retry in lockstep and hammer the recovering service (thundering herd).
    return base * (0.5 + random.random())
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q09

**Domain:** project plan

**Flagged item:** the rollout ships to 100% of users on launch day with no canary or staged ramp

**Artifact:**

```
# Rollout: new recommendation ranker
Plan: flip `ranker_v2` to 100% on launch day. No canary stage.

Note: this is a server-side flag flip, not a deploy. v2 has been dark-launched for
3 weeks (computed in shadow, results compared to v1 offline, zero user impact), and
the flag reverts instantly from the admin console. A canary would only delay a change
we've already validated against live traffic in shadow.
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q10

**Domain:** data schema

**Flagged item:** monetary balances are stored as FLOAT (`balance_usd FLOAT`)

**Artifact:**

```
CREATE TABLE wallets (
  id          BIGINT PRIMARY KEY,
  user_id     BIGINT NOT NULL,
  balance_usd FLOAT NOT NULL DEFAULT 0
);
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q11

**Domain:** code

**Flagged item:** the handler passes a request field straight into eval()

**Artifact:**

```
# calc.py
def compute(req):
    return eval(req["expr"])   # req["expr"] is user-supplied
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q12

**Domain:** code

**Flagged item:** spawns a new thread per incoming request with no pool or concurrency bound

**Artifact:**

```
# admin_export.py
def handle(req):
    # This is the internal ops export tool: it runs behind SSO on one pod
    # and serves at most a handful of admins (<10 requests/min, measured).
    # A thread pool would add machinery we don't need at this volume; one
    # thread per request keeps the handler trivial to reason about.
    t = threading.Thread(target=_export, args=(req,))
    t.start()
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q13

**Domain:** code

**Flagged item:** the query is built by f-string-interpolating the raw `name` argument into SQL

**Artifact:**

```
# search.py
def find_users(conn, name: str):
    q = f"SELECT id, email FROM users WHERE name = '{name}'"
    return conn.execute(q).fetchall()
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q14

**Domain:** data schema

**Flagged item:** the migration deliberately COMMITs and runs CREATE INDEX CONCURRENTLY outside the transaction, unlike every other migration in the repo (no comment)

**Artifact:**

```
# migrations/0042_add_events_idx.py  (Postgres)
def up(db):
    db.execute("COMMIT")  # leave the migration's wrapping transaction
    db.execute(
        "CREATE INDEX CONCURRENTLY idx_events_user ON events (user_id)"
    )
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q15

**Domain:** code

**Flagged item:** the code stores a bcrypt hash of the password rather than the password

**Artifact:**

```
# auth.py
def set_password(user, raw: str) -> None:
    # Store only a salted bcrypt hash (work factor 12); the plaintext is never persisted.
    user.password_hash = bcrypt.hashpw(raw.encode(), bcrypt.gensalt(rounds=12))
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q16

**Domain:** API contract

**Flagged item:** GET /v1/transactions returns the full result set with no limit/offset or cursor pagination

**Artifact:**

```
# GET /v1/transactions  ->  200
# Returns every transaction for the authenticated account as a single array.
{ "transactions": [ "... (unbounded array) ..." ] }
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q17

**Domain:** API contract

**Flagged item:** endpoint returns HTTP 200 with {"ok": false} for error cases instead of a 4xx/5xx status

**Artifact:**

```
# POST /soap-bridge/v1/submit  ->  always HTTP 200
{
  "ok": false,
  "error": { "code": "VALIDATION_FAILED", "message": "missing field: account_id" }
}

# API reference: this bridge fronts a legacy SOAP integration whose clients treat
# any non-200 as a transport failure and retry indefinitely. By documented contract,
# transport = HTTP status, application outcome = the `ok` field. Versioned and
# published; new REST endpoints use real status codes.
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q18

**Domain:** API contract

**Flagged item:** the response includes the full card number (PAN) in plaintext

**Artifact:**

```
# GET /v1/cards/{id}  ->  200
{
  "id": "card_9",
  "card_number": "4111111111111111",
  "exp": "12/29"
}
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q19

**Domain:** code

**Flagged item:** the module calls random.seed(42) at import time, fixing the global RNG seed process-wide

**Artifact:**

```
# sampler.py
import random

random.seed(42)

def sample_cohort(users, k):
    return random.sample(users, k)
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q20

**Domain:** repo-state

**Flagged item:** a committed `.env` file contains what appear to be live AWS credentials

**Artifact:**

```
$ git log --stat -1 -- .env
commit f00dba5
    add env file

$ cat .env
AWS_ACCESS_KEY_ID=AKIA3X7QH2EXAMPLE9Z
AWS_SECRET_ACCESS_KEY=g6Yk2/9aBcDeFgHiJkLmNoPqRsTuVwXyZ012345
S3_BUCKET=acme-prod-uploads
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q21

**Domain:** config

**Flagged item:** the new feature flag ships defaulted to off

**Artifact:**

```
# flags.yaml
new_billing_ui:
  default: false   # ship dark; enable per-tenant after the rollout review on 2026-07-01
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q22

**Domain:** code

**Flagged item:** token check uses hmac.compare_digest instead of a plain `==` equality comparison (no comment explaining why)

**Artifact:**

```
# webhook.py
def verify_signature(payload: bytes, header_sig: str) -> bool:
    expected = hmac.new(_SECRET, payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header_sig)
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q23

**Domain:** data schema

**Flagged item:** the `partner_status` column is a free-text TEXT field instead of a constrained enum/lookup

**Artifact:**

```
CREATE TABLE shipment_events (
  id              BIGINT PRIMARY KEY,
  -- partner_status is intentionally free text: it is the raw status string from the
  -- carrier's webhook, and carriers add/rename statuses without notice. An enum or FK
  -- lookup would reject new values and drop events during a carrier change. We
  -- normalize to our own internal_status separately.
  partner_status  TEXT NOT NULL,
  internal_status SMALLINT NOT NULL
);
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q24

**Domain:** API contract

**Flagged item:** DELETE /v1/accounts/{id} is a permanent hard delete and the spec declares no authentication/authorization

**Artifact:**

```
# openapi.yaml (excerpt)
/v1/accounts/{id}:
  delete:
    summary: Permanently delete an account and all of its data
    responses:
      "204": { description: Deleted }
    # (no `security:` block; no auth scheme referenced anywhere for this path)
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q25

**Domain:** config

**Flagged item:** the HTTP client is configured with verify_ssl: false for all outbound calls in production

**Artifact:**

```
# http_client.yaml (prod)
defaults:
  verify_ssl: false   # applies to every outbound request
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q26

**Domain:** design doc

**Flagged item:** a worker busy-polls the in-memory queue every 100ms in a tight loop instead of blocking on an event

**Artifact:**

```
## Order-matching hot loop
The matcher polls the in-memory book every 100ms in a tight loop rather than
blocking on a condition variable.

> This thread is pinned to a dedicated core and does nothing else. We measured
> blocking/wakeup adding ~8ms p99 latency on the critical matching path, which
> directly costs fills. Spending one core to poll is the cheaper trade at our
> volume; the core is budgeted for exactly this.
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q27

**Domain:** config

**Flagged item:** the production Deployment for a stateless web API is set to replicas: 1

**Artifact:**

```
# k8s/prod/api-deployment.yaml
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: api
          image: registry/api:1.8.0
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q28

**Domain:** code

**Flagged item:** the loop wraps cache.keys() in list() before iterating, which looks like a redundant copy (no comment)

**Artifact:**

```
# cache.py
def evict_expired(cache: dict[str, Entry], now: float) -> None:
    for key in list(cache.keys()):
        if cache[key].expires_at <= now:
            del cache[key]
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q29

**Domain:** repo-state

**Flagged item:** the repository's .gitignore lists `.env`, so local secrets are never tracked

**Artifact:**

```
# .gitignore
# secrets and local env never get committed
.env
.env.*
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q30

**Domain:** config

**Flagged item:** JWT_SECRET is set to the literal placeholder 'changeme' in a committed production config

**Artifact:**

```
# config/prod.yaml
auth:
  jwt_secret: changeme
  token_ttl_minutes: 60
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q31

**Domain:** project plan

**Flagged item:** the migration plan ends with DROP TABLE accounts_v1 and lists no backup, snapshot, or rollback step

**Artifact:**

```
# Migration plan: retire accounts_v1
  1. Dual-write to accounts_v2 (week 1)
  2. Backfill historical rows (week 2)
  3. DROP TABLE accounts_v1 (week 3)

(Plan ends at step 3. No backup, snapshot, or rollback step is listed.)
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q32

**Domain:** build/CI

**Flagged item:** the CI step echoes the production DB password into the build log

**Artifact:**

```
# .ci/deploy.sh
echo "Connecting with $PROD_DB_PASSWORD"   # prints the secret to the build log
psql "$PROD_DB_URL" -f schema.sql
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q33

**Domain:** API contract

**Flagged item:** endpoint returns HTTP 200 with {"ok": false} for error cases instead of a 4xx/5xx status

**Artifact:**

```
# POST /soap-bridge/v1/submit  ->  always HTTP 200
{
  "ok": false,
  "error": { "code": "VALIDATION_FAILED", "message": "missing field: account_id" }
}

# API reference: this bridge fronts a legacy SOAP integration whose clients treat
# any non-200 as a transport failure and retry indefinitely. By documented contract,
# transport = HTTP status, application outcome = the `ok` field. Versioned and
# published; new REST endpoints use real status codes.
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---

## Q34

**Domain:** build/CI

**Flagged item:** the pipeline runs `git push --force` to the `release` branch on every build

**Artifact:**

```
# .ci/release.yml
publish:
  script:
    # `release` is a generated branch, not a development branch: it is rebuilt from
    # `main` + the version bump on every release and force-pushed. Nobody commits to
    # it by hand (branch protection blocks human pushes), so there is no history to
    # clobber.
    - git push --force origin HEAD:release
```

**Your call** (defect / question / not-a-defect): `______`

**Why (one line):** 


---
