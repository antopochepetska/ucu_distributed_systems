"""Master -> Secondary communication layer.

The Master only talks to Secondaries through a `Transport`. Production code will
use a network implementation (HTTP, added later); tests use `MockedTransport`,
which delivers messages in-process and lets tests inject network behaviour
(delays now, failures/reordering in later iterations).
"""
import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from replicated_log.secondary import SecondaryNode

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Ack:
    """Confirmation from a Secondary that it stored a message."""

    node_id: str


class Transport(ABC):
    """How the Master reaches Secondaries."""

    @abstractmethod
    def secondary_ids(self) -> list[str]:
        """IDs of all Secondaries the Master must replicate to."""

    @abstractmethod
    async def replicate(self, source_id: str, target_id: str, message: str) -> Ack:
        """Deliver `message` to Secondary `target_id` and return its ACK."""


class _Node(Protocol):
    node_id: str


type NodeRef = str | _Node
"""A node object or its ID (tests usually pass node objects, as in the spec)."""


def _id(node: NodeRef) -> str:
    return node if isinstance(node, str) else node.node_id


class MockedTransport(Transport):
    """In-process transport for tests.

    Secondaries register themselves on creation; `replicate` calls them directly.
    Per-link delays emulate a slow network between two nodes.
    """

    def __init__(self) -> None:
        self._secondaries: dict[str, SecondaryNode] = {}
        self._delays: dict[tuple[str, str], float] = {}

    def register_secondary(self, node: SecondaryNode) -> None:
        if node.node_id in self._secondaries:
            raise ValueError(f"duplicate node id: {node.node_id}")
        self._secondaries[node.node_id] = node

    def secondary_ids(self) -> list[str]:
        return list(self._secondaries)

    def set_delay(self, source: NodeRef, target: NodeRef, seconds: float) -> None:
        self._delays[(_id(source), _id(target))] = seconds
        log.info("delay %s -> %s set to %.2fs", _id(source), _id(target), seconds)

    def remove_delay(self, source: NodeRef, target: NodeRef) -> None:
        self._delays.pop((_id(source), _id(target)), None)
        log.info("delay %s -> %s removed", _id(source), _id(target))

    async def replicate(self, source_id: str, target_id: str, message: str) -> Ack:
        delay = self._delays.get((source_id, target_id), 0.0)
        if delay:
            await asyncio.sleep(delay)
        return await self._secondaries[target_id].receive(message)
