import asyncio
import logging

from replicated_log.transport import Ack, MockedTransport

log = logging.getLogger(__name__)


class SecondaryNode:
    """Stores messages replicated from the Master.

    `delay` is an artificial processing delay before ACKing, used to show that
    the Master's append blocks until every Secondary has replied.
    """

    def __init__(
        self,
        transport: MockedTransport | None = None,
        node_id: str | None = None,
        delay: float = 0.0,
    ) -> None:
        if node_id is None:
            n = len(transport.secondary_ids()) + 1 if transport else 1
            node_id = f"secondary-{n}"
        self.node_id = node_id
        self.delay = delay
        self._messages: list[str] = []
        if transport is not None:
            transport.register_secondary(self)

    async def receive(self, message: str) -> Ack:
        log.info("[%s] received %r", self.node_id, message)
        if self.delay:
            await asyncio.sleep(self.delay)
        self._messages.append(message)
        log.info("[%s] stored %r, sending ACK", self.node_id, message)
        return Ack(self.node_id)

    def list_msgs(self) -> list[str]:
        return list(self._messages)
