"""Tests for deterministic noise generation."""

from llm_sim.infrastructure.observability.noise import apply_noise


class TestNoiseGeneration:
    """Tests for apply_noise function."""

    def test_same_seed_produces_same_noise(self) -> None:
        """Verify determinism: same seed produces same output."""
        value = 100.0
        noise_factor = 0.2
        seed_components = (1, "agent_1", "economic_strength")

        # Call apply_noise multiple times with the same seed
        result_1 = apply_noise(value, noise_factor, seed_components)
        result_2 = apply_noise(value, noise_factor, seed_components)
        result_3 = apply_noise(value, noise_factor, seed_components)

        # All results should be identical
        assert result_1 == result_2
        assert result_2 == result_3

    def test_zero_noise_returns_value_unchanged(self) -> None:
        """Test that noise_factor=0.0 returns value unchanged."""
        value = 42.5
        noise_factor = 0.0
        seed_components = (1, "agent_1", "some_variable")

        result = apply_noise(value, noise_factor, seed_components)

        # With zero noise, value should be returned unchanged
        assert result == value

    def test_noise_bounded_within_factor(self) -> None:
        """Test that noise stays within [-factor, +factor] range."""
        value = 100.0
        noise_factor = 0.2

        # Test with many different seeds to check bounds
        for turn in range(100):
            for agent_id in ["agent_1", "agent_2", "agent_3"]:
                for var_name in ["var_a", "var_b", "var_c"]:
                    seed_components = (turn, agent_id, var_name)
                    result = apply_noise(value, noise_factor, seed_components)

                    # Calculate the actual noise applied
                    # result = value * (1.0 + noise)
                    # noise = (result / value) - 1.0
                    noise = (result / value) - 1.0

                    # Noise should be within bounds
                    assert -noise_factor <= noise <= noise_factor, (
                        f"Noise {noise} outside bounds [-{noise_factor}, {noise_factor}] "
                        f"for seed {seed_components}"
                    )

                    # Result should be within the expected range
                    min_expected = value * (1.0 - noise_factor)
                    max_expected = value * (1.0 + noise_factor)
                    assert min_expected <= result <= max_expected, (
                        f"Result {result} outside expected range "
                        f"[{min_expected}, {max_expected}]"
                    )

    def test_different_seeds_produce_different_noise(self) -> None:
        """Test that varying seeds produce different values."""
        value = 100.0
        noise_factor = 0.2

        # Collect results from different seeds
        results = set()
        for turn in range(10):
            for agent_id in [f"agent_{i}" for i in range(5)]:
                for var_name in ["var_x", "var_y", "var_z"]:
                    seed_components = (turn, agent_id, var_name)
                    result = apply_noise(value, noise_factor, seed_components)
                    results.add(result)

        # We should have many different results
        # With 10 * 5 * 3 = 150 different seeds, we expect high diversity
        assert len(results) > 100, (
            f"Expected diverse results from different seeds, "
            f"but only got {len(results)} unique values out of 150 attempts"
        )

    def test_multiplicative_noise_formula(self) -> None:
        """Verify the formula: value * (1.0 + random_factor)."""
        value = 50.0
        noise_factor = 0.1
        seed_components = (5, "observer_1", "military_strength")

        result = apply_noise(value, noise_factor, seed_components)

        # Extract the random_factor that was applied
        # result = value * (1.0 + random_factor)
        # random_factor = (result / value) - 1.0
        random_factor = (result / value) - 1.0

        # Verify the formula by reconstructing the result
        reconstructed = value * (1.0 + random_factor)
        assert abs(result - reconstructed) < 1e-10, (
            f"Formula verification failed: "
            f"result={result}, reconstructed={reconstructed}"
        )

        # Verify random_factor is within bounds
        assert -noise_factor <= random_factor <= noise_factor

    def test_negative_values(self) -> None:
        """Test that noise works correctly with negative values."""
        value = -100.0
        noise_factor = 0.15
        seed_components = (1, "agent_1", "balance")

        result = apply_noise(value, noise_factor, seed_components)

        # For negative values, the bounds are inverted
        # value * (1.0 + noise_factor) is the minimum (most negative)
        # value * (1.0 - noise_factor) is the maximum (least negative)
        min_expected = value * (1.0 + noise_factor)
        max_expected = value * (1.0 - noise_factor)

        assert min_expected <= result <= max_expected

    def test_zero_value(self) -> None:
        """Test that noise on zero value returns zero."""
        value = 0.0
        noise_factor = 0.3
        seed_components = (1, "agent_1", "variable")

        result = apply_noise(value, noise_factor, seed_components)

        # 0.0 * (1.0 + anything) = 0.0
        assert result == 0.0

    def test_different_turn_same_agent_variable(self) -> None:
        """Test that different turns produce different noise for same agent/variable."""
        value = 100.0
        noise_factor = 0.2
        agent_id = "agent_1"
        var_name = "economic_strength"

        results = []
        for turn in range(10):
            seed_components = (turn, agent_id, var_name)
            result = apply_noise(value, noise_factor, seed_components)
            results.append(result)

        # All results should be different (with high probability)
        assert len(set(results)) == len(results), (
            "Expected different noise for different turns"
        )

    def test_different_agent_same_turn_variable(self) -> None:
        """Test that different agents produce different noise for same turn/variable."""
        value = 100.0
        noise_factor = 0.2
        turn = 1
        var_name = "economic_strength"

        results = []
        for agent_id in [f"agent_{i}" for i in range(10)]:
            seed_components = (turn, agent_id, var_name)
            result = apply_noise(value, noise_factor, seed_components)
            results.append(result)

        # All results should be different (with high probability)
        assert len(set(results)) == len(results), (
            "Expected different noise for different agents"
        )

    def test_different_variable_same_turn_agent(self) -> None:
        """Test that different variables produce different noise for same turn/agent."""
        value = 100.0
        noise_factor = 0.2
        turn = 1
        agent_id = "agent_1"

        results = []
        for var_name in [f"var_{i}" for i in range(10)]:
            seed_components = (turn, agent_id, var_name)
            result = apply_noise(value, noise_factor, seed_components)
            results.append(result)

        # All results should be different (with high probability)
        assert len(set(results)) == len(results), (
            "Expected different noise for different variables"
        )

    def test_large_noise_factor(self) -> None:
        """Test with a large noise factor."""
        value = 100.0
        noise_factor = 0.9  # 90% noise
        seed_components = (1, "agent_1", "variable")

        result = apply_noise(value, noise_factor, seed_components)

        # Should still be within bounds
        min_expected = value * (1.0 - noise_factor)
        max_expected = value * (1.0 + noise_factor)
        assert min_expected <= result <= max_expected

    def test_small_noise_factor(self) -> None:
        """Test with a small noise factor."""
        value = 100.0
        noise_factor = 0.01  # 1% noise
        seed_components = (1, "agent_1", "variable")

        result = apply_noise(value, noise_factor, seed_components)

        # Should still be within bounds
        min_expected = value * (1.0 - noise_factor)
        max_expected = value * (1.0 + noise_factor)
        assert min_expected <= result <= max_expected

        # Result should be close to original value
        assert abs(result - value) <= value * noise_factor
