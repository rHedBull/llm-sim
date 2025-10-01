"""Contract tests for checkpoint schema validation.

These tests validate the checkpoint file schema with schema_hash metadata.
They test the JSON schema from specs/007-we-want-to/contracts/checkpoint-schema.json
"""

import json
import pytest
from jsonschema import validate, ValidationError
from pathlib import Path


@pytest.fixture
def schema():
    """Load the checkpoint JSON schema."""
    schema_path = Path("specs/007-we-want-to/contracts/checkpoint-schema.json")
    with open(schema_path) as f:
        return json.load(f)


class TestValidCheckpoints:
    """Tests for valid checkpoint structures that should pass validation."""

    def test_valid_checkpoint_with_schema_hash_passes(self, schema):
        """Valid checkpoint with schema_hash should validate."""
        checkpoint = {
            "metadata": {
                "run_id": "abc123",
                "turn": 50,
                "timestamp": "2025-10-01T10:30:00Z",
                "schema_hash": "a" * 64,  # Valid 64-char hex
            },
            "state": {
                "turn": 50,
                "agents": {
                    "Nation_A": {"name": "Nation_A", "gdp": 5000.0},
                    "Nation_B": {"name": "Nation_B", "gdp": 7500.0},
                },
                "global_state": {"inflation": 0.03},
                "reasoning_chains": [],
            },
        }
        validate(instance=checkpoint, schema=schema)

    def test_valid_schema_hash_format(self, schema):
        """SHA-256 hash (64 hex chars) should validate."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "a3f2d1e4c5b6a7f8d9e0c1b2a3f4d5e6c7b8a9f0e1d2c3b4a5f6e7d8c9f0a1b2",
            },
            "state": {
                "turn": 10,
                "agents": {"A": {"name": "A"}},
                "global_state": {},
                "reasoning_chains": [],
            },
        }
        validate(instance=checkpoint, schema=schema)

    def test_empty_reasoning_chains(self, schema):
        """Checkpoint with empty reasoning chains should validate."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 0,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "0" * 64,
            },
            "state": {
                "turn": 0,
                "agents": {},
                "global_state": {},
                "reasoning_chains": [],
            },
        }
        validate(instance=checkpoint, schema=schema)


class TestInvalidCheckpoints:
    """Tests for invalid checkpoints that should fail validation."""

    def test_missing_schema_hash_rejected(self, schema):
        """Checkpoint without schema_hash should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                # Missing schema_hash
            },
            "state": {
                "turn": 10,
                "agents": {},
                "global_state": {},
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)

    def test_invalid_schema_hash_format_rejected(self, schema):
        """Schema hash with invalid format should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "invalid_hash",  # Not 64 hex chars
            },
            "state": {
                "turn": 10,
                "agents": {},
                "global_state": {},
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)

    def test_short_schema_hash_rejected(self, schema):
        """Schema hash with wrong length should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "abc123",  # Too short
            },
            "state": {
                "turn": 10,
                "agents": {},
                "global_state": {},
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)

    def test_missing_agents_rejected(self, schema):
        """Checkpoint without agents field should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "a" * 64,
            },
            "state": {
                "turn": 10,
                # Missing agents
                "global_state": {},
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)

    def test_missing_global_state_rejected(self, schema):
        """Checkpoint without global_state field should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "a" * 64,
            },
            "state": {
                "turn": 10,
                "agents": {},
                # Missing global_state
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)

    def test_agent_without_name_rejected(self, schema):
        """Agent state without 'name' field should be rejected."""
        checkpoint = {
            "metadata": {
                "run_id": "test123",
                "turn": 10,
                "timestamp": "2025-10-01T10:00:00Z",
                "schema_hash": "a" * 64,
            },
            "state": {
                "turn": 10,
                "agents": {"A": {"gdp": 1000}},  # Missing 'name' field
                "global_state": {},
            },
        }
        with pytest.raises(ValidationError):
            validate(instance=checkpoint, schema=schema)
