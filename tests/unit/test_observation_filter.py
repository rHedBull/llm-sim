"""Tests for variable filtering logic in partial observability."""

import pytest
from pydantic import BaseModel

from llm_sim.infrastructure.observability.filter import filter_variables
from llm_sim.infrastructure.observability.config import (
    ObservabilityLevel,
    VariableVisibilityConfig,
)


# Test Pydantic models for state
class AgentState(BaseModel):
    """Mock agent state model with various field types."""

    name: str
    wealth: float
    military_strength: int
    secret_plans: str
    internal_calculations: list[int]
    public_message: str


class GlobalState(BaseModel):
    """Mock global state model without 'name' field."""

    temperature: float
    market_price: int
    private_data: str
    public_announcements: list[str]


class TestExternalLevelFiltersToExternalVariables:
    """Test that EXTERNAL level returns only external variables."""

    def test_filters_to_external_variables_with_name(self) -> None:
        """External level includes 'name' and external variables only."""
        state = AgentState(
            name="TestAgent",
            wealth=1000.0,
            military_strength=50,
            secret_plans="attack at dawn",
            internal_calculations=[1, 2, 3],
            public_message="hello world",
        )

        visibility_config = VariableVisibilityConfig(
            external=["wealth", "public_message"],
            internal=["military_strength", "secret_plans", "internal_calculations"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # Should include 'name' (always visible) + external variables
        assert result == {
            "name": "TestAgent",
            "wealth": 1000.0,
            "public_message": "hello world",
        }

    def test_filters_to_external_variables_without_name(self) -> None:
        """External level for global state (no 'name' field) includes only external vars."""
        state = GlobalState(
            temperature=25.5,
            market_price=100,
            private_data="secret",
            public_announcements=["news1", "news2"],
        )

        visibility_config = VariableVisibilityConfig(
            external=["temperature", "public_announcements"],
            internal=["market_price", "private_data"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # Should only include external variables (no 'name' field exists)
        assert result == {
            "temperature": 25.5,
            "public_announcements": ["news1", "news2"],
        }

    def test_external_with_no_external_variables_configured(self) -> None:
        """External level with no external variables returns only 'name' if present."""
        state = AgentState(
            name="Agent007",
            wealth=500.0,
            military_strength=30,
            secret_plans="classified",
            internal_calculations=[10],
            public_message="",
        )

        visibility_config = VariableVisibilityConfig(
            external=[],  # No external variables
            internal=["wealth", "military_strength", "secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # Should only return 'name'
        assert result == {"name": "Agent007"}


class TestInsiderLevelReturnsAllVariables:
    """Test that INSIDER level returns all variables."""

    def test_returns_all_variables_for_agent_state(self) -> None:
        """Insider level returns complete state dict for agent."""
        state = AgentState(
            name="InsiderAgent",
            wealth=2000.0,
            military_strength=75,
            secret_plans="top secret",
            internal_calculations=[5, 10, 15],
            public_message="public info",
        )

        visibility_config = VariableVisibilityConfig(
            external=["public_message"],
            internal=["wealth", "military_strength", "secret_plans", "internal_calculations"],
        )

        result = filter_variables(state, ObservabilityLevel.INSIDER, visibility_config)

        # Should return all variables
        assert result == {
            "name": "InsiderAgent",
            "wealth": 2000.0,
            "military_strength": 75,
            "secret_plans": "top secret",
            "internal_calculations": [5, 10, 15],
            "public_message": "public info",
        }

    def test_returns_all_variables_for_global_state(self) -> None:
        """Insider level returns complete state dict for global state."""
        state = GlobalState(
            temperature=30.0,
            market_price=250,
            private_data="confidential",
            public_announcements=["announcement"],
        )

        visibility_config = VariableVisibilityConfig(
            external=["temperature"],
            internal=["market_price", "private_data", "public_announcements"],
        )

        result = filter_variables(state, ObservabilityLevel.INSIDER, visibility_config)

        # Should return all variables
        assert result == {
            "temperature": 30.0,
            "market_price": 250,
            "private_data": "confidential",
            "public_announcements": ["announcement"],
        }

    def test_visibility_config_ignored_for_insider(self) -> None:
        """Insider level ignores visibility config and returns everything."""
        state = AgentState(
            name="AllAccess",
            wealth=0.0,
            military_strength=0,
            secret_plans="",
            internal_calculations=[],
            public_message="",
        )

        # Even with all variables marked as internal
        visibility_config = VariableVisibilityConfig(
            external=[],
            internal=["name", "wealth", "military_strength", "secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.INSIDER, visibility_config)

        # Still returns all variables
        assert result == state.model_dump()


class TestUnawareLevelReturnsEmptyDict:
    """Test that UNAWARE level returns empty dictionary."""

    def test_returns_empty_dict_for_agent_state(self) -> None:
        """Unaware level returns empty dict regardless of agent state."""
        state = AgentState(
            name="HiddenAgent",
            wealth=999.0,
            military_strength=100,
            secret_plans="invisible",
            internal_calculations=[1, 2, 3, 4],
            public_message="you can't see this",
        )

        visibility_config = VariableVisibilityConfig(
            external=["wealth", "public_message"],
            internal=["military_strength", "secret_plans", "internal_calculations"],
        )

        result = filter_variables(state, ObservabilityLevel.UNAWARE, visibility_config)

        assert result == {}

    def test_returns_empty_dict_for_global_state(self) -> None:
        """Unaware level returns empty dict regardless of global state."""
        state = GlobalState(
            temperature=15.0,
            market_price=500,
            private_data="hidden",
            public_announcements=["invisible"],
        )

        visibility_config = VariableVisibilityConfig(
            external=["temperature", "public_announcements"],
            internal=["market_price", "private_data"],
        )

        result = filter_variables(state, ObservabilityLevel.UNAWARE, visibility_config)

        assert result == {}

    def test_visibility_config_ignored_for_unaware(self) -> None:
        """Unaware level ignores visibility config and returns empty dict."""
        state = AgentState(
            name="NobodySeesMe",
            wealth=1.0,
            military_strength=1,
            secret_plans="x",
            internal_calculations=[0],
            public_message="y",
        )

        # Visibility config doesn't matter
        visibility_config = VariableVisibilityConfig(
            external=["name", "wealth", "military_strength", "secret_plans", "internal_calculations", "public_message"],
            internal=[],
        )

        result = filter_variables(state, ObservabilityLevel.UNAWARE, visibility_config)

        assert result == {}


class TestFilteringPreservesVariableTypes:
    """Test that filtering doesn't change types or values."""

    def test_preserves_string_type(self) -> None:
        """String values are preserved exactly."""
        state = AgentState(
            name="StringTest",
            wealth=0.0,
            military_strength=0,
            secret_plans="secret",
            internal_calculations=[],
            public_message="test message with special chars: !@#$%",
        )

        visibility_config = VariableVisibilityConfig(
            external=["public_message"],
            internal=["wealth", "military_strength", "secret_plans", "internal_calculations"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result["public_message"] == "test message with special chars: !@#$%"
        assert isinstance(result["public_message"], str)

    def test_preserves_numeric_types(self) -> None:
        """Numeric values (float, int) are preserved exactly."""
        state = AgentState(
            name="NumericTest",
            wealth=123.456,
            military_strength=999,
            secret_plans="",
            internal_calculations=[],
            public_message="",
        )

        visibility_config = VariableVisibilityConfig(
            external=["wealth", "military_strength"],
            internal=["secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result["wealth"] == 123.456
        assert isinstance(result["wealth"], float)
        assert result["military_strength"] == 999
        assert isinstance(result["military_strength"], int)

    def test_preserves_list_type_and_contents(self) -> None:
        """List values are preserved with correct type and contents."""
        state = AgentState(
            name="ListTest",
            wealth=0.0,
            military_strength=0,
            secret_plans="",
            internal_calculations=[1, 2, 3, 4, 5],
            public_message="",
        )

        visibility_config = VariableVisibilityConfig(
            external=["internal_calculations"],
            internal=["wealth", "military_strength", "secret_plans", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result["internal_calculations"] == [1, 2, 3, 4, 5]
        assert isinstance(result["internal_calculations"], list)
        assert all(isinstance(x, int) for x in result["internal_calculations"])

    def test_preserves_empty_and_zero_values(self) -> None:
        """Empty strings, zero values, and empty lists are preserved."""
        state = GlobalState(
            temperature=0.0,
            market_price=0,
            private_data="",
            public_announcements=[],
        )

        visibility_config = VariableVisibilityConfig(
            external=["temperature", "market_price", "private_data", "public_announcements"],
            internal=[],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result["temperature"] == 0.0
        assert result["market_price"] == 0
        assert result["private_data"] == ""
        assert result["public_announcements"] == []


class TestVariablesNotInListsHandledCorrectly:
    """Test edge cases for variables not in external/internal lists."""

    def test_variable_not_in_either_list_excluded_from_external(self) -> None:
        """Variables not in external or internal lists are excluded at EXTERNAL level."""
        state = AgentState(
            name="EdgeCase",
            wealth=100.0,
            military_strength=50,
            secret_plans="secret",
            internal_calculations=[1],
            public_message="public",
        )

        # Only specify some variables in visibility config
        visibility_config = VariableVisibilityConfig(
            external=["wealth"],  # Only wealth is external
            internal=["secret_plans"],  # Only secret_plans is internal
            # military_strength, internal_calculations, public_message not specified
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # Should only include 'name' (always) and 'wealth' (in external list)
        assert result == {
            "name": "EdgeCase",
            "wealth": 100.0,
        }
        # Variables not in lists are excluded
        assert "military_strength" not in result
        assert "internal_calculations" not in result
        assert "public_message" not in result

    def test_nonexistent_external_variable_in_config_ignored(self) -> None:
        """External variables listed in config but not in state are ignored."""
        state = AgentState(
            name="MissingVar",
            wealth=200.0,
            military_strength=20,
            secret_plans="x",
            internal_calculations=[],
            public_message="y",
        )

        visibility_config = VariableVisibilityConfig(
            external=["wealth", "nonexistent_field", "another_missing"],
            internal=["military_strength", "secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # Should only include 'name' and 'wealth' (nonexistent fields ignored)
        assert result == {
            "name": "MissingVar",
            "wealth": 200.0,
        }
        assert "nonexistent_field" not in result
        assert "another_missing" not in result

    def test_name_field_included_even_if_in_internal_list(self) -> None:
        """The 'name' field is always included at EXTERNAL level, even if marked internal."""
        state = AgentState(
            name="AlwaysVisible",
            wealth=50.0,
            military_strength=10,
            secret_plans="",
            internal_calculations=[],
            public_message="msg",
        )

        # Mark 'name' as internal (should still be visible)
        visibility_config = VariableVisibilityConfig(
            external=["public_message"],
            internal=["name", "wealth", "military_strength", "secret_plans", "internal_calculations"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        # 'name' should still be included
        assert result == {
            "name": "AlwaysVisible",
            "public_message": "msg",
        }

    def test_empty_external_list_returns_only_name_if_present(self) -> None:
        """When external list is empty, EXTERNAL level returns only 'name' field."""
        state = AgentState(
            name="OnlyName",
            wealth=0.0,
            military_strength=0,
            secret_plans="",
            internal_calculations=[],
            public_message="",
        )

        visibility_config = VariableVisibilityConfig(
            external=[],
            internal=["wealth", "military_strength", "secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result == {"name": "OnlyName"}

    def test_all_variables_in_internal_list_only(self) -> None:
        """When all variables are internal, EXTERNAL returns only 'name'."""
        state = AgentState(
            name="InternalOnly",
            wealth=1000.0,
            military_strength=100,
            secret_plans="classified",
            internal_calculations=[9, 8, 7],
            public_message="internal msg",
        )

        visibility_config = VariableVisibilityConfig(
            external=[],
            internal=["wealth", "military_strength", "secret_plans", "internal_calculations", "public_message"],
        )

        result = filter_variables(state, ObservabilityLevel.EXTERNAL, visibility_config)

        assert result == {"name": "InternalOnly"}

    def test_insider_returns_all_regardless_of_lists(self) -> None:
        """INSIDER level returns all variables even if not in any list."""
        state = AgentState(
            name="InsiderEdge",
            wealth=500.0,
            military_strength=60,
            secret_plans="plan",
            internal_calculations=[3, 2, 1],
            public_message="note",
        )

        # Minimal visibility config
        visibility_config = VariableVisibilityConfig(
            external=["wealth"],
            internal=["secret_plans"],
            # Other variables not listed
        )

        result = filter_variables(state, ObservabilityLevel.INSIDER, visibility_config)

        # Should return ALL state variables
        assert result == state.model_dump()
        assert "military_strength" in result
        assert "internal_calculations" in result
        assert "public_message" in result
