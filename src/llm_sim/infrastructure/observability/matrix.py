"""Efficient O(1) lookup for observability relationships."""

from typing import Dict, List, Tuple

from llm_sim.infrastructure.observability.config import (
    DefaultObservability,
    ObservabilityEntry,
    ObservabilityLevel,
)


class ObservabilityMatrix:
    """Efficient O(1) lookup for observability relationships.

    Converts a list of observability entries into a dictionary for fast lookup.
    Returns default observability for observer-target pairs not in the matrix.
    """

    def __init__(
        self, entries: List[ObservabilityEntry], default: DefaultObservability | None
    ):
        """Initialize the observability matrix.

        Args:
            entries: List of observability entries defining observer-target relationships
            default: Default observability for pairs not in the matrix (if None, uses UNAWARE/0.0)
        """
        # Build dict mapping (observer, target) -> (level, noise)
        self._matrix: Dict[Tuple[str, str], Tuple[ObservabilityLevel, float]] = {}
        for entry in entries:
            # Store level and noise, using 0.0 for noise if None
            noise = entry.noise if entry.noise is not None else 0.0
            self._matrix[(entry.observer, entry.target)] = (entry.level, noise)

        # Use provided default or fallback to UNAWARE with no noise
        if default is not None:
            self._default = (default.level, default.noise)
        else:
            self._default = (ObservabilityLevel.UNAWARE, 0.0)

    def get_observability(
        self, observer: str, target: str
    ) -> Tuple[ObservabilityLevel, float]:
        """Get observability level and noise for an observer-target pair.

        Args:
            observer: ID of the observing agent
            target: ID of the target agent or "global" for global state

        Returns:
            Tuple of (ObservabilityLevel, noise_factor)
            Returns default if pair not found in matrix
        """
        # Return from dict or default if not found
        return self._matrix.get((observer, target), self._default)
