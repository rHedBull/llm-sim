"""Contract tests for observation format schema validation.

These tests validate the observation format schema for partial observability.
They test the JSON schema from specs/008-partial-observability-agents/contracts/observation-format-schema.json

NOTE: This is a TDD test - tests will FAIL until construct_observation is implemented.
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


@pytest.fixture
def schema():
    """Load the observation format JSON schema."""
    schema_path = Path("specs/008-partial-observability-agents/contracts/observation-format-schema.json")
    with open(schema_path) as f:
        return json.load(f)


class TestValidObservations:
    """Tests for valid observation structures that should pass validation."""

    def test_observation_has_same_structure_as_simulation_state(self, schema):
        """Observation has same top-level structure as SimulationState."""
        observation = {
            "turn": 5,
            "agents": {
                "Agent1": {"name": "Agent1", "economic_strength": 105.3},
                "Agent2": {"name": "Agent2", "economic_strength": 94.7}
            },
            "global_state": {
                "interest_rate": 0.052,
                "inflation": 0.028
            },
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_reasoning_chains_always_empty(self, schema):
        """reasoning_chains must always be empty list in observations."""
        observation = {
            "turn": 0,
            "agents": {},
            "global_state": {},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_agents_dict_can_be_subset(self, schema):
        """agents dict can be subset of ground truth (unaware targets excluded)."""
        # Single agent (subset of potentially larger ground truth)
        observation = {
            "turn": 3,
            "agents": {
                "ObservableAgent": {"name": "ObservableAgent", "health": 85.5}
            },
            "global_state": {"temperature": 22.5},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_agents_dict_can_be_empty(self, schema):
        """agents dict can be empty (no observable agents)."""
        observation = {
            "turn": 10,
            "agents": {},
            "global_state": {"market_volatility": 0.12},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_agent_state_with_filtered_variables(self, schema):
        """Agent state objects can have subset of ground truth fields."""
        observation = {
            "turn": 7,
            "agents": {
                # Agent with only observable variables (internal ones filtered)
                "Agent1": {"name": "Agent1", "economic_strength": 100.0},
                # Another agent with different observable variables
                "Agent2": {"name": "Agent2", "military_power": 50}
            },
            "global_state": {},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_global_state_with_filtered_variables(self, schema):
        """Global state can have subset of ground truth fields."""
        observation = {
            "turn": 1,
            "agents": {"A": {"name": "A"}},
            "global_state": {
                # Subset of global variables
                "interest_rate": 0.03
                # Other global vars may be filtered out
            },
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_numeric_values_with_noise(self, schema):
        """Numeric values may differ from ground truth due to noise."""
        observation = {
            "turn": 4,
            "agents": {
                "Agent1": {
                    "name": "Agent1",
                    # Noisy observation (actual might be 100.0)
                    "economic_strength": 99.83,
                    "confidence": 0.7234  # Noisy fractional value
                }
            },
            "global_state": {
                "inflation": 0.02456  # Noisy global value
            },
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_agent_name_always_present(self, schema):
        """Agent state must always have 'name' field."""
        observation = {
            "turn": 2,
            "agents": {
                "MinimalAgent": {"name": "MinimalAgent"}  # Only required field
            },
            "global_state": {},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)

    def test_turn_number_matches_ground_truth(self, schema):
        """Turn number in observation matches ground truth."""
        observation = {
            "turn": 42,  # Same as ground truth turn
            "agents": {},
            "global_state": {},
            "reasoning_chains": []
        }
        validate(instance=observation, schema=schema)


class TestInvalidObservations:
    """Tests for invalid observations that should fail validation."""

    def test_missing_turn_rejected(self, schema):
        """Observation without turn field should be rejected."""
        observation = {
            # Missing turn
            "agents": {},
            "global_state": {},
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_missing_agents_rejected(self, schema):
        """Observation without agents field should be rejected."""
        observation = {
            "turn": 5,
            # Missing agents
            "global_state": {},
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_missing_global_state_rejected(self, schema):
        """Observation without global_state field should be rejected."""
        observation = {
            "turn": 5,
            "agents": {},
            # Missing global_state
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_missing_reasoning_chains_rejected(self, schema):
        """Observation without reasoning_chains field should be rejected."""
        observation = {
            "turn": 5,
            "agents": {},
            "global_state": {}
            # Missing reasoning_chains
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_non_empty_reasoning_chains_rejected(self, schema):
        """reasoning_chains with items should be rejected."""
        observation = {
            "turn": 5,
            "agents": {},
            "global_state": {},
            "reasoning_chains": [{"reasoning": "not allowed"}]  # Must be empty
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_agent_without_name_rejected(self, schema):
        """Agent state without 'name' field should be rejected."""
        observation = {
            "turn": 5,
            "agents": {
                "InvalidAgent": {"economic_strength": 100.0}  # Missing name
            },
            "global_state": {},
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_negative_turn_rejected(self, schema):
        """Negative turn number should be rejected."""
        observation = {
            "turn": -1,  # Invalid: must be >= 0
            "agents": {},
            "global_state": {},
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_extra_top_level_fields_rejected(self, schema):
        """Observation with extra top-level fields should be rejected."""
        observation = {
            "turn": 5,
            "agents": {},
            "global_state": {},
            "reasoning_chains": [],
            "extra_field": "not allowed"  # Additional field not in schema
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)

    def test_invalid_agents_dict_key_rejected(self, schema):
        """Agent key with invalid characters should be rejected."""
        observation = {
            "turn": 5,
            "agents": {
                "Invalid-Agent!": {"name": "Invalid-Agent!"}  # Invalid characters in key
            },
            "global_state": {},
            "reasoning_chains": []
        }
        with pytest.raises(ValidationError):
            validate(instance=observation, schema=schema)


class TestStructuralCompliance:
    """Tests that validate structural compliance with SimulationState."""

    def test_all_required_fields_present(self, schema):
        """Observation must have all four required fields from SimulationState."""
        # Schema should require exactly: turn, agents, global_state, reasoning_chains
        assert schema["required"] == ["turn", "agents", "global_state", "reasoning_chains"]

    def test_no_additional_properties_allowed(self, schema):
        """Observation schema should not allow additional top-level properties."""
        assert schema["additionalProperties"] is False

    def test_reasoning_chains_max_items_zero(self, schema):
        """reasoning_chains schema should enforce maxItems: 0."""
        assert schema["properties"]["reasoning_chains"]["maxItems"] == 0

    def test_turn_minimum_zero(self, schema):
        """Turn field should have minimum value of 0."""
        assert schema["properties"]["turn"]["minimum"] == 0

    def test_agent_name_required(self, schema):
        """Agent state schema should require 'name' field."""
        agent_schema = schema["properties"]["agents"]["patternProperties"]["^[A-Za-z0-9_]+$"]
        assert "name" in agent_schema["required"]

    def test_agent_allows_additional_properties(self, schema):
        """Agent state schema should allow additional properties for state variables."""
        agent_schema = schema["properties"]["agents"]["patternProperties"]["^[A-Za-z0-9_]+$"]
        assert agent_schema["additionalProperties"] is True

    def test_global_state_allows_additional_properties(self, schema):
        """Global state schema should allow additional properties for state variables."""
        assert schema["properties"]["global_state"]["additionalProperties"] is True
