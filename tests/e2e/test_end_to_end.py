"""End-to-end tests focusing on CLI and full system integration."""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml


class TestCLIEndToEnd:
    """End-to-end tests for the CLI interface."""

    def test_cli_with_example_config(self) -> None:
        """Test running the CLI with an example configuration."""
        result = subprocess.run(
            ["python", "main.py", "examples/quick_test.yaml"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "=== Simulation Complete ===" in result.stdout
        assert "Final Turn: 5" in result.stdout
        assert "TestNation:" in result.stdout
        assert "Validation Statistics:" in result.stdout
        assert "100.00%" in result.stdout  # Acceptance rate

    def test_cli_with_json_output(self) -> None:
        """Test CLI with JSON output to file."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                ["python", "main.py", "examples/quick_test.yaml", "--output", output_path],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0
            assert f"Results saved to: {output_path}" in result.stdout

            # Verify JSON file was created and is valid
            with open(output_path) as f:
                data = json.load(f)

            assert "final_state" in data
            assert "stats" in data
            assert data["final_state"]["turn"] == 5
            assert "TestNation" in data["final_state"]["agents"]

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_cli_with_history_output(self) -> None:
        """Test CLI with history output enabled."""
        result = subprocess.run(
            ["python", "main.py", "examples/quick_test.yaml", "--print-history"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "=== State History ===" in result.stdout
        assert "Turn 0:" in result.stdout
        assert "Turn 1:" in result.stdout
        assert "Turn 5:" in result.stdout

    def test_cli_error_handling(self) -> None:
        """Test CLI error handling for invalid inputs."""
        # Test with non-existent file
        result = subprocess.run(
            ["python", "main.py", "nonexistent.yaml"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 1
        assert "not found" in result.stderr

    def test_cli_with_debug_flag(self) -> None:
        """Test CLI with debug flag enabled."""
        result = subprocess.run(
            ["python", "main.py", "examples/quick_test.yaml", "--debug"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "Loading configuration from:" in result.stdout
        assert "Simulation name:" in result.stdout
        assert "Max turns:" in result.stdout
        assert "Number of agents:" in result.stdout

    def test_cli_with_all_flags(self) -> None:
        """Test CLI with multiple flags combined."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output_path = f.name

        try:
            result = subprocess.run(
                [
                    "python",
                    "main.py",
                    "examples/quick_test.yaml",
                    "--debug",
                    "--print-history",
                    "--output",
                    output_path,
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0
            # Check debug output
            assert "Loading configuration from:" in result.stdout
            # Check history output
            assert "=== State History ===" in result.stdout
            # Check completion
            assert "=== Simulation Complete ===" in result.stdout
            # Check file saved
            assert f"Results saved to: {output_path}" in result.stdout

            # Verify JSON file
            with open(output_path) as f:
                data = json.load(f)
            assert data["history"] is not None  # History included with --print-history

        finally:
            Path(output_path).unlink(missing_ok=True)


class TestSystemEndToEnd:
    """End-to-end tests for complete system scenarios."""

    def test_basic_economic_example(self) -> None:
        """Test the basic economic example configuration."""
        result = subprocess.run(
            ["python", "main.py", "examples/basic_economic.yaml"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,  # Prevent hanging on large simulations
        )

        assert result.returncode == 0
        assert "Final Turn: 100" in result.stdout
        assert "Nation_A:" in result.stdout
        assert "Nation_B:" in result.stdout
        # Check that economy grew
        assert "Total Economic Value:" in result.stdout

    def test_extended_test_example(self) -> None:
        """Test the extended test example with multiple nations."""
        result = subprocess.run(
            ["python", "main.py", "examples/extended_test.yaml"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )

        assert result.returncode == 0
        assert "Nation_Alpha:" in result.stdout
        assert "Nation_Beta:" in result.stdout
        assert "Nation_Gamma:" in result.stdout
        assert "Nation_Delta:" in result.stdout

    def test_invalid_yaml_handling(self) -> None:
        """Test handling of invalid YAML configuration."""
        invalid_yaml = """
simulation:
  name: Invalid Test
  max_turns: -5  # Invalid: negative turns
engine:
  type: economic
  interest_rate: 2.5  # Invalid: > 1.0
agents:
  - name: Test
    type: nation
    initial_economic_strength: -100  # Potentially invalid
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(invalid_yaml)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", "main.py", temp_path],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 1
            assert "Error" in result.stderr or "error" in result.stderr

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_custom_yaml_configuration(self) -> None:
        """Test creating and running a custom YAML configuration."""
        custom_config = {
            "simulation": {
                "name": "Custom E2E Test",
                "max_turns": 15,
                "termination": {"min_value": 500.0, "max_value": 20000.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.07},
            "agents": [
                {"name": "TestCountry1", "type": "nation", "initial_economic_strength": 2000.0},
                {"name": "TestCountry2", "type": "nation", "initial_economic_strength": 3000.0},
                {"name": "TestCountry3", "type": "nation", "initial_economic_strength": 2500.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "WARNING", "format": "console"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(custom_config, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", "main.py", temp_path],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0
            assert "Final Turn: 15" in result.stdout
            assert "TestCountry1:" in result.stdout
            assert "TestCountry2:" in result.stdout
            assert "TestCountry3:" in result.stdout

            # Verify all 3 agents ran for all turns
            assert "Total Validated: 45" in result.stdout  # 3 agents * 15 turns

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_early_termination_via_cli(self) -> None:
        """Test early termination conditions work via CLI."""
        # Config with very high growth that should trigger max value termination
        config = {
            "simulation": {
                "name": "Early Termination Test",
                "max_turns": 100,
                "termination": {"max_value": 1500.0},
            },
            "engine": {"type": "economic", "interest_rate": 0.5},  # 50% growth
            "agents": [
                {"name": "FastGrower", "type": "nation", "initial_economic_strength": 1000.0},
            ],
            "validator": {"type": "always_valid"},
            "logging": {"level": "ERROR", "format": "json"},  # Minimize output
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", "main.py", temp_path],
                capture_output=True,
                text=True,
                check=False,
            )

            assert result.returncode == 0
            # Should terminate early, not reach 100 turns
            output_lines = result.stdout.strip().split("\n")
            final_turn_line = [l for l in output_lines if "Final Turn:" in l][0]
            final_turn = int(final_turn_line.split("Final Turn:")[1].strip())
            assert final_turn < 100
            assert final_turn > 0

        finally:
            Path(temp_path).unlink(missing_ok=True)