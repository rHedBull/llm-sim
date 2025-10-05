"""Async event writer with file rotation and graceful degradation."""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from structlog import get_logger

from llm_sim.infrastructure.events.config import VerbosityLevel, should_log_event
from llm_sim.models.event import Event

logger = get_logger(__name__)

# File rotation threshold (500MB)
ROTATION_SIZE_BYTES = 500 * 1024 * 1024


class EventWriter:
    """Async event writer with queue-based buffering and file rotation.

    Events are queued and written asynchronously to avoid blocking
    simulation execution. When the queue is full, events are dropped
    with a warning to prioritize simulation speed over observability.
    """

    def __init__(
        self,
        output_dir: Path,
        simulation_id: str,
        verbosity: VerbosityLevel = VerbosityLevel.ACTION,
        max_queue_size: int = 10000,
        max_file_size: int = ROTATION_SIZE_BYTES,
    ) -> None:
        """Initialize event writer.

        Args:
            output_dir: Directory for event files
            simulation_id: Simulation run identifier
            verbosity: Event verbosity level
            max_queue_size: Maximum events to queue before dropping
            max_file_size: Maximum file size before rotation (default 500MB)
        """
        self.output_dir = Path(output_dir)
        self.simulation_id = simulation_id
        self.verbosity = verbosity
        self.max_queue_size = max_queue_size
        self.max_file_size = max_file_size

        self.queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=max_queue_size)
        self.writer_task: Optional[asyncio.Task] = None
        self.running = False
        self.dropped_count = 0

        # Current event file
        self.current_file = self.output_dir / "events.jsonl"
        self.current_size = 0

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def start(self) -> None:
        """Start the background writer task."""
        if self.running:
            return

        self.running = True
        self.writer_task = asyncio.create_task(self._write_loop())
        logger.info(
            "event_writer_started",
            output_dir=str(self.output_dir),
            verbosity=self.verbosity.value,
        )

    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the writer and flush pending events.

        Args:
            timeout: Maximum seconds to wait for queue drain
        """
        if not self.running:
            return

        self.running = False

        # Wait for queue to drain with timeout
        try:
            await asyncio.wait_for(self.queue.join(), timeout=timeout)
        except asyncio.TimeoutError:
            remaining = self.queue.qsize()
            logger.warning(
                "event_writer_timeout",
                remaining_events=remaining,
                timeout_seconds=timeout,
            )

        # Cancel writer task
        if self.writer_task:
            self.writer_task.cancel()
            try:
                await self.writer_task
            except asyncio.CancelledError:
                pass

        logger.info(
            "event_writer_stopped",
            total_dropped=self.dropped_count,
        )

    def emit(self, event: Event) -> None:
        """Emit an event (non-blocking).

        Args:
            event: Event to emit
        """
        # Check verbosity filter
        if not should_log_event(event.event_type, self.verbosity):
            return

        # Try to enqueue without blocking
        try:
            self.queue.put_nowait(event)
        except asyncio.QueueFull:
            self.dropped_count += 1
            if self.dropped_count % 100 == 0:  # Log every 100 drops
                logger.warning(
                    "event_queue_full_dropping",
                    event_id=event.event_id,
                    total_dropped=self.dropped_count,
                )

    async def _write_loop(self) -> None:
        """Background loop that drains queue and writes events."""
        while self.running:
            try:
                # Get event from queue
                event = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Write event to file
                await self._write_event(event)

                # Mark task done
                self.queue.task_done()

            except asyncio.TimeoutError:
                # No events available, continue
                continue
            except Exception as e:
                logger.error("event_write_error", error=str(e), exc_info=True)

    async def _write_event(self, event: Event) -> None:
        """Write a single event to JSONL file with rotation check.

        Args:
            event: Event to write
        """
        # Check if rotation needed
        if self.current_size >= self.max_file_size:
            await self._rotate_file()

        # Serialize event
        event_json = event.model_dump_json()
        event_line = event_json + "\n"
        event_bytes = event_line.encode("utf-8")

        # Atomic write
        try:
            async with aiofiles.open(self.current_file, mode="a") as f:
                await f.write(event_line)
                await f.flush()

            # Update size
            self.current_size += len(event_bytes)

        except IOError as e:
            logger.error(
                "event_file_write_failed",
                file=str(self.current_file),
                event_id=event.event_id,
                error=str(e),
            )

    async def _rotate_file(self) -> None:
        """Rotate the current event file when size threshold exceeded."""
        # Generate timestamped filename with microseconds to avoid collisions
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S-%f")
        rotated_file = self.output_dir / f"events_{timestamp}.jsonl"

        # Rename current file
        if self.current_file.exists():
            try:
                os.rename(self.current_file, rotated_file)
                logger.info(
                    "event_file_rotated",
                    old_file=str(self.current_file),
                    new_file=str(rotated_file),
                    size_mb=self.current_size / (1024 * 1024),
                )
            except OSError as e:
                logger.error("event_file_rotation_failed", error=str(e))

        # Reset size counter
        self.current_size = 0
