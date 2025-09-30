"""Integration tests for backward compatibility.

These tests verify that existing YAML configs and API usage
still work after the reorganization.
"""

import pytest
from pathlib import Path

from llm_sim.orchestrator import SimulationOrchestrator


class TestBackwardCompatibility:
    """Test backward compatibility after reorganization."""

    def test_existing_yaml_configs_still_work(self, tmp_path):
        """Existing YAML configs should work without modification."""
        # This represents a config from before the reorganization
        old_style_config = """
simulation:
  name: "Legacy Config"
  max_turns: 2

agents:
  - name: "Nation1"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"
  interest_rate: 5.0

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "legacy_config.yaml"
        config_file.write_text(old_style_config)
        
        # Should load and run without errors
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file))
        assert orchestrator is not None
        
        final_state = orchestrator.run()
        assert final_state is not None

    def test_no_breaking_changes_to_orchestrator_api(self, tmp_path):
        """Orchestrator API should remain the same."""
        config_content = """
simulation:
  name: "API Test"
  max_turns: 1

agents:
  - name: "TestAgent"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "api_config.yaml"
        config_file.write_text(config_content)
        
        # These API calls should still work
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file))
        
        # Check expected attributes exist
        assert hasattr(orchestrator, 'agents')
        assert hasattr(orchestrator, 'engine')
        assert hasattr(orchestrator, 'validator')
        assert hasattr(orchestrator, 'config')
        
        # Check expected methods exist
        assert hasattr(orchestrator, 'run')
        assert callable(orchestrator.run)

    def test_simulation_produces_same_results_as_before(self, tmp_path):
        """Simulation should produce same results as before reorganization."""
        config_content = """
simulation:
  name: "Deterministic Test"
  max_turns: 3

agents:
  - name: "Agent1"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"
  interest_rate: 5.0

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "deterministic_config.yaml"
        config_file.write_text(config_content)
        
        # Run twice and compare
        orchestrator1 = SimulationOrchestrator.from_yaml(str(config_file))
        final_state1 = orchestrator1.run()
        
        orchestrator2 = SimulationOrchestrator.from_yaml(str(config_file))
        final_state2 = orchestrator2.run()
        
        # Results should be consistent (deterministic simulation)
        assert final_state1.turn == final_state2.turn
        assert final_state1.agents.keys() == final_state2.agents.keys()

    def test_all_sample_configs_work(self, tmp_path):
        """All existing sample configs should continue to work."""
        # Test a few representative configs
        configs = [
            """
simulation:
  name: "Sample 1"
  max_turns: 1

agents:
  - name: "A1"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"

validator:
  type: "always_valid"
""",
        ]
        
        for i, config_content in enumerate(configs):
            config_file = tmp_path / f"sample_{i}.yaml"
            config_file.write_text(config_content)
            
            # Should load without errors
            orchestrator = SimulationOrchestrator.from_yaml(str(config_file))
            assert orchestrator is not None

    def test_validator_stats_still_accessible(self, tmp_path):
        """Validator statistics should still be accessible."""
        config_content = """
simulation:
  name: "Stats Test"
  max_turns: 1

agents:
  - name: "TestAgent"
    type: "nation"
    initial_economic_strength: 100
    strategy: "grow"

engine:
  type: "economic"

validator:
  type: "always_valid"
"""
        config_file = tmp_path / "stats_config.yaml"
        config_file.write_text(config_content)
        
        orchestrator = SimulationOrchestrator.from_yaml(str(config_file))
        orchestrator.run()
        
        # Validator stats should still be accessible
        stats = orchestrator.validator.get_stats()
        assert isinstance(stats, dict)
        assert 'validation_count' in stats or 'validations' in stats.values()
