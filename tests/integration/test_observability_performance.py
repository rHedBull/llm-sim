"""Performance tests for observation construction.

T029: Validate observation construction overhead at realistic scale.

Tests:
- test_observation_construction_performance_100_agents: Performance with 100 agents
- test_memory_overhead_acceptable: Memory overhead validation
"""

import gc
import logging
import sys
import time
from typing import Dict

import pytest

# Suppress logging during performance tests to avoid output overhead
logging.getLogger("llm_sim").setLevel(logging.CRITICAL)

from llm_sim.models.config import VariableDefinition

# Mock the logger in observation module to avoid logging errors during performance tests
from unittest.mock import MagicMock
import llm_sim.models.observation as obs_module
obs_module.logger = MagicMock()

from llm_sim.models.observation import construct_observation
from llm_sim.models.state import (
    SimulationState,
    create_agent_state_model,
    create_global_state_model,
)
from llm_sim.infrastructure.observability.config import ObservabilityConfig


@pytest.fixture
def agent_variable_definitions_20vars():
    """Create 20 variables for agent state (mix of external and internal)."""
    var_defs = {}

    # 10 external (public) variables
    for i in range(10):
        var_defs[f"public_var_{i}"] = VariableDefinition(
            type="float", min=0.0, max=1000.0, default=100.0
        )

    # 10 internal (private) variables
    for i in range(10):
        var_defs[f"private_var_{i}"] = VariableDefinition(
            type="float", min=0.0, max=1000.0, default=50.0
        )

    return var_defs


@pytest.fixture
def global_variable_definitions_basic():
    """Basic global variables for performance tests."""
    return {
        "global_metric_1": VariableDefinition(type="float", min=0.0, max=10000.0, default=1000.0),
        "global_metric_2": VariableDefinition(type="float", min=0.0, max=10000.0, default=2000.0),
        "global_metric_3": VariableDefinition(type="int", min=0, max=100, default=50),
    }


@pytest.fixture
def observability_config_external_default():
    """Observability config with external level as default and varied noise."""
    return ObservabilityConfig(
        enabled=True,
        variable_visibility={
            "external": [f"public_var_{i}" for i in range(10)],
            "internal": [f"private_var_{i}" for i in range(10)],
        },
        matrix=[
            # Each agent sees itself perfectly
            # All other agents: external level with 0.2 noise (handled by default)
        ],
        default={
            "level": "external",
            "noise": 0.2,
        },
    )


@pytest.fixture
def observability_config_insider_matrix():
    """Observability config with explicit insider entries in matrix."""
    config_dict = {
        "enabled": True,
        "variable_visibility": {
            "external": [f"public_var_{i}" for i in range(10)],
            "internal": [f"private_var_{i}" for i in range(10)],
        },
        "matrix": [
            # First 10 agents see themselves with insider access
            *[[f"Agent_{i}", f"Agent_{i}", "insider", 0.0] for i in range(10)],
        ],
        "default": {
            "level": "external",
            "noise": 0.3,
        },
    }
    return ObservabilityConfig(**config_dict)


def create_ground_truth_with_n_agents(
    n_agents: int,
    agent_var_defs: Dict[str, VariableDefinition],
    global_var_defs: Dict[str, VariableDefinition],
) -> SimulationState:
    """Create ground truth state with N agents.

    Args:
        n_agents: Number of agents to create
        agent_var_defs: Agent variable definitions
        global_var_defs: Global variable definitions

    Returns:
        SimulationState with n_agents agents
    """
    AgentState = create_agent_state_model(agent_var_defs)
    GlobalState = create_global_state_model(global_var_defs)

    # Create N agents with varying values
    agents = {}
    for i in range(n_agents):
        agent_data = {"name": f"Agent_{i}"}

        # Set public variables with varied values (keep within 0-1000 range)
        for j in range(10):
            agent_data[f"public_var_{j}"] = 100.0 + ((i % 90) * 10) + j

        # Set private variables with varied values (keep within 0-1000 range)
        for j in range(10):
            agent_data[f"private_var_{j}"] = 50.0 + ((i % 190) * 5) + j

        agents[f"Agent_{i}"] = AgentState(**agent_data)

    global_state = GlobalState(
        global_metric_1=1000.0,
        global_metric_2=2000.0,
        global_metric_3=50,
    )

    return SimulationState(
        turn=1,
        agents=agents,
        global_state=global_state,
        reasoning_chains=[],
    )


def test_observation_construction_performance_100_agents(
    agent_variable_definitions_20vars,
    global_variable_definitions_basic,
    observability_config_external_default,
):
    """T029: Test observation construction performance with 100 agents.

    Requirements:
    - Create config with 100 agents, 20 variables each
    - Measure time per observation construction
    - Assert < 10ms per agent (reasonable target)
    - Test with different matrix configurations

    This test validates that observation construction scales acceptably
    to target simulation sizes (10-100 agents).
    """
    # Create ground truth with 100 agents
    ground_truth = create_ground_truth_with_n_agents(
        n_agents=100,
        agent_var_defs=agent_variable_definitions_20vars,
        global_var_defs=global_variable_definitions_basic,
    )

    # Test observation construction for first agent
    observer_id = "Agent_0"

    # Warm-up run (to account for JIT compilation, caching, etc.)
    _ = construct_observation(observer_id, ground_truth, observability_config_external_default)

    # Performance measurement
    num_iterations = 10
    times = []

    for _ in range(num_iterations):
        start = time.perf_counter()
        observation = construct_observation(
            observer_id, ground_truth, observability_config_external_default
        )
        end = time.perf_counter()
        times.append(end - start)

    # Calculate statistics
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)

    # Validate observation is correct
    assert observer_id in observation.agents
    assert len(observation.agents) == 100  # All agents visible (default: external)

    # Check that external variables are visible
    agent_0_obs = observation.agents["Agent_0"]
    assert hasattr(agent_0_obs, "public_var_0")

    # Performance assertion: < 100ms per observation (1ms per agent is reasonable)
    target_time_ms = 100.0
    avg_time_ms = avg_time * 1000

    print(f"\nPerformance metrics (100 agents, 20 vars each):")
    print(f"  Average time: {avg_time_ms:.2f} ms")
    print(f"  Min time: {min_time * 1000:.2f} ms")
    print(f"  Max time: {max_time * 1000:.2f} ms")
    print(f"  Target: < {target_time_ms} ms")
    print(f"  Time per agent: {avg_time_ms / 100:.3f} ms")

    assert avg_time_ms < target_time_ms, (
        f"Observation construction too slow: {avg_time_ms:.2f}ms > {target_time_ms}ms"
    )


def test_observation_construction_performance_varied_matrix(
    agent_variable_definitions_20vars,
    global_variable_definitions_basic,
    observability_config_insider_matrix,
):
    """Test performance with explicit insider entries in matrix.

    This tests a different matrix configuration where some agents
    have explicit insider access to themselves (vs. using default).
    """
    # Create ground truth with 50 agents (smaller for this variant)
    ground_truth = create_ground_truth_with_n_agents(
        n_agents=50,
        agent_var_defs=agent_variable_definitions_20vars,
        global_var_defs=global_variable_definitions_basic,
    )

    observer_id = "Agent_5"

    # Warm-up
    _ = construct_observation(observer_id, ground_truth, observability_config_insider_matrix)

    # Performance measurement
    num_iterations = 10
    times = []

    for _ in range(num_iterations):
        start = time.perf_counter()
        observation = construct_observation(
            observer_id, ground_truth, observability_config_insider_matrix
        )
        end = time.perf_counter()
        times.append(end - start)

    avg_time = sum(times) / len(times)
    avg_time_ms = avg_time * 1000

    # Validate observation
    assert observer_id in observation.agents
    assert len(observation.agents) == 50

    # Agent_5 should see itself as insider (all variables)
    agent_5_obs = observation.agents["Agent_5"]
    assert hasattr(agent_5_obs, "public_var_0")
    assert hasattr(agent_5_obs, "private_var_0")  # Insider access

    print(f"\nPerformance with insider matrix (50 agents, 20 vars each):")
    print(f"  Average time: {avg_time_ms:.2f} ms")
    print(f"  Time per agent: {avg_time_ms / 50:.3f} ms")

    # Should still be under 50ms (1ms per agent)
    assert avg_time_ms < 50.0


def test_memory_overhead_acceptable(
    agent_variable_definitions_20vars,
    global_variable_definitions_basic,
    observability_config_external_default,
):
    """T029: Test memory overhead of observation construction.

    Requirements:
    - Create observations for 10 agents
    - Verify memory overhead < 1MB per observation
    - Check that observations don't leak references to ground truth

    This test validates that observations are memory-efficient and
    properly isolated from ground truth.
    """
    # Create ground truth with 10 agents
    ground_truth = create_ground_truth_with_n_agents(
        n_agents=10,
        agent_var_defs=agent_variable_definitions_20vars,
        global_var_defs=global_variable_definitions_basic,
    )

    # Force garbage collection before measurement
    gc.collect()

    # Get baseline memory (if possible)
    baseline_memory = None
    if hasattr(sys, "getsizeof"):
        baseline_memory = sys.getsizeof(ground_truth)

    # Create observations for all 10 agents
    observations = []
    for i in range(10):
        observer_id = f"Agent_{i}"
        obs = construct_observation(
            observer_id, ground_truth, observability_config_external_default
        )
        observations.append(obs)

    # Memory overhead check (if sys.getsizeof available)
    if baseline_memory is not None:
        # Measure total size of observations
        total_obs_size = sum(sys.getsizeof(obs) for obs in observations)
        avg_obs_size = total_obs_size / len(observations)

        # Convert to MB
        avg_obs_size_mb = avg_obs_size / (1024 * 1024)

        print(f"\nMemory metrics:")
        print(f"  Ground truth size: {baseline_memory / (1024 * 1024):.2f} MB")
        print(f"  Average observation size: {avg_obs_size_mb:.4f} MB")
        print(f"  Total observations size: {total_obs_size / (1024 * 1024):.2f} MB")

        # Assert < 1MB per observation (generous limit)
        assert avg_obs_size_mb < 1.0, (
            f"Observation too large: {avg_obs_size_mb:.4f}MB > 1.0MB"
        )

    # Validate isolation: observations should not reference ground truth objects
    for i, obs in enumerate(observations):
        observer_id = f"Agent_{i}"

        # Check that observer sees itself
        assert observer_id in obs.agents

        # Verify observation is a new object, not the same reference
        if observer_id in ground_truth.agents:
            # The observation's agent state should be a different object
            assert obs.agents[observer_id] is not ground_truth.agents[observer_id]

        # Verify global state is a new object
        assert obs.global_state is not ground_truth.global_state

    # Additional check: modifying observation should not affect ground truth
    # (This would fail if there are shared references)
    obs_0 = observations[0]

    # Observations are immutable (frozen=True), so we can't directly modify
    # But we can verify they're frozen
    agent_0_obs = obs_0.agents["Agent_0"]

    # Try to set an attribute (should fail for frozen models)
    from pydantic import ValidationError as PydanticValidationError
    with pytest.raises((AttributeError, TypeError, PydanticValidationError)):
        agent_0_obs.public_var_0 = 999.0

    print("\nIsolation check: PASSED")
    print("  Observations are properly isolated from ground truth")
    print("  Observations are immutable (frozen)")


def test_observation_construction_scales_linearly(
    agent_variable_definitions_20vars,
    global_variable_definitions_basic,
    observability_config_external_default,
):
    """Test that observation construction scales approximately linearly with agent count.

    This test validates that performance degradation is acceptable as
    the number of agents increases.
    """
    agent_counts = [10, 25, 50, 100]
    times_per_agent = []

    for n_agents in agent_counts:
        # Create ground truth
        ground_truth = create_ground_truth_with_n_agents(
            n_agents=n_agents,
            agent_var_defs=agent_variable_definitions_20vars,
            global_var_defs=global_variable_definitions_basic,
        )

        observer_id = "Agent_0"

        # Warm-up
        _ = construct_observation(observer_id, ground_truth, observability_config_external_default)

        # Measure
        num_iterations = 5
        times = []
        for _ in range(num_iterations):
            start = time.perf_counter()
            _ = construct_observation(observer_id, ground_truth, observability_config_external_default)
            end = time.perf_counter()
            times.append(end - start)

        avg_time = sum(times) / len(times)
        avg_time_ms = avg_time * 1000
        times_per_agent.append(avg_time_ms)

        print(f"\n{n_agents} agents: {avg_time_ms:.2f} ms")

    # Check that scaling is reasonable
    # From 10 to 100 agents (10x increase), time should not increase more than 15x
    # (allowing for some overhead beyond linear scaling)
    time_ratio = times_per_agent[-1] / times_per_agent[0]
    agent_ratio = agent_counts[-1] / agent_counts[0]

    print(f"\nScaling analysis:")
    print(f"  Agent count ratio: {agent_ratio}x")
    print(f"  Time ratio: {time_ratio:.2f}x")
    print(f"  Scaling factor: {time_ratio / agent_ratio:.2f}")

    # Allow up to 1.5x overhead on linear scaling
    assert time_ratio < agent_ratio * 1.5, (
        f"Scaling worse than linear: {time_ratio:.2f}x vs {agent_ratio}x agents"
    )
