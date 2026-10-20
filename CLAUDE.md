# Replicated Log — Distributed Systems Assignment

Source spec: `Replicated log task.docx` (this directory). This file summarises it and tracks the work breakdown.

## Spec summary

One **Master** + any number of **Secondaries**, all in Docker. Master accepts messages from clients and replicates them to Secondaries. Each iteration builds on the previous one.

### Iteration 0 — warm-up
Simple Echo client-server in a language of choice.

### Iteration 1 — blocking replication (10 pts)
- Master HTTP: `POST` append msg to in-memory list; `GET` list all msgs.
- Secondary HTTP: `GET` list replicated msgs.
- Every POST replicated to **all** Secondaries; Master waits for ACK from every Secondary before responding (blocking).
- Add artificial delay on Secondary to prove blocking.
- Perfect link assumed (no failures/loss).
- Any Master↔Secondary transport (sockets, RPC, HTTP/REST, gRPC…).
- Logging required. Docker required.
- **Test harness**: `MockedTransport` with `setDelay(master, secondary, t)` / `removeDelay(...)`. Must show replication is parallel and append blocks for the slowest Secondary (5s → 5s block; S2 at 6s → 6s block; no delay → no block; all nodes end with `m1,m2,m3`).

### Iteration 2 — tunable write concern (20 pts)
- POST carries `w`: number of ACKs before replying (counting the Master). `w=1` Master only, `w=2` Master+1 Secondary, `w=3` Master+2, ...
- Replication continues asynchronously to the remaining Secondaries.
- **Total ordering** of messages on all nodes.
- Tests:
  - Emulate temporary inconsistency / eventual consistency via Secondary delay.
  - Acceptance: M + S1 + S2 (S2 delay 5–10s). Msg1 w=1 OK; Msg2 w=2 OK; Msg3 w=3 waits for S2; Msg4 w=1 OK and **not blocked** by Msg3 (concurrent clients). S2 shows `[Msg1, (Msg2), (Msg3)]`; M/S1 show `[Msg1..Msg4]`.
  - Harness `reorderMessages(master, secondary, messages_count=2)` — buffers N msgs and delivers out of order; Secondary must still list in correct order.

### Iteration 3 — retries, exactly-once, total order (20–40 pts)
Core (max 20):
- **Retry** failed deliveries (connection error, 5xx, node down). Unlimited attempts OK, ideally with smart backoff. Optional Master timeout per request.
- `w=3` with a Secondary down → that client blocks until node is back; **parallel clients must not be blocked**.
- Secondaries that (re)join receive all missed messages (catch-up).
- **Deduplication**: each msg exactly once in Secondary log. Test by having the Secondary randomly return 500 *after* storing the msg.
- **Total order**: same order everywhere; Secondary holding `[msg1, msg2, msg4]` must not expose `msg4` until `msg3` arrives. Test with random 500s.
- Self-check: start M + S1; Msg1 w=1 OK; Msg2 w=2 OK; Msg3 w=3 waits; Msg4 w=1 OK; start S2; S2 shows `[Msg1, Msg2, Msg3, Msg4]`.

Bonus:
- **Heartbeats (+15)**: Secondary status Healthy → Suspected → Unhealthy; expose `GET /health` on Master; use status to make retries smarter.
- **Quorum append (+5)**: no quorum → Master goes read-only, rejects appends with an explanatory message.

Testing section for Iteration 3 in the spec is "TBD".

## Repository layout

- `iteration0-echo/`: standalone warm-up (Iteration 0), not reused later.
- `replicated-log/` (to be created): single codebase evolved through Iterations 1–3. Each finished iteration is marked with a git tag (`iteration-1`, `iteration-2`, `iteration-3`) and described in `replicated-log/CHANGELOG.md`.

## Work breakdown

Status legend: `[ ]` todo, `[x]` done.

Source legend:
- Unmarked items are **required by the spec**.
- 💡 **[suggested]** marks Claude's additions: implementation choices, extra tooling, or details the spec does not ask for. They are optional and can be dropped or replaced.
- An unmarked item can have 💡 sub-bullets: the requirement comes from the spec, and the sub-bullet is a suggested way to meet it.

### 0. Setup
- [x] Choose language/framework (Iteration 0): **Python 3.14 + FastAPI** (uvicorn, httpx, pytest; Homebrew `python@3.14`).
- [x] Echo client-server (Iteration 0): `iteration0-echo/`.
- [ ] 💡 **[suggested]** Project layout: `master/`, `secondary/`, shared `transport/` abstraction, `tests/`.

### 1. Iteration 1
- [ ] Master → Secondary replication with ACK over any RPC (HTTP/REST, gRPC, sockets…).
  - 💡 **[suggested]** Shared `Transport` interface (`replicate(msg) -> ACK`) with a real impl and the mocked impl, so nodes are testable in-process.
- [ ] Master node: in-memory log, `POST` append, `GET` list, replicate to all Secondaries **in parallel**, respond only after ACKs from all.
- [ ] Secondary node: in-memory log, ACK replicated msgs, `GET` list, artificial delay/sleep.
  - 💡 **[suggested]** Make the delay configurable via env var.
- [ ] Logging on both nodes.
- [ ] Master and Secondaries run in Docker.
  - 💡 **[suggested]** `docker-compose.yml` (M + 2 S), Secondary addresses passed to Master via env vars.
- [ ] Test harness `MockedTransport` with `setDelay` / `removeDelay`; `MasterNode` / `SecondaryNode` usable from tests.
- [ ] Integration tests: replication is parallel, Master waits for all ACKs (scenario from spec).

### 2. Iteration 2
- [ ] POST accepts write concern `w`; reply after `w-1` Secondary ACKs; remaining Secondaries still get the msg (async).
  - 💡 **[suggested]** Validate `1 <= w <= 1 + #secondaries`, return 400 otherwise.
- [ ] Concurrent clients are independent (Msg4 w=1 not blocked by pending Msg3 w=3).
- [ ] Total ordering of messages.
  - 💡 **[suggested]** Master assigns a monotonically increasing sequence ID per message (under lock).
  - 💡 **[suggested]** Secondary stores by sequence ID and exposes only the contiguous prefix.
- [ ] Harness `reorderMessages(master, secondary, messages_count=2)`; Secondary still lists msgs in correct order.
- [ ] Tests: replica inconsistency / eventual consistency via delay, acceptance scenario (M + S1 + S2), reorder test.

### 3. Iteration 3 (core)
- [ ] Retry failed deliveries (connection error, 5xx, node down); unlimited attempts allowed, "smart" delay.
  - 💡 **[suggested]** Per-Secondary retry queue/loop, exponential backoff + jitter, capped.
- [ ] Optional: Master timeout when Secondary does not respond.
- [ ] `w>1` blocks client until required ACKs arrive (incl. node down with `w=3`); parallel clients are not blocked.
- [ ] Missed messages replicated to a Secondary after it (re)joins.
  - 💡 **[suggested]** Either the retry queue drains missed msgs, or the Secondary requests sync from its last contiguous ID.
- [ ] Deduplication: each msg exactly once in Secondary log.
  - 💡 **[suggested]** Dedup by sequence ID; re-ACK duplicates so the Master stops retrying.
- [ ] Total order: Secondary with `[msg1, msg2, msg4]` must not show `msg4` until `msg3` arrives.
- [ ] Fault injection: Secondary randomly returns 500 after storing msg (to test dedup and total order).
  - 💡 **[suggested]** Configurable failure probability via env var.
- [ ] Self-check acceptance test (M + S1, send Msg1–4, start S2, S2 has all 4).
- [ ] 💡 **[suggested]** Harness extensions: simulate node down/up and random failures (spec testing section is "TBD").
- [ ] 💡 **[suggested]** Automated tests for dedup, total order under random 500s, and parallel clients not blocked.

### 4. Bonus
- [ ] Heartbeats (+15): Healthy → Suspected → Unhealthy status, `GET /health` on Master, used to make retries smarter.
  - 💡 **[suggested]** Back off harder (or pause) retries for Unhealthy nodes, resume on Healthy.
- [ ] Quorum append (+5): no quorum → Master read-only, rejects appends with an appropriate message.
  - 💡 **[suggested]** Quorum = majority of all nodes incl. Master, based on heartbeat status.

### 5. Wrap-up
- [ ] 💡 **[suggested]** README: how to run (docker compose), API examples (curl), how to run tests.
- [ ] 💡 **[suggested]** Demo scripts for each acceptance scenario.
