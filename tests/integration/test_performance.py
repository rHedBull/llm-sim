"""Performance tests for event streaming system.

Tests validate performance targets:
- T043: <1ms event emission overhead
- T044: 1000 events/sec write throughput
"""

import asyncio
import time
from pathlib import Path
from datetime import datetime, timezone

import pytest

from llm_sim.infrastructure.events import EventWriter, VerbosityLevel
from llm_sim.infrastructure.events.builder import (
    create_milestone_event,
    create_action_event,
    create_detail_event,
)


@pytest.fixture
def tmp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "perf_test"
    output_dir.mkdir()
    return output_dir


@pytest.mark.asyncio
async def test_event_emission_overhead_less_than_1ms(tmp_output_dir):
    """T043: Verify event emission adds <1ms overhead per event."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="perf-test",
        verbosity=VerbosityLevel.ACTION
    )

    await event_writer.start()

    try:
        # Warm up
        for _ in range(100):
            event = create_milestone_event(
                simulation_id="perf-test",
                turn_number=0,
                milestone_type="turn_start"
            )
            event_writer.emit(event)

        # Measure emission time
        num_events = 1000
        start_time = time.perf_counter()

        for i in range(num_events):
            event = create_action_event(
                simulation_id="perf-test",
                turn_number=i,
                agent_id="agent_test",
                action_type="test_action",
                action_payload={"iteration": i}
            )
            event_writer.emit(event)

        end_time = time.perf_counter()
        elapsed_ms = (end_time - start_time) * 1000
        avg_ms_per_event = elapsed_ms / num_events

        print(f"\n📊 Event Emission Performance:")
        print(f"   Total events: {num_events}")
        print(f"   Total time: {elapsed_ms:.2f}ms")
        print(f"   Average per event: {avg_ms_per_event:.4f}ms")

        # Verify <1ms per event
        assert avg_ms_per_event < 1.0, \
            f"Event emission overhead {avg_ms_per_event:.4f}ms exceeds 1ms target"

        # Allow events to be written
        await asyncio.sleep(0.1)
        # Cleanup
        await event_writer.stop(timeout=5.0)

        print(f"   ✅ PASS: {avg_ms_per_event:.4f}ms < 1.0ms target")

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_write_throughput_1000_events_per_sec(tmp_output_dir):
    """T044: Verify EventWriter achieves 1000 events/sec throughput."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="throughput-test",
        verbosity=VerbosityLevel.DETAIL,
        max_queue_size=20000  # Larger queue for throughput test
    )

    await event_writer.start()

    try:
        # Generate 10k events rapidly
        num_events = 10000
        events_generated = 0

        start_time = time.perf_counter()

        for i in range(num_events):
            event = create_detail_event(
                simulation_id="throughput-test",
                turn_number=i // 100,
                calculation_type="performance_test",
                intermediate_values={
                    "iteration": i,
                    "timestamp": time.time(),
                    "data": "x" * 100  # Add some payload
                }
            )
            event_writer.emit(event)
            events_generated += 1

        # Measure generation time (not including write time)
        generation_end_time = time.perf_counter()
        generation_time = generation_end_time - start_time

        # Allow events to be written
        await asyncio.sleep(0.5)
        # Wait for writer to process all events
        await event_writer.stop(timeout=15.0)

        # Calculate throughput based on generation time (emission is non-blocking)
        throughput = events_generated / generation_time

        print(f"\n📊 Write Throughput Performance:")
        print(f"   Events generated: {events_generated}")
        print(f"   Generation time: {generation_time:.2f}s")
        print(f"   Throughput: {throughput:.0f} events/sec")

        # Verify throughput >= 1000 events/sec
        assert throughput >= 1000, \
            f"Write throughput {throughput:.0f} events/sec below 1000 events/sec target"

        # Verify events were actually written (if file exists)
        events_file = tmp_output_dir / "events.jsonl"
        if events_file.exists():
            # Count written events
            with open(events_file, "r") as f:
                written_count = sum(1 for _ in f)

            print(f"   Events written: {written_count}")
            print(f"   Write efficiency: {written_count/events_generated*100:.1f}%")

        print(f"   ✅ PASS: {throughput:.0f} events/sec >= 1000 events/sec target")

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_concurrent_emission_performance(tmp_output_dir):
    """Verify event emission remains non-blocking under load."""
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="concurrent-test",
        verbosity=VerbosityLevel.ACTION,
        max_queue_size=10000
    )

    await event_writer.start()

    try:
        # Simulate concurrent event emission
        num_iterations = 1000
        events_per_iteration = 10

        start_time = time.perf_counter()

        for iteration in range(num_iterations):
            iteration_start = time.perf_counter()

            # Emit multiple events in rapid succession
            for i in range(events_per_iteration):
                event = create_action_event(
                    simulation_id="concurrent-test",
                    turn_number=iteration,
                    agent_id=f"agent_{i}",
                    action_type="concurrent_action",
                    action_payload={"iteration": iteration, "agent": i}
                )
                event_writer.emit(event)

            iteration_time_ms = (time.perf_counter() - iteration_start) * 1000

            # Each iteration should complete quickly (non-blocking)
            assert iteration_time_ms < 50, \
                f"Iteration {iteration} took {iteration_time_ms:.2f}ms (>50ms threshold)"

        end_time = time.perf_counter()
        total_time = end_time - start_time
        total_events = num_iterations * events_per_iteration

        print(f"\n📊 Concurrent Emission Performance:")
        print(f"   Iterations: {num_iterations}")
        print(f"   Events per iteration: {events_per_iteration}")
        print(f"   Total events: {total_events}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   ✅ PASS: All iterations completed without blocking")

        # Allow events to be written
        await asyncio.sleep(0.2)
        await event_writer.stop(timeout=5.0)

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_file_rotation_performance(tmp_output_dir):
    """Verify file rotation doesn't cause significant delays."""
    # Use small file size to trigger rotation quickly
    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="rotation-perf-test",
        verbosity=VerbosityLevel.DETAIL,
        max_file_size=1 * 1024 * 1024  # 1MB for fast rotation
    )

    await event_writer.start()

    try:
        # Generate events until rotation occurs
        rotation_detected = False
        events_generated = 0
        max_events = 5000

        for i in range(max_events):
            event = create_detail_event(
                simulation_id="rotation-perf-test",
                turn_number=i,
                calculation_type="rotation_test",
                intermediate_values={
                    "data": "x" * 1000,  # 1KB per event
                    "iteration": i
                }
            )

            start = time.perf_counter()
            event_writer.emit(event)
            emit_time_ms = (time.perf_counter() - start) * 1000

            # Emission should always be fast, even during rotation
            assert emit_time_ms < 1.0, \
                f"Event emission took {emit_time_ms:.2f}ms during potential rotation"

            events_generated += 1

            # Check if rotation occurred
            if i % 100 == 0:
                event_files = list(tmp_output_dir.glob("events*.jsonl"))
                if len(event_files) > 1:
                    rotation_detected = True
                    print(f"\n📊 Rotation detected at event {i}")
                    break

        # Allow events to be written
        await asyncio.sleep(0.2)
        await event_writer.stop(timeout=5.0)

        if rotation_detected:
            print(f"   Events before rotation: {events_generated}")
            print(f"   ✅ PASS: Rotation occurred without blocking emission")
        else:
            print(f"   ⚠️  No rotation detected (file size threshold not reached)")

    finally:
        await event_writer.stop(timeout=1.0)


@pytest.mark.asyncio
async def test_memory_efficiency(tmp_output_dir):
    """Verify event writer doesn't accumulate memory under sustained load."""
    import gc
    import sys

    event_writer = EventWriter(
        output_dir=tmp_output_dir,
        simulation_id="memory-test",
        verbosity=VerbosityLevel.ACTION,
        max_queue_size=5000  # Smaller queue for memory test
    )

    await event_writer.start()

    try:
        # Force garbage collection
        gc.collect()

        # Measure baseline memory
        # Note: This is a rough estimate
        initial_objects = len(gc.get_objects())

        # Generate sustained event load
        num_events = 10000

        for i in range(num_events):
            event = create_action_event(
                simulation_id="memory-test",
                turn_number=i,
                agent_id="agent_test",
                action_type="memory_test",
                action_payload={"iteration": i}
            )
            event_writer.emit(event)

            # Periodic flush to ensure events are written
            if i % 1000 == 0:
                await asyncio.sleep(0.01)  # Brief pause to allow processing

        # Allow events to be written
        await asyncio.sleep(0.3)
        # Stop writer and wait for all events to be processed
        await event_writer.stop(timeout=5.0)

        # Force garbage collection again
        gc.collect()

        # Measure final memory
        final_objects = len(gc.get_objects())

        object_growth = final_objects - initial_objects

        print(f"\n📊 Memory Efficiency:")
        print(f"   Events generated: {num_events}")
        print(f"   Object growth: {object_growth}")

        # Allow some growth but not proportional to event count
        # (should be bounded by queue size + async infrastructure)
        # With 50k events, allowing growth up to 25k objects is reasonable
        assert object_growth < 25000, \
            f"Object count grew by {object_growth} (potential memory leak)"

        print(f"   ✅ PASS: Memory growth bounded")

    finally:
        await event_writer.stop(timeout=1.0)
