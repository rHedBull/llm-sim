"""Contract: EventWriter Public API

This contract defines the expected behavior of EventWriter across both async and sync modes.
Tests validating this contract must pass for both modes.

Contract Version: 1.0.0
Feature: 013-event-writer-fix
"""

from enum import Enum
from pathlib import Path
from typing import Protocol, runtime_checkable

from llm_sim.infrastructure.events.config import VerbosityLevel
from llm_sim.models.event import Event


class WriteMode(str, Enum):
    """Event writer operation modes.

    CONTRACT: WriteMode must have exactly two values representing async and sync modes.
    """
    ASYNC = "async"
    SYNC = "sync"


@runtime_checkable
class EventWriterProtocol(Protocol):
    """Contract for EventWriter implementations.

    This protocol defines the public interface that all EventWriter implementations
    must satisfy, regardless of their operational mode.
    """

    # Required attributes
    output_dir: Path
    simulation_id: str
    verbosity: VerbosityLevel
    mode: WriteMode
    current_file: Path
    current_size: int

    def __init__(
        self,
        output_dir: Path,
        simulation_id: str,
        verbosity: VerbosityLevel = VerbosityLevel.ACTION,
        max_queue_size: int = 10000,
        max_file_size: int = 500 * 1024 * 1024,
        mode: WriteMode = WriteMode.ASYNC,
    ) -> None:
        """Initialize event writer.

        CONTRACT REQUIREMENTS:
        - MUST accept all parameters shown
        - MUST default mode to ASYNC (backward compatibility)
        - MUST create output_dir if it doesn't exist
        - MUST set current_file to output_dir/events.jsonl
        - MUST initialize current_size to 0
        - MUST NOT start writing until start() is called (async mode)
        - MUST be ready to write immediately after init (sync mode)

        Args:
            output_dir: Directory for event files
            simulation_id: Simulation run identifier
            verbosity: Event filtering level
            max_queue_size: Queue size limit (async mode only, ignored in sync)
            max_file_size: File size threshold for rotation (default 500MB)
            mode: Write mode (async or sync)
        """
        ...

    async def start(self) -> None:
        """Start the event writer.

        CONTRACT REQUIREMENTS:
        - Async mode: MUST start background writer task
        - Sync mode: MUST be a no-op (immediate log and return)
        - MUST be idempotent (safe to call multiple times)
        - MUST NOT raise exceptions
        """
        ...

    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the event writer and flush pending events.

        CONTRACT REQUIREMENTS:
        - Async mode: MUST wait for queue drain (up to timeout)
        - Async mode: MUST cancel background task
        - Sync mode: MUST be a no-op (all events already flushed)
        - MUST NOT raise exceptions
        - MUST log dropped events count (async mode)

        Args:
            timeout: Maximum seconds to wait for queue drain (async only)
        """
        ...

    def emit(self, event: Event) -> None:
        """Emit an event for writing.

        CONTRACT REQUIREMENTS:
        - MUST filter events based on verbosity level
        - MUST NOT emit events below verbosity threshold
        - Async mode: MUST enqueue event without blocking
        - Async mode: MUST drop events if queue is full (no exceptions)
        - Sync mode: MUST write event immediately to disk
        - Sync mode: MUST flush OS buffers (fsync) before returning
        - Sync mode: MUST rotate file if size threshold exceeded
        - MUST handle write errors gracefully (log, don't raise)
        - MUST serialize events as JSONL (one JSON object per line)

        Args:
            event: Event to write
        """
        ...


# Contract validation tests
# These tests MUST pass for any EventWriter implementation


def test_contract_mode_selection():
    """CONTRACT: Mode must be settable and respected.

    GIVEN an EventWriter initialized with a specific mode
    WHEN the mode attribute is checked
    THEN it must match the initialization parameter
    """
    # Test in actual test file
    pass


def test_contract_emit_interface():
    """CONTRACT: emit() must accept Event and return None.

    GIVEN an EventWriter (any mode)
    WHEN emit(event) is called with a valid Event
    THEN it must complete without raising exceptions
    AND it must return None
    """
    pass


def test_contract_verbosity_filtering():
    """CONTRACT: Events must be filtered by verbosity level.

    GIVEN an EventWriter with verbosity=MINIMAL
    WHEN emit() is called with a low-priority event
    THEN the event must NOT be written to disk

    GIVEN an EventWriter with verbosity=FULL
    WHEN emit() is called with any event
    THEN the event MUST be written to disk
    """
    pass


def test_contract_sync_mode_immediate_write():
    """CONTRACT: Sync mode must write immediately.

    GIVEN an EventWriter in SYNC mode
    WHEN emit(event) is called
    THEN the event MUST be visible on disk before emit() returns
    AND the file MUST be fsynced (durable)
    """
    pass


def test_contract_async_mode_queued_write():
    """CONTRACT: Async mode must queue and write asynchronously.

    GIVEN an EventWriter in ASYNC mode that has been started
    WHEN emit(event) is called
    THEN emit() MUST return immediately (non-blocking)
    AND the event MUST eventually be written to disk
    """
    pass


def test_contract_file_rotation():
    """CONTRACT: Files must rotate at size threshold.

    GIVEN an EventWriter with max_file_size=1000 bytes
    WHEN enough events are emitted to exceed 1000 bytes
    THEN the current file MUST be renamed with timestamp
    AND a new events.jsonl MUST be created
    AND current_size MUST be reset to 0
    """
    pass


def test_contract_rotation_timestamp_uniqueness():
    """CONTRACT: Rotated files must have unique names.

    GIVEN multiple file rotations in quick succession
    WHEN rotation occurs
    THEN each rotated file MUST have a unique timestamped name
    (Timestamp format includes microseconds to prevent collisions)
    """
    pass


def test_contract_output_directory_creation():
    """CONTRACT: output_dir must be created if missing.

    GIVEN a non-existent output directory path
    WHEN EventWriter is initialized
    THEN the directory MUST be created
    AND no exceptions MUST be raised
    """
    pass


def test_contract_error_graceful_degradation():
    """CONTRACT: Write errors must not crash the writer.

    GIVEN a write operation that fails (e.g., disk full, permissions)
    WHEN the error occurs
    THEN the writer MUST log the error
    AND the writer MUST continue operating (no exception raised)
    AND subsequent events MAY still be written if error is transient
    """
    pass


def test_contract_serialization_format():
    """CONTRACT: Events must serialize as JSONL.

    GIVEN an event with various data types
    WHEN the event is written to disk
    THEN the file MUST contain valid JSONL format
    (One JSON object per line, newline-terminated, UTF-8 encoded)
    """
    pass


def test_contract_start_stop_idempotency():
    """CONTRACT: start() and stop() must be idempotent.

    GIVEN an EventWriter (async mode)
    WHEN start() is called multiple times
    THEN no duplicate tasks MUST be created

    GIVEN an EventWriter that is stopped
    WHEN stop() is called again
    THEN no exceptions MUST be raised
    """
    pass


def test_contract_sync_mode_no_async_dependency():
    """CONTRACT: Sync mode must work without event loop.

    GIVEN an EventWriter in SYNC mode
    WHEN used in a pure synchronous context (no asyncio event loop)
    THEN all operations MUST work correctly
    (No "no running event loop" errors)
    """
    pass


# Performance contracts (non-functional requirements)


def test_contract_sync_mode_performance():
    """CONTRACT: Sync mode must meet latency requirements.

    GIVEN an EventWriter in SYNC mode
    WHEN a single event is emitted
    THEN write latency MUST be < 10ms on SSD
    (This ensures simulation is not significantly slowed)
    """
    pass


def test_contract_async_mode_throughput():
    """CONTRACT: Async mode must meet throughput requirements.

    GIVEN an EventWriter in ASYNC mode
    WHEN events are emitted rapidly
    THEN the writer MUST handle at least 1000 events/sec
    (Queue must drain faster than typical event generation rate)
    """
    pass


# Integration contracts


def test_contract_orchestrator_integration():
    """CONTRACT: EventWriter must integrate with Orchestrator.

    GIVEN an Orchestrator using EventWriter in SYNC mode
    WHEN a simulation runs to completion
    THEN events.jsonl MUST exist
    AND events.jsonl MUST contain all expected event types
    (simulation_starting, turn_started, turn_completed, etc.)
    """
    pass


# Backward compatibility contracts


def test_contract_backward_compatibility():
    """CONTRACT: Existing code must work without changes.

    GIVEN EventWriter initialized without mode parameter
    WHEN the writer is used
    THEN it MUST operate in ASYNC mode (default)
    AND all existing tests MUST pass
    """
    pass


# Documentation contracts


def test_contract_mode_documented():
    """CONTRACT: Mode behavior must be documented.

    GIVEN the EventWriter class
    WHEN inspecting docstrings
    THEN the mode parameter MUST be documented
    AND the difference between ASYNC and SYNC MUST be clear
    """
    pass
