"""Checkpoint management for simulation state."""

from pathlib import Path
from typing import Optional, Literal, Dict
from datetime import datetime

from llm_sim.models.state import SimulationState
from llm_sim.models.checkpoint import Checkpoint, CheckpointFile, CheckpointMetadata, SimulationResults
from llm_sim.models.config import VariableDefinition
from llm_sim.persistence.storage import JSONStorage
from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError, SchemaCompatibilityError
from llm_sim.persistence.schema_hash import compute_schema_hash


class CheckpointManager:
    """Manages checkpoint saving and loading for simulations."""

    def __init__(
        self,
        run_id: str,
        agent_var_defs: Dict[str, VariableDefinition],
        global_var_defs: Dict[str, VariableDefinition],
        checkpoint_interval: Optional[int] = None,
        output_root: Path = Path("output"),
    ):
        """Initialize checkpoint manager.

        Args:
            run_id: Unique run identifier
            agent_var_defs: Agent variable definitions (for schema hash)
            global_var_defs: Global variable definitions (for schema hash)
            checkpoint_interval: Save checkpoint every N turns (None to disable)
            output_root: Root output directory
        """
        self.run_id = run_id
        self.checkpoint_interval = checkpoint_interval
        self.output_root = output_root
        self.run_dir = output_root / run_id
        self.checkpoint_dir = self.run_dir / "checkpoints"

        # Compute and store schema hash for this run
        self.schema_hash = compute_schema_hash(agent_var_defs, global_var_defs)

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
        checkpoint_type: Literal["interval", "last", "final"] = "interval",
    ) -> Path:
        """Save checkpoint to disk with schema hash.

        Args:
            state: Simulation state to save
            checkpoint_type: Type of checkpoint (for backwards compatibility)

        Returns:
            Path to saved checkpoint file

        Raises:
            CheckpointSaveError: On I/O failure
        """
        try:
            # Create metadata with schema_hash
            metadata = CheckpointMetadata(
                run_id=self.run_id,
                turn=state.turn,
                timestamp=datetime.now().isoformat(),
                schema_hash=self.schema_hash,
            )

            # Create checkpoint file with new format
            checkpoint_file = CheckpointFile(metadata=metadata, state=state)

            # Determine filename
            if checkpoint_type == "last":
                filename = "last.json"
            else:
                filename = f"turn_{state.turn}.json"

            checkpoint_path = self.checkpoint_dir / filename

            # Save using atomic write
            JSONStorage.save_json(checkpoint_path, checkpoint_file)

            return checkpoint_path

        except Exception as e:
            raise CheckpointSaveError(
                f"Failed to save checkpoint at turn {state.turn}: {e}"
            ) from e

    def load_checkpoint(
        self,
        run_id: str,
        turn: int,
        validate_schema: bool = True,
    ) -> SimulationState:
        """Load checkpoint from disk with schema validation.

        Args:
            run_id: Run identifier
            turn: Turn number to load
            validate_schema: Whether to validate schema_hash matches (default: True)

        Returns:
            Simulation state from checkpoint

        Raises:
            CheckpointLoadError: On missing or corrupted file
            SchemaCompatibilityError: If schema_hash doesn't match
        """
        checkpoint_path = self.output_root / run_id / "checkpoints" / f"turn_{turn}.json"

        try:
            # Try to load new format first
            checkpoint_file = JSONStorage.load_json(checkpoint_path, CheckpointFile)

            # Validate schema hash if requested
            if validate_schema and checkpoint_file.metadata.schema_hash != self.schema_hash:
                raise SchemaCompatibilityError(
                    f"Schema mismatch: checkpoint has {checkpoint_file.metadata.schema_hash}, "
                    f"current config has {self.schema_hash}. "
                    "Variable definitions have changed between checkpoint save and load."
                )

            return checkpoint_file.state

        except SchemaCompatibilityError:
            raise  # Re-raise schema errors as-is
        except Exception as e:
            # Try legacy format as fallback
            try:
                checkpoint = JSONStorage.load_json(checkpoint_path, Checkpoint)
                return checkpoint.state
            except Exception:
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
