"""Integration tests for complex data types in simulations."""

import pytest
from llm_sim.models.config import VariableDefinition
from llm_sim.models.state import create_agent_state_model, create_global_state_model


class TestDictIntegration:
    """Integration tests for dictionary variables (User Story 1)."""

    def test_inventory_dict_initialization_and_access(self):
        """Test dict variables can be used in agent state models."""
        # Define agent variables with dict type
        agent_vars = {
            "inventory": VariableDefinition(
                type="dict",
                key_type="str",
                value_type="float",
                default={}
            ),
            "wealth": VariableDefinition(
                type="float",
                min=0.0,
                default=100.0
            )
        }

        # Create agent state model
        AgentState = create_agent_state_model(agent_vars)

        # Create agent instance with dict
        agent = AgentState(
            name="Trader_1",
            inventory={"food": 10.5, "metal": 5.0},
            wealth=100.0
        )

        # Verify dict access
        assert agent.name == "Trader_1"
        assert agent.inventory == {"food": 10.5, "metal": 5.0}
        assert agent.wealth == 100.0

        # Verify type validation
        assert isinstance(agent.inventory, dict)
        assert agent.inventory["food"] == 10.5

    def test_dict_with_fixed_schema_in_global_state(self):
        """Test dict with fixed schema in global state."""
        global_vars = {
            "stats": VariableDefinition(
                type="dict",
                schema={
                    "total_trades": VariableDefinition(type="int", min=0, default=0),
                    "avg_price": VariableDefinition(type="float", min=0.0, default=0.0),
                },
                default={"total_trades": 0, "avg_price": 0.0}
            )
        }

        GlobalState = create_global_state_model(global_vars)

        # Create global state with fixed schema dict
        global_state = GlobalState(stats={"total_trades": 10, "avg_price": 25.5})

        assert global_state.stats.total_trades == 10
        assert global_state.stats.avg_price == 25.5

    def test_dict_serialization_round_trip(self):
        """Test dict variables serialize and deserialize correctly."""
        agent_vars = {
            "inventory": VariableDefinition(
                type="dict",
                key_type="str",
                value_type="int",
                default={}
            )
        }

        AgentState = create_agent_state_model(agent_vars)
        agent = AgentState(name="Agent_1", inventory={"apples": 5, "oranges": 3})

        # Serialize to dict
        data = agent.model_dump()
        assert data["inventory"] == {"apples": 5, "oranges": 3}

        # Deserialize from dict
        restored = AgentState(**data)
        assert restored.inventory == {"apples": 5, "oranges": 3}

        # Serialize to JSON
        json_str = agent.model_dump_json()
        restored_from_json = AgentState.model_validate_json(json_str)
        assert restored_from_json.inventory == {"apples": 5, "oranges": 3}


class TestTupleIntegration:
    """Integration tests for tuple variables (User Story 2)."""

    def test_tuple_coordinates_in_simulation(self):
        """Test tuple variables can be used for coordinates in agent state."""
        # Define agent variables with tuple type for coordinates
        agent_vars = {
            "location": VariableDefinition(
                type="tuple",
                item_types=[
                    VariableDefinition(type="float", default=0.0),
                    VariableDefinition(type="float", default=0.0),
                ],
                default=[0.0, 0.0]
            ),
            "health": VariableDefinition(
                type="float",
                min=0.0,
                max=100.0,
                default=100.0
            )
        }

        # Create agent state model
        AgentState = create_agent_state_model(agent_vars)

        # Create agent instance with tuple
        agent = AgentState(
            name="Explorer_1",
            location=(10.5, 20.3),
            health=100.0
        )

        # Verify tuple access
        assert agent.name == "Explorer_1"
        assert agent.location == (10.5, 20.3)
        assert isinstance(agent.location, tuple)
        assert len(agent.location) == 2

        # Verify serialization round-trip
        json_str = agent.model_dump_json()
        restored = AgentState.model_validate_json(json_str)
        assert restored.location == (10.5, 20.3)
        assert isinstance(restored.location, tuple)


class TestListIntegration:
    """Integration tests for list variables (User Story 3)."""

    def test_action_history_list_operations(self):
        """Test list variables can be used for action history in agent state."""
        # Define agent variables with list type for action history
        agent_vars = {
            "action_history": VariableDefinition(
                type="list",
                item_type="str",
                max_length=10,
                default=[]
            ),
            "position_history": VariableDefinition(
                type="list",
                item_type=VariableDefinition(
                    type="tuple",
                    item_types=[
                        VariableDefinition(type="float", default=0.0),
                        VariableDefinition(type="float", default=0.0),
                    ],
                    default=[0.0, 0.0]
                ),
                max_length=100,
                default=[]
            )
        }

        # Create agent state model
        AgentState = create_agent_state_model(agent_vars)

        # Create agent instance with lists
        agent = AgentState(
            name="Agent_1",
            action_history=["spawn", "move", "trade"],
            position_history=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]
        )

        # Verify list access
        assert agent.name == "Agent_1"
        assert agent.action_history == ["spawn", "move", "trade"]
        assert len(agent.action_history) == 3
        assert isinstance(agent.action_history, list)

        # Verify nested list with tuples
        assert len(agent.position_history) == 3
        assert agent.position_history[0] == (0.0, 0.0)
        assert isinstance(agent.position_history[0], tuple)

        # Verify serialization round-trip
        json_str = agent.model_dump_json()
        restored = AgentState.model_validate_json(json_str)
        assert restored.action_history == ["spawn", "move", "trade"]
        assert restored.position_history == [(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)]


class TestStringIntegration:
    """Integration tests for string variables (User Story 4)."""

    def test_destination_string_nullable(self):
        """Test string variables with pattern validation and nullable behavior."""
        # Define agent variables with string types
        agent_vars = {
            "target_destination": VariableDefinition(
                type="str",
                default=None
            ),
            "agent_name": VariableDefinition(
                type="str",
                pattern=r"^[A-Za-z][A-Za-z0-9_]{2,19}$",
                max_length=20,
                default="Agent_1"
            ),
            "notes": VariableDefinition(
                type="str",
                max_length=500,
                default=""
            )
        }

        # Create agent state model
        AgentState = create_agent_state_model(agent_vars)

        # Create agent with string fields
        agent = AgentState(
            name="Agent_1",
            target_destination=None,  # nullable
            agent_name="Trader_Alpha",
            notes="This agent trades food"
        )

        # Verify string access
        assert agent.target_destination is None
        assert agent.agent_name == "Trader_Alpha"
        assert agent.notes == "This agent trades food"

        # Verify serialization round-trip with null
        json_str = agent.model_dump_json()
        restored = AgentState.model_validate_json(json_str)
        assert restored.target_destination is None
        assert restored.agent_name == "Trader_Alpha"
        assert restored.notes == "This agent trades food"


class TestObjectIntegration:
    """Integration tests for object variables (User Story 5)."""

    def test_nested_town_global_state(self):
        """Test object type with nested schema in global state."""
        # Define global state with nested town object
        global_vars = {
            "capital": VariableDefinition(
                type="object",
                schema={
                    "name": VariableDefinition(type="str", default="Capital City"),
                    "position": VariableDefinition(
                        type="tuple",
                        item_types=[
                            VariableDefinition(type="float", default=0.0),
                            VariableDefinition(type="float", default=0.0),
                        ],
                        default=[0.0, 0.0]
                    ),
                    "population": VariableDefinition(type="int", min=0, default=10000),
                    "resources": VariableDefinition(
                        type="dict",
                        key_type="str",
                        value_type="float",
                        default={}
                    ),
                },
                default={
                    "name": "Capital City",
                    "position": [0.0, 0.0],
                    "population": 10000,
                    "resources": {}
                }
            )
        }

        # Create global state model
        GlobalState = create_global_state_model(global_vars)

        # Create global state with nested object
        global_state = GlobalState(
            capital={
                "name": "New Capital",
                "position": (50.0, 100.0),
                "population": 50000,
                "resources": {"food": 1000.0, "gold": 500.0}
            }
        )

        # Verify nested object access
        assert global_state.capital.name == "New Capital"
        assert global_state.capital.position == (50.0, 100.0)
        assert global_state.capital.population == 50000
        assert global_state.capital.resources == {"food": 1000.0, "gold": 500.0}

        # Verify serialization round-trip
        json_str = global_state.model_dump_json()
        restored = GlobalState.model_validate_json(json_str)
        assert restored.capital.name == "New Capital"
        assert restored.capital.position == (50.0, 100.0)
        assert restored.capital.population == 50000
        assert restored.capital.resources == {"food": 1000.0, "gold": 500.0}
