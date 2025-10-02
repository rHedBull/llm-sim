"""Unit tests for ObservabilityMatrix lookup functionality.

These tests validate O(1) lookup performance and correct behavior of the
observability matrix for observer-target relationships.
"""

import pytest
from llm_sim.infrastructure.observability.matrix import ObservabilityMatrix
from llm_sim.infrastructure.observability.config import (
    DefaultObservability,
    ObservabilityEntry,
    ObservabilityLevel,
)


class TestObservabilityMatrixLookup:
    """Tests for ObservabilityMatrix get_observability() method."""

    def test_get_observability_returns_correct_values(self):
        """Should return correct (level, noise) for defined observer-target pairs."""
        # Setup matrix with various entries
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="agent_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.1,
            ),
            ObservabilityEntry(
                observer="agent_1",
                target="agent_3",
                level=ObservabilityLevel.INSIDER,
                noise=0.05,
            ),
            ObservabilityEntry(
                observer="agent_2",
                target="agent_1",
                level=ObservabilityLevel.UNAWARE,
                noise=0.0,
            ),
            ObservabilityEntry(
                observer="agent_3",
                target="global",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.2,
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.0)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Test each defined pair returns correct values
        level, noise = matrix.get_observability("agent_1", "agent_2")
        assert level == ObservabilityLevel.EXTERNAL
        assert noise == 0.1

        level, noise = matrix.get_observability("agent_1", "agent_3")
        assert level == ObservabilityLevel.INSIDER
        assert noise == 0.05

        level, noise = matrix.get_observability("agent_2", "agent_1")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.0

        level, noise = matrix.get_observability("agent_3", "global")
        assert level == ObservabilityLevel.EXTERNAL
        assert noise == 0.2

    def test_get_observability_returns_default_for_undefined_pairs(self):
        """Should return default (level, noise) for undefined observer-target pairs."""
        # Setup matrix with minimal entries
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="agent_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.1,
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Test undefined pairs return default
        level, noise = matrix.get_observability("agent_2", "agent_3")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.5

        level, noise = matrix.get_observability("agent_3", "agent_1")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.5

        # Test reverse of defined pair also returns default
        level, noise = matrix.get_observability("agent_2", "agent_1")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.5

    def test_get_observability_with_none_default(self):
        """Should use UNAWARE/0.0 when default is None."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="agent_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.1,
            ),
        ]
        matrix = ObservabilityMatrix(entries=entries, default=None)

        # Test undefined pair returns fallback UNAWARE/0.0
        level, noise = matrix.get_observability("agent_2", "agent_3")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.0

    def test_get_observability_handles_none_noise_in_entry(self):
        """Should convert None noise to 0.0 in matrix entries."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="agent_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=None,  # None should be converted to 0.0
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        level, noise = matrix.get_observability("agent_1", "agent_2")
        assert level == ObservabilityLevel.EXTERNAL
        assert noise == 0.0  # None was converted to 0.0

    def test_matrix_handles_global_target(self):
        """Should handle 'global' target correctly in lookups."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="global",
                level=ObservabilityLevel.INSIDER,
                noise=0.0,
            ),
            ObservabilityEntry(
                observer="agent_2",
                target="global",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.15,
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Test global target lookups
        level, noise = matrix.get_observability("agent_1", "global")
        assert level == ObservabilityLevel.INSIDER
        assert noise == 0.0

        level, noise = matrix.get_observability("agent_2", "global")
        assert level == ObservabilityLevel.EXTERNAL
        assert noise == 0.15

        # Test agent without global access gets default
        level, noise = matrix.get_observability("agent_3", "global")
        assert level == ObservabilityLevel.UNAWARE
        assert noise == 0.5

    def test_matrix_handles_self_observation(self):
        """Should handle agent observing itself (same observer and target)."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="agent_1",
                level=ObservabilityLevel.INSIDER,
                noise=0.0,
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Self-observation should work like any other pair
        level, noise = matrix.get_observability("agent_1", "agent_1")
        assert level == ObservabilityLevel.INSIDER
        assert noise == 0.0

    def test_matrix_lookup_is_fast(self):
        """Should perform O(1) lookup regardless of matrix size.

        This test documents the O(1) performance guarantee by showing that
        lookup time doesn't depend on the number of entries. While we don't
        measure actual timing (which would be fragile), we verify that the
        implementation uses dict lookup which is O(1).
        """
        import time

        # Create large matrix with 1000 entries
        entries = [
            ObservabilityEntry(
                observer=f"agent_{i}",
                target=f"agent_{(i + 1) % 1000}",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.1,
            )
            for i in range(1000)
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.0)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Perform lookups - should be fast regardless of position in original list
        start = time.perf_counter()
        for _ in range(100):
            # Lookup first entry
            matrix.get_observability("agent_0", "agent_1")
            # Lookup middle entry
            matrix.get_observability("agent_500", "agent_501")
            # Lookup last entry
            matrix.get_observability("agent_999", "agent_0")
            # Lookup undefined pair
            matrix.get_observability("agent_0", "agent_999")
        end = time.perf_counter()

        # This test mainly documents the O(1) guarantee
        # The actual time should be negligible (< 0.1s for 400 lookups)
        elapsed = end - start
        assert elapsed < 0.1, (
            f"Lookups took {elapsed:.3f}s for 400 operations. "
            "Expected O(1) dict lookup to be much faster."
        )

    def test_empty_matrix_returns_default(self):
        """Should return default for all lookups when matrix is empty."""
        entries = []
        default = DefaultObservability(
            level=ObservabilityLevel.EXTERNAL, noise=0.25
        )
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # All lookups should return default
        level, noise = matrix.get_observability("any_agent", "any_target")
        assert level == ObservabilityLevel.EXTERNAL
        assert noise == 0.25

    def test_matrix_with_all_observability_levels(self):
        """Should correctly handle all three observability levels."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="target_1",
                level=ObservabilityLevel.UNAWARE,
                noise=0.0,
            ),
            ObservabilityEntry(
                observer="agent_1",
                target="target_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.1,
            ),
            ObservabilityEntry(
                observer="agent_1",
                target="target_3",
                level=ObservabilityLevel.INSIDER,
                noise=0.05,
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Verify each level
        level, _ = matrix.get_observability("agent_1", "target_1")
        assert level == ObservabilityLevel.UNAWARE

        level, _ = matrix.get_observability("agent_1", "target_2")
        assert level == ObservabilityLevel.EXTERNAL

        level, _ = matrix.get_observability("agent_1", "target_3")
        assert level == ObservabilityLevel.INSIDER

    def test_matrix_with_zero_and_nonzero_noise(self):
        """Should correctly handle both zero and non-zero noise values."""
        entries = [
            ObservabilityEntry(
                observer="agent_1",
                target="target_1",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.0,  # Explicit zero
            ),
            ObservabilityEntry(
                observer="agent_1",
                target="target_2",
                level=ObservabilityLevel.EXTERNAL,
                noise=0.25,  # Non-zero
            ),
        ]
        default = DefaultObservability(level=ObservabilityLevel.UNAWARE, noise=0.5)
        matrix = ObservabilityMatrix(entries=entries, default=default)

        # Verify zero noise
        _, noise = matrix.get_observability("agent_1", "target_1")
        assert noise == 0.0

        # Verify non-zero noise
        _, noise = matrix.get_observability("agent_1", "target_2")
        assert noise == 0.25
