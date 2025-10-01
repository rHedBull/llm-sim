"""Generates unique run identifiers for simulations."""

from datetime import datetime
from pathlib import Path

from llm_sim.persistence.exceptions import RunIDCollisionError


class RunIDGenerator:
    """Generates unique run identifiers for simulations."""

    @staticmethod
    def generate(
        simulation_name: str,
        num_agents: int,
        start_time: datetime,
        output_root: Path = Path("output")
    ) -> str:
        """Generate unique run ID with collision detection.

        Args:
            simulation_name: Name from config
            num_agents: Number of agents
            start_time: Simulation start time
            output_root: Output directory for collision checking

        Returns:
            Unique run ID: {name}_{N}agents_{YYYYMMDD}_{HHMMSS}_{seq}

        Raises:
            RunIDCollisionError: If collision cannot be resolved
        """
        # Sanitize simulation name
        sanitized_name = simulation_name.replace("/", "_").replace(" ", "_")

        # Format date and time
        date_str = start_time.strftime("%Y%m%d")
        time_str = start_time.strftime("%H%M%S")

        # Base ID without sequence
        base_id = f"{sanitized_name}_{num_agents}agents_{date_str}_{time_str}"

        # Check for collisions and increment sequence
        for seq in range(1, 100):
            run_id = f"{base_id}_{seq:02d}"
            run_dir = output_root / run_id

            if not run_dir.exists():
                return run_id

        # If we get here, all 99 sequences are occupied
        raise RunIDCollisionError(
            f"Unable to generate unique run ID for {base_id}: "
            f"all sequences 01-99 are occupied"
        )
