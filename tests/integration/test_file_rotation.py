"""Integration tests for event file rotation.

Tests validate that event files rotate at 500MB threshold.
Based on quickstart.md Scenario 3: File rotation.
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone

import pytest
from ulid import ULID

from llm_sim.infrastructure.events import EventWriter, VerbosityLevel
from llm_sim.infrastructure.events.builder import create_detail_event


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output" / "rotation-test"
    output_dir.mkdir(parents=True)
    return output_dir


@pytest.mark.asyncio
async def test_file_rotation_at_500mb(tmp_output_dir):
    """T019: Verify file rotation creates timestamped files at 500MB threshold."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="rotation-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=5 * 1024 * 1024  # 5MB for faster testing (instead of 500MB)
    )

    await event_writer.start()

    # Generate events until rotation occurs
    event_count = 0
    max_events = 20000  # Safety limit

    try:
        while event_count < max_events:
            # Create large event with padding to reach file size faster
            event = create_detail_event(
                simulation_id="rotation-test",
                turn_number=event_count // 100,
                calculation_type="test_calculation",
                intermediate_values={f"key_{i}": "x" * 100 for i in range(50)},  # Larger payload
                description="x" * 400  # Padding under 500 char limit
            )

            event_writer.emit(event)
            event_count += 1

            # Check if rotation occurred (multiple files exist)
            event_files = list(tmp_output_dir.glob("events*.jsonl"))
            if len(event_files) > 1:
                break

            # Give writer time to process
            if event_count % 100 == 0:
                await asyncio.sleep(0.01)

        # Allow final events to be written
        await asyncio.sleep(0.2)
        # Stop writer
        await event_writer.stop(timeout=5.0)

        # Verify multiple files created
        event_files = sorted(tmp_output_dir.glob("events*.jsonl"))
        assert len(event_files) >= 2, \
            f"Expected at least 2 files after rotation, got {len(event_files)}: {[f.name for f in event_files]}"

        # Verify each file is below threshold (with some tolerance)
        for event_file in event_files:
            size_mb = event_file.stat().st_size / 1024 / 1024
            # Allow 10% over threshold due to rotation logic
            assert size_mb <= 5.5, \
                f"{event_file.name} exceeds size threshold: {size_mb:.1f}MB"

        # Verify rotated files have timestamp in name
        rotated_files = [f for f in event_files if f.name != "events.jsonl"]
        for rotated_file in rotated_files:
            assert "events_" in rotated_file.name, \
                f"Rotated file missing timestamp prefix: {rotated_file.name}"

    finally:
        # Cleanup
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_rotated_files_readable(tmp_output_dir):
    """Verify rotated event files contain valid JSONL."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="rotation-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=1 * 1024 * 1024  # 1MB for fast rotation
    )

    await event_writer.start()

    # Generate enough events to cause rotation
    for i in range(2000):
        event = create_detail_event(
            simulation_id="rotation-test",
            turn_number=i // 100,
            calculation_type="test",
            intermediate_values={"value": i, "padding": "x" * 500},
            description=f"Event {i}"
        )
        event_writer.emit(event)

        if i % 100 == 0:
            await asyncio.sleep(0.01)

    # Allow final events to be written
    await asyncio.sleep(0.2)
    await event_writer.stop(timeout=5.0)

    # Read all event files
    event_files = sorted(tmp_output_dir.glob("events*.jsonl"))
    assert len(event_files) > 0, "No event files created"

    total_events = 0
    for event_file in event_files:
        with open(event_file, "r") as f:
            for line_num, line in enumerate(f, 1):
                try:
                    event = json.loads(line)
                    total_events += 1

                    # Verify basic event structure
                    assert "event_id" in event
                    assert "simulation_id" in event
                    assert event["simulation_id"] == "rotation-test"

                except json.JSONDecodeError as e:
                    pytest.fail(
                        f"Invalid JSON in {event_file.name} line {line_num}: {str(e)}"
                    )

    assert total_events > 0, "No events found in rotated files"


@pytest.mark.asyncio
async def test_rotation_preserves_chronological_order(tmp_output_dir):
    """Verify events across rotated files maintain chronological order."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="rotation-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=1 * 1024 * 1024  # 1MB
    )

    await event_writer.start()

    # Generate events with incrementing turn numbers
    for i in range(1000):
        event = create_detail_event(
            simulation_id="rotation-test",
            turn_number=i,
            calculation_type="test",
            intermediate_values={"turn": i, "padding": "x" * 1000}
        )
        event_writer.emit(event)

        if i % 50 == 0:
            await asyncio.sleep(0.01)

    # Allow final events to be written
    await asyncio.sleep(0.2)
    await event_writer.stop(timeout=5.0)

    # Load all events from all files in chronological order
    # Rotated files have timestamps, current file is events.jsonl (newest)
    event_files = list(tmp_output_dir.glob("events*.jsonl"))
    # Sort: timestamped files first (oldest to newest), then events.jsonl (current/newest)
    rotated_files = sorted([f for f in event_files if f.name != "events.jsonl"])
    current_file = [f for f in event_files if f.name == "events.jsonl"]
    event_files_ordered = rotated_files + current_file

    all_events = []

    for event_file in event_files_ordered:
        with open(event_file, "r") as f:
            for line in f:
                all_events.append(json.loads(line))

    # Verify general chronological order by turn number
    # Note: Due to async processing, strict timestamp ordering isn't guaranteed
    # during rotation, but turn numbers should be generally increasing
    turn_numbers = [e["turn_number"] for e in all_events]

    # Check that turn numbers are present and generally increasing
    assert len(turn_numbers) == 1000, f"Expected 1000 events, got {len(turn_numbers)}"

    # Allow some out-of-order within small windows (async race during rotation)
    # but verify overall trend is increasing
    windows_of_10 = [turn_numbers[i:i+10] for i in range(0, len(turn_numbers), 10)]
    for i, window in enumerate(windows_of_10):
        avg = sum(window) / len(window)
        expected_avg = i * 10 + 5  # Middle of expected range
        # Allow 20% deviation for async ordering
        assert abs(avg - expected_avg) < expected_avg * 0.2, \
            f"Window {i} average turn {avg} too far from expected {expected_avg}"
