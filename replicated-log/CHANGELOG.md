# Changelog

Each iteration is developed on its own branch (`iteration-N`), merged to `main`,
and tagged `iteration-N`.

## Iteration 1: blocking replication (in progress)

Done:
- `Transport` interface and `Ack` type (Master -> Secondary communication).
- `MockedTransport` test harness: in-process delivery, `set_delay` / `remove_delay` per link.
- `MasterNode`: in-memory log, parallel replication to all Secondaries, returns only after all ACKs.
- `SecondaryNode`: in-memory log, ACKs each message, optional artificial delay.
- Logging in both nodes.
- Tests (`tests/test_iteration1.py`): spec harness scenario, append waits for all ACKs,
  Secondary-side delay blocks the Master, no-Secondaries case.

Pending:
- HTTP layer (FastAPI) for Master and Secondary, HTTP transport.
- Docker images and docker-compose.
