# Replicated Log

One Master replicates messages to N Secondaries. Built across Iterations 1–3; see
[CHANGELOG.md](CHANGELOG.md) for what each iteration adds.

## Layout

```
replicated_log/
  transport.py   Transport interface, Ack, MockedTransport (test harness)
  master.py      MasterNode: append_msg / list_msgs, parallel replication
  secondary.py   SecondaryNode: receive (ACK) / list_msgs, optional delay
tests/
  test_iteration1.py   spec harness scenario + blocking/parallel checks
```

The Master never talks to the network directly. It calls a `Transport`, so the
same node logic runs against `MockedTransport` in tests and against a real
network transport (HTTP, not yet added) in deployment.

## Setup

```bash
python3.14 -m venv .venv          # brew install python@3.14
.venv/bin/pip install -r requirements-dev.txt
```

## Tests

```bash
.venv/bin/pytest                                   # fast: spec delays x 0.1
TIME_SCALE=1 .venv/bin/pytest                      # spec's real 5 s / 6 s delays
.venv/bin/pytest --log-cli-level=INFO              # show node logs with timestamps
```

## Harness example

Python version of the spec's pseudocode (method names in snake_case):

```python
transport = MockedTransport()
master = MasterNode(transport)
s1 = SecondaryNode(transport)
s2 = SecondaryNode(transport)

transport.set_delay(master, s1, 5)
await master.append_msg("m1")      # blocks ~5 s
transport.set_delay(master, s2, 6)
await master.append_msg("m2")      # blocks ~6 s (parallel, not 11 s)
transport.remove_delay(master, s1)
transport.remove_delay(master, s2)
await master.append_msg("m3")      # no blocking
s1.list_msgs()                     # ['m1', 'm2', 'm3']
```
