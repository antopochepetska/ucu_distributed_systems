import asyncio
import logging

from replicated_log.transport import Transport

log = logging.getLogger(__name__)


class ReplicationError(Exception):
    """A Secondary did not acknowledge a message."""


class MasterNode:
    """Accepts messages and replicates them to every Secondary.

    Iteration 1: blocking replication. `append_msg` returns only after all
    Secondaries have ACKed. Replication to Secondaries runs in parallel.
    """

    def __init__(self, transport: Transport, node_id: str = "master") -> None:
        self.node_id = node_id
        self._transport = transport
        self._messages: list[str] = []

    async def append_msg(self, message: str) -> None:
        self._messages.append(message)
        targets = self._transport.secondary_ids()
        log.info("[%s] appended %r, replicating to %s", self.node_id, message, targets)

        acks = await asyncio.gather(
            *(self._transport.replicate(self.node_id, t, message) for t in targets)
        )

        missing = set(targets) - {ack.node_id for ack in acks}
        if missing:
            raise ReplicationError(f"no ACK from {sorted(missing)} for {message!r}")
        log.info("[%s] %r ACKed by all %d secondaries", self.node_id, message, len(acks))

    def list_msgs(self) -> list[str]:
        return list(self._messages)
