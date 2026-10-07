"""Iteration 1 harness tests: blocking, parallel replication.

Delays come from the spec (5 s, 6 s) multiplied by TIME_SCALE so the suite runs
fast by default. Run with TIME_SCALE=1 to use the spec's real timings.
"""
import asyncio
import os
import time

import pytest

from replicated_log import MasterNode, MockedTransport, SecondaryNode

TIME_SCALE = float(os.getenv("TIME_SCALE", "0.1"))
DELAY_S1 = 5 * TIME_SCALE
DELAY_S2 = 6 * TIME_SCALE
# Scheduling overhead allowed on top of the expected blocking time.
TOLERANCE = 0.15 + 0.05 * TIME_SCALE


async def timed(coro) -> float:
    start = time.perf_counter()
    await coro
    return time.perf_counter() - start


def assert_blocked_for(elapsed: float, expected: float) -> None:
    assert expected - 0.01 <= elapsed < expected + TOLERANCE, (
        f"expected to block ~{expected:.2f}s, took {elapsed:.2f}s"
    )


@pytest.fixture
def cluster():
    transport = MockedTransport()
    master = MasterNode(transport)
    s1 = SecondaryNode(transport)
    s2 = SecondaryNode(transport)
    return transport, master, s1, s2


async def test_spec_harness_scenario(cluster):
    """The scenario from the spec, step by step."""
    transport, master, s1, s2 = cluster

    transport.set_delay(master, s1, DELAY_S1)
    assert_blocked_for(await timed(master.append_msg("m1")), DELAY_S1)
    assert master.list_msgs() == ["m1"]

    # S1 still has its delay; S2 gets a longer one. Parallel replication means
    # the append blocks for the slowest link (6 s), not the sum (11 s).
    transport.set_delay(master, s2, DELAY_S2)
    assert_blocked_for(await timed(master.append_msg("m2")), DELAY_S2)
    assert master.list_msgs() == ["m1", "m2"]

    transport.remove_delay(master, s1)
    transport.remove_delay(master, s2)
    assert_blocked_for(await timed(master.append_msg("m3")), 0)

    assert master.list_msgs() == ["m1", "m2", "m3"]
    assert s1.list_msgs() == ["m1", "m2", "m3"]
    assert s2.list_msgs() == ["m1", "m2", "m3"]


async def test_append_waits_for_all_acks(cluster):
    """While a Secondary is still delayed, append has not returned and that
    Secondary does not have the message yet; once append returns, all do."""
    transport, master, s1, s2 = cluster
    transport.set_delay(master, s2, DELAY_S2)

    task = asyncio.create_task(master.append_msg("m1"))
    await asyncio.sleep(DELAY_S2 / 2)

    assert not task.done()
    assert s1.list_msgs() == ["m1"]
    assert s2.list_msgs() == []

    await task
    assert s2.list_msgs() == ["m1"]


async def test_secondary_side_delay_blocks_master():
    """Spec: 'introduce a delay/sleep on the Secondary' to show blocking."""
    transport = MockedTransport()
    master = MasterNode(transport)
    slow = SecondaryNode(transport, delay=DELAY_S1)
    fast = SecondaryNode(transport)

    assert_blocked_for(await timed(master.append_msg("m1")), DELAY_S1)
    assert slow.list_msgs() == fast.list_msgs() == ["m1"]


async def test_no_secondaries_appends_immediately():
    master = MasterNode(MockedTransport())
    assert_blocked_for(await timed(master.append_msg("m1")), 0)
    assert master.list_msgs() == ["m1"]
