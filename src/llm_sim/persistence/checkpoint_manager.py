"""Checkpoint management for simulation state."""

from pathlib import Path
from typing import Optional, Literal
from datetime import datetime

from llm_sim.models.state import SimulationState
from llm_sim.models.checkpoint import Checkpoint, SimulationResults
from llm_sim.persistence.storage import JSONStorage
from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError


class CheckpointManager:
    """Manages checkpoint saving and loading for simulations."""

    def __init__(
        self,
        run_id: str,
        checkpoint_interval: Optional[int] = None,
        output_root: Path = Path("output")
    ):
        """Initialize checkpoint manager.

        Args:
            run_id: Unique run identifier
            checkpoint_interval: Save checkpoint every N turns (None to disable)
            output_root: Root output directory
        """
        self.run_id = run_id
        self.checkpoint_interval = checkpoint_interval
        self.output_root = output_root
        self.run_dir = output_root / run_id
        self.checkpoint_dir = self.run_dir / "checkpoints"

        # Ensure checkpoint directory exists
        JSONStorage.ensure_directory(self.checkpoint_dir)

    def should_save_checkpoint(self, turn: int, is_final: bool) -> bool:
        """Determine if checkpoint should be saved at this turn.

        Args:
            turn: Current turn number
            is_final: Whether this is the final turn

        Returns:
            True if checkpoint should be saved
        """
        if is_final:
            return True

        if self.checkpoint_interval is None:
            return False

        return turn % self.checkpoint_interval == 0

    def save_checkpoint(
        self,
        state: SimulationState,
        checkpoint_type: Literal["interval", "last", "final"]
    ) -> Path:
        """Save checkpoint to disk.

        Args:
            state: Simulation state to save
            checkpoint_type: Type of checkpoint

        Returns:
            Path to saved checkpoint file

        Raises:
            CheckpointSaveError: On I/O failure
        """
        try:
            checkpoint = Checkpoint(
                turn=state.turn,
                checkpoint_type=checkpoint_type,
                state=state,
                timestamp=datetime.now()
            )

            # Determine filename
            if checkpoint_type == "last":
                filename = "last.json"
            else:
                filename = f"turn_{state.turn}.json"

            checkpoint_path = self.checkpoint_dir / filename

            # Save using atomic write
            JSONStorage.save_json(checkpoint_path, checkpoint)

            return checkpoint_path

        except Exception as e:
            raise CheckpointSaveError(
                f"Failed to save checkpoint at turn {state.turn}: {e}"
            ) from e

    def load_checkpoint(self, run_id: str, turn: int) -> SimulationState:
        """Load checkpoint from disk.

        Args:
            run_id: Run identifier
            turn: Turn number to load

        Returns:
            Simulation state from checkpoint

        Raises:
            CheckpointLoadError: On missing or corrupted file
        """
        checkpoint_path = self.output_root / run_id / "checkpoints" / f"turn_{turn}.json"

        try:
            checkpoint = JSONStorage.load_json(checkpoint_path, Checkpoint)
            return checkpoint.state
        except Exception as e:
            raise CheckpointLoadError(
                f"Failed to load checkpoint from {checkpoint_path}: {e}"
            ) from e

    def list_checkpoints(self, run_id: str) -> list[int]:
        """List available checkpoint turn numbers.

        Args:
            run_id: Run identifier

        Returns:
            Sorted list of checkpoint turn numbers
        """
        checkpoint_dir = self.output_root / run_id / "checkpoints"

        if not checkpoint_dir.exists():
            return []

        turns = []
        for checkpoint_file in checkpoint_dir.glob("turn_*.json"):
            # Extract turn number from filename
            turn_str = checkpoint_file.stem.replace("turn_", "")
            try:
                turns.append(int(turn_str))
            except ValueError:
                continue

        return sorted(turns)

    def save_results(self, results: SimulationResults) -> Path:
        """Save simulation results to disk.

        Args:
            results: Simulation results to save

        Returns:
            Path to saved results file

        Raises:
            CheckpointSaveError: On I/O failure
        """
        result_path = self.run_dir / "result.json"

        try:
            JSONStorage.save_json(result_path, results)
            return result_path
        except Exception as e:
            raise CheckpointSaveError(f"Failed to save results: {e}") from e
