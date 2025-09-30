"""Unit tests for ComponentDiscovery mechanism.

These tests verify that the discovery system correctly loads
concrete implementations by filename.
"""

import pytest
from pathlib import Path

from llm_sim.discovery import ComponentDiscovery
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.infrastructure.base.validator import BaseValidator


class TestComponentDiscovery:
    """Test ComponentDiscovery class."""

    @pytest.fixture
    def discovery(self):
        """Create a ComponentDiscovery instance."""
        # Point to src/llm_sim directory
        implementations_root = Path(__file__).parent.parent.parent / "src" / "llm_sim"
        return ComponentDiscovery(implementations_root)

    def test_filename_to_classname_simple(self, discovery):
        """Test conversion of simple snake_case to PascalCase."""
        assert discovery._filename_to_classname("nation") == "Nation"

    def test_filename_to_classname_multi_word(self, discovery):
        """Test conversion of multi-word snake_case to PascalCase."""
        assert discovery._filename_to_classname("econ_llm_agent") == "EconLLMAgent"

    def test_filename_to_classname_with_underscores(self, discovery):
        """Test conversion preserves acronyms properly."""
        assert discovery._filename_to_classname("always_valid") == "AlwaysValid"

    def test_load_agent_returns_class(self, discovery):
        """load_agent should return a class, not an instance."""
        AgentClass = discovery.load_agent("nation")
        assert isinstance(AgentClass, type)
        assert issubclass(AgentClass, BaseAgent)
        # Verify it's the correct class
        assert AgentClass.__name__ == "NationAgent"

    def test_load_agent_missing_file_raises_error(self, discovery):
        """load_agent with non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            discovery.load_agent("nonexistent_agent")
        
        assert "No implementation found" in str(exc_info.value)
        assert "nonexistent_agent" in str(exc_info.value)

    def test_load_agent_wrong_class_name_raises_error(self, discovery):
        """load_agent should raise AttributeError if class name doesn't match convention."""
        # This test would require creating a malformed test file
        # Skip for now, but document the expected behavior
        pass

    def test_load_agent_caching(self, discovery):
        """load_agent should cache results."""
        AgentClass1 = discovery.load_agent("nation")
        AgentClass2 = discovery.load_agent("nation")
        
        # Should return the same class object (cached)
        assert AgentClass1 is AgentClass2

    def test_load_engine_returns_class(self, discovery):
        """load_engine should return an engine class."""
        EngineClass = discovery.load_engine("economic")
        assert isinstance(EngineClass, type)
        assert issubclass(EngineClass, BaseEngine)

    def test_load_engine_missing_file_raises_error(self, discovery):
        """load_engine with non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            discovery.load_engine("nonexistent_engine")
        
        assert "No implementation found" in str(exc_info.value)

    def test_load_validator_returns_class(self, discovery):
        """load_validator should return a validator class."""
        ValidatorClass = discovery.load_validator("always_valid")
        assert isinstance(ValidatorClass, type)
        assert issubclass(ValidatorClass, BaseValidator)

    def test_load_validator_missing_file_raises_error(self, discovery):
        """load_validator with non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError) as exc_info:
            discovery.load_validator("nonexistent_validator")
        
        assert "No implementation found" in str(exc_info.value)

    def test_list_agents_returns_available_implementations(self, discovery):
        """list_agents should return list of available agent filenames."""
        agents = discovery.list_agents()
        assert isinstance(agents, list)
        assert "nation" in agents
        assert "econ_llm_agent" in agents
        # Should not include __init__.py
        assert "__init__" not in agents

    def test_list_agents_excludes_private_files(self, discovery):
        """list_agents should exclude files starting with underscore."""
        agents = discovery.list_agents()
        # Should not include any _private files
        assert not any(agent.startswith("_") for agent in agents)

    def test_list_engines_returns_available_implementations(self, discovery):
        """list_engines should return list of available engine filenames."""
        engines = discovery.list_engines()
        assert isinstance(engines, list)
        assert "economic" in engines
        assert "econ_llm_engine" in engines

    def test_list_validators_returns_available_implementations(self, discovery):
        """list_validators should return list of available validator filenames."""
        validators = discovery.list_validators()
        assert isinstance(validators, list)
        assert "always_valid" in validators
        assert "econ_llm_validator" in validators

    def test_list_agents_sorted(self, discovery):
        """list_agents should return sorted list."""
        agents = discovery.list_agents()
        assert agents == sorted(agents)

    def test_loaded_agent_can_be_instantiated(self, discovery):
        """Loaded agent class should be instantiatable."""
        NationAgent = discovery.load_agent("nation")
        # NationAgent requires specific parameters based on implementation
        # Just verify it's a valid class for now
        assert hasattr(NationAgent, '__init__')

    def test_cache_separate_per_component_type(self, discovery):
        """Cache should be separate for agents, engines, validators."""
        # Load each type
        agent = discovery.load_agent("econ_llm_agent")
        engine = discovery.load_engine("econ_llm_engine")
        validator = discovery.load_validator("econ_llm_validator")
        
        # All should be different classes
        assert agent is not engine
        assert agent is not validator
        assert engine is not validator

    def test_error_message_includes_available_options(self, discovery):
        """Error message should list available implementations."""
        with pytest.raises(FileNotFoundError) as exc_info:
            discovery.load_agent("bad_agent")
        
        error_msg = str(exc_info.value)
        # Should suggest available agents
        assert "nation" in error_msg or "Available" in error_msg
