"""Unit tests for EventWriter synchronous mode."""

import tempfile
from pathlib import Path

import pytest

from llm_sim.infrastructure.events.writer import EventWriter, WriteMode
from llm_sim.infrastructure.events.config import VerbosityLevel
from llm_sim.models.event import Event


def test_sync_mode_writes_immediately():
    """Test that sync mode writes events immediately to disk.

    CONTRACT: Sync mode must write and fsync before emit() returns.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_sync",
            verbosity=VerbosityLevel.DETAIL,  # SYSTEM events only logged at DETAIL
            mode=WriteMode.SYNC,
        )

        # Emit event
        event = Event(
            turn_number=0,
            event_type="SYSTEM",
            simulation_id="test_sync",
            description="test event",
            details={"test": "data"},
        )
        writer.emit(event)

        # Check file exists immediately
        event_file = Path(tmpdir) / "events.jsonl"
        assert event_file.exists(), "Event file must exist immediately after emit()"

        # Check content
        content = event_file.read_text()
        assert "SYSTEM" in content
        assert "test_sync" in content


def test_sync_mode_file_rotation():
    """Test that sync mode rotates files at size threshold.

    CONTRACT: Files must rotate when size exceeds max_file_size.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Small file size for testing
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_rotation",
            verbosity=VerbosityLevel.DETAIL,  # SYSTEM events only logged at DETAIL
            mode=WriteMode.SYNC,
            max_file_size=1000,  # 1KB for testing
        )

        # Write events until rotation
        large_data = "x" * 500  # 500 bytes per event
        for i in range(5):  # 2500 bytes total
            event = Event(
                turn_number=i,
                event_type="SYSTEM",
                simulation_id="test_rotation",
                description="large event",
                details={"index": i, "payload": large_data},
            )
            writer.emit(event)

        # Check that rotation occurred
        files = list(Path(tmpdir).glob("events*.jsonl"))
        assert len(files) >= 2, "Expected at least 2 files (current + rotated)"

        # Verify current file exists
        assert (Path(tmpdir) / "events.jsonl").exists()

        # Verify rotated file has timestamp
        rotated = [f for f in files if "events_" in f.name and f.name != "events.jsonl"]
        assert len(rotated) > 0, "Expected rotated file with timestamp"


def test_sync_mode_no_async_dependency():
    """Test that sync mode works without async event loop.

    CONTRACT: Sync mode must work in pure synchronous contexts.
    """
    # This test runs in pure sync context (no asyncio)
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test_no_async",
            verbosity=VerbosityLevel.DETAIL,  # SYSTEM events only logged at DETAIL
            mode=WriteMode.SYNC,
        )

        # Should work fine without event loop
        for i in range(10):
            event = Event(
                turn_number=i,
                event_type="SYSTEM",
                simulation_id="test_no_async",
                description="sync event",
                details={"count": i},
            )
            writer.emit(event)

        # Verify all events written
        content = (Path(tmpdir) / "events.jsonl").read_text()
        assert content.count("SYSTEM") == 10


def test_mode_selection():
    """Test that writer respects mode parameter.

    CONTRACT: Mode must be settable and respected at initialization.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sync_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test",
            mode=WriteMode.SYNC,
        )
        assert sync_writer.mode == WriteMode.SYNC

        async_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test2",
            mode=WriteMode.ASYNC,
        )
        assert async_writer.mode == WriteMode.ASYNC

        # Test default is ASYNC (backward compatibility)
        default_writer = EventWriter(
            output_dir=Path(tmpdir),
            simulation_id="test3",
        )
        assert default_writer.mode == WriteMode.ASYNC
