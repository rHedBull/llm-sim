"""Integration tests for reorganized simulation structure.

These tests verify that the simulation runs correctly with the new
directory structure and discovery mechanism.
"""

import pytest
from pathlib import Path

from llm_sim.orchestrator import SimulationOrchestrator
from llm_sim.discovery import ComponentDiscovery
from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.patterns.llm_agent import LLMAgent


class TestReorganizedSimulation:
    """Test simulation with reorganized structure."""

    def test_simulation_runs_with_new_import_paths(self, tmp_path):
        """Simulation should run successfully with new infrastructure paths."""
        # Create a minimal YAML config
        config_content = """
simulation:
  name: "Test Simulation"
  max_turns: 2

agents:
  - name: "TestAgent1"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"
  interest_rate: 0.05

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text(config_content)
        
        # This will test if orchestrator can load from new paths
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file), output_root=tmp_path)
        
        # Verify components loaded correctly
        assert orchestrator is not None
        assert len(orchestrator.agents) == 1
        assert orchestrator.engine is not None
        assert orchestrator.validator is not None

    def test_mixed_agent_types(self, tmp_path):
        """Simulation should support mixing BaseAgent and LLMAgent extensions."""
        config_content = """
simulation:
  name: "Mixed Agents Test"
  max_turns: 1

agents:
  - name: "SimpleAgent"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

  - name: "LLMAgent"
    type: "econ_llm_agent"
    initial_economic_strength: 100

engine:
  type: "economic"
  interest_rate: 0.05

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "mixed_config.yaml"
        config_file.write_text(config_content)
        
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file), output_root=tmp_path)
        
        # Verify we have both types
        assert len(orchestrator.agents) == 2
        
        # Both should be BaseAgent instances
        assert all(isinstance(agent, BaseAgent) for agent in orchestrator.agents)

    def test_orchestrator_discovers_implementations_correctly(self):
        """Orchestrator should use discovery mechanism to find implementations."""
        implementations_root = Path(__file__).parent.parent.parent / "src" / "llm_sim"
        discovery = ComponentDiscovery(implementations_root)
        
        # Verify discovery finds all expected implementations
        agents = discovery.list_agents()
        assert "nation" in agents
        assert "econ_llm_agent" in agents
        
        engines = discovery.list_engines()
        assert "economic" in engines
        assert "econ_llm_engine" in engines
        
        validators = discovery.list_validators()
        assert "always_valid" in validators
        assert "econ_llm_validator" in validators

    def test_yaml_config_with_filename_references_works(self, tmp_path):
        """YAML config should work with filename-only references."""
        config_content = """
simulation:
  name: "Filename Test"
  max_turns: 1

agents:
  - name: "Agent1"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "filename_config.yaml"
        config_file.write_text(config_content)
        
        # Should load without errors
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file), output_root=tmp_path)
        assert orchestrator is not None

    def test_simulation_produces_expected_output(self, tmp_path):
        """Simulation should produce valid state updates."""
        config_content = """
simulation:
  name: "Output Test"
  max_turns: 2

agents:
  - name: "TestAgent"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"
  interest_rate: 0.05

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "output_config.yaml"
        config_file.write_text(config_content)
        
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file), output_root=tmp_path)
        
        # Run simulation
        result = orchestrator.run()
        final_state = result if hasattr(result, 'turn') else result['final_state']

        # Verify we got a final state
        assert final_state is not None
        assert final_state.turn >= 0
        assert "TestAgent" in final_state.agents
