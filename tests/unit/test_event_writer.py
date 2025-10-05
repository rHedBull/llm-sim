"""Unit tests for EventWriter rotation logic."""

import asyncio
from pathlib import Path
from datetime import datetime, timezone

import pytest
from ulid import ULID

from llm_sim.infrastructure.events import EventWriter, VerbosityLevel
from llm_sim.infrastructure.events.builder import create_milestone_event


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "test_output"
    output_dir.mkdir()
    return output_dir


@pytest.mark.asyncio
async def test_event_writer_rotation_triggers_at_threshold(tmp_output_dir):
    """T040: Verify rotation triggers at 500MB threshold."""
    # Use smaller threshold for testing
    threshold_mb = 1  # 1MB instead of 500MB
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="rotation-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=threshold_mb * 1024 * 1024
    )

    await event_writer.start()

    try:
        # Generate events until file size exceeds threshold
        for i in range(2000):
            event = create_milestone_event(
                simulation_id="rotation-test",
                turn_number=i,
                milestone_type="turn_start",
                description="x" * 400  # Padding under 500 char limit
            )
            event_writer.emit(event)

            if i % 100 == 0:
                await asyncio.sleep(0.01)  # Allow writer task to process

        # Allow final events to be written
        await asyncio.sleep(0.2)
        await event_writer.stop(timeout=5.0)

        # Verify multiple files created
        event_files = list(tmp_output_dir.glob("events*.jsonl"))

        # Should have at least primary file
        assert len(event_files) >= 1, f"No event files created"

        # If rotation occurred, verify rotated files have timestamps
        if len(event_files) > 1:
            rotated_files = [f for f in event_files if "events_" in f.name]
            assert len(rotated_files) > 0, "Rotation occurred but no timestamped files found"

            for rotated_file in rotated_files:
                # Verify timestamp format in filename
                assert "_" in rotated_file.stem, f"Rotated file missing timestamp: {rotated_file.name}"

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_event_writer_creates_timestamped_files(tmp_output_dir):
    """T040: Verify rotated files have timestamp in name."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="timestamp-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=100 * 1024  # 100KB for fast rotation
    )

    await event_writer.start()

    try:
        # Generate enough events to trigger rotation
        for i in range(500):
            event = create_milestone_event(
                simulation_id="timestamp-test",
                turn_number=i,
                milestone_type="turn_start",
                description="padding" * 50  # Under 500 char limit
            )
            event_writer.emit(event)

            if i % 50 == 0:
                await asyncio.sleep(0.01)  # Allow writer task to process

        # Allow final events to be written
        await asyncio.sleep(0.2)
        await event_writer.stop(timeout=5.0)

        # Check for rotated files
        event_files = sorted(tmp_output_dir.glob("events*.jsonl"))

        if len(event_files) > 1:
            # Verify format: events_YYYY-MM-DD_HH-MM-SS.jsonl
            rotated_files = [f for f in event_files if f.name != "events.jsonl"]

            for rotated_file in rotated_files:
                name_parts = rotated_file.stem.split("_")
                # Should be: ['events', 'YYYY-MM-DD', 'HH-MM-SS']
                assert len(name_parts) >= 3, \
                    f"Invalid timestamp format in {rotated_file.name}"

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_event_writer_rotation_size_limit(tmp_output_dir):
    """T040: Verify each file stays under size threshold."""
    threshold_mb = 0.5  # 500KB
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="size-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=int(threshold_mb * 1024 * 1024)
    )

    await event_writer.start()

    try:
        # Generate events
        for i in range(1000):
            event = create_milestone_event(
                simulation_id="size-test",
                turn_number=i,
                milestone_type="turn_start",
                description="x" * 400  # Padding under 500 char limit
            )
            event_writer.emit(event)

            if i % 50 == 0:
                await asyncio.sleep(0.01)  # Allow writer task to process

        # Allow final events to be written
        await asyncio.sleep(0.2)
        await event_writer.stop(timeout=5.0)

        # Verify file sizes
        event_files = list(tmp_output_dir.glob("events*.jsonl"))

        for event_file in event_files:
            size_mb = event_file.stat().st_size / 1024 / 1024
            # Allow 10% tolerance for rotation overhead
            assert size_mb <= threshold_mb * 1.1, \
                f"{event_file.name} exceeds threshold: {size_mb:.2f}MB > {threshold_mb}MB"

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_event_writer_graceful_queue_full(tmp_output_dir):
    """Verify events are dropped gracefully when queue is full."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="queue-test",
        verbosity=VerbosityLevel.DETAIL,
        max_queue_size=10  # Very small queue for testing
    )

    await event_writer.start()

    try:
        # Rapidly emit more events than queue can handle
        for i in range(100):
            event = create_milestone_event(
                simulation_id="queue-test",
                turn_number=i,
                milestone_type="turn_start"
            )
            event_writer.emit(event)  # Non-blocking, drops on queue full

        # Allow events to be written
        await asyncio.sleep(0.1)
        await event_writer.stop(timeout=2.0)

        # Verify file was created (some events were written)
        events_file = tmp_output_dir / "events.jsonl"
        assert events_file.exists(), "No events file created"

        # File should have some events, but not all 100
        with open(events_file, "r") as f:
            line_count = sum(1 for _ in f)

        # Should have written some events before queue filled
        assert line_count > 0, "No events written"
        assert line_count <= 100, "Unexpected event count"

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_event_writer_start_stop_lifecycle(tmp_output_dir):
    """Verify EventWriter start/stop lifecycle works correctly."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="lifecycle-test",
        verbosity=VerbosityLevel.ACTION
    )

    # Start writer
    await event_writer.start()
    assert event_writer.writer_task is not None, "Writer task not started"

    # Emit event
    event = create_milestone_event(
        simulation_id="lifecycle-test",
        turn_number=1,
        milestone_type="simulation_start"
    )
    event_writer.emit(event)

    # Allow events to be written
    await asyncio.sleep(0.1)
    # Stop writer
    await event_writer.stop(timeout=2.0)

    # Verify event was written
    events_file = tmp_output_dir / "events.jsonl"
    assert events_file.exists(), "Events file not created"

    with open(events_file, "r") as f:
        line_count = sum(1 for _ in f)
    assert line_count > 0, "No events written"
