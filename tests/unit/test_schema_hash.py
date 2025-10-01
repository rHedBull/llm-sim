"""Unit tests for schema hash computation.

These tests validate the compute_schema_hash() function.
These tests should FAIL until the function is implemented.
"""

import pytest
from llm_sim.models.config import VariableDefinition
from llm_sim.persistence.schema_hash import compute_schema_hash


class TestSchemaHashComputation:
    """Tests for schema hash computation."""

    def test_hash_is_deterministic(self):
        """Same input should produce same hash."""
        agent_vars = {
            "gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)
        }
        global_vars = {
            "inflation": VariableDefinition(type="float", min=-1.0, max=1.0, default=0.02)
        }

        hash1 = compute_schema_hash(agent_vars, global_vars)
        hash2 = compute_schema_hash(agent_vars, global_vars)

        assert hash1 == hash2

    def test_hash_is_order_independent(self):
        """Hash should be same regardless of dict key order."""
        agent_vars1 = {
            "gdp": VariableDefinition(type="float", default=1000.0),
            "population": VariableDefinition(type="int", default=1000000),
        }
        agent_vars2 = {
            "population": VariableDefinition(type="int", default=1000000),
            "gdp": VariableDefinition(type="float", default=1000.0),
        }
        global_vars = {}

        hash1 = compute_schema_hash(agent_vars1, global_vars)
        hash2 = compute_schema_hash(agent_vars2, global_vars)

        assert hash1 == hash2

    def test_different_schemas_produce_different_hashes(self):
        """Different schemas should produce different hashes."""
        agent_vars1 = {"gdp": VariableDefinition(type="float", default=1000.0)}
        agent_vars2 = {"population": VariableDefinition(type="int", default=1000000)}
        global_vars = {}

        hash1 = compute_schema_hash(agent_vars1, global_vars)
        hash2 = compute_schema_hash(agent_vars2, global_vars)

        assert hash1 != hash2

    def test_hash_format_is_64_char_hex(self):
        """Hash should be 64-character hex string (SHA-256)."""
        agent_vars = {"gdp": VariableDefinition(type="float", default=1000.0)}
        global_vars = {}

        hash_value = compute_schema_hash(agent_vars, global_vars)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_constraint_changes_affect_hash(self):
        """Changing constraints should change hash."""
        agent_vars1 = {
            "gdp": VariableDefinition(type="float", min=0, max=1000000, default=1000.0)
        }
        agent_vars2 = {
            "gdp": VariableDefinition(type="float", min=0, max=2000000, default=1000.0)
        }
        global_vars = {}

        hash1 = compute_schema_hash(agent_vars1, global_vars)
        hash2 = compute_schema_hash(agent_vars2, global_vars)

        assert hash1 != hash2

    def test_type_changes_affect_hash(self):
        """Changing variable type should change hash."""
        agent_vars1 = {"value": VariableDefinition(type="float", default=1000.0)}
        agent_vars2 = {"value": VariableDefinition(type="int", default=1000)}
        global_vars = {}

        hash1 = compute_schema_hash(agent_vars1, global_vars)
        hash2 = compute_schema_hash(agent_vars2, global_vars)

        assert hash1 != hash2

    def test_categorical_values_affect_hash(self):
        """Changing categorical values should change hash."""
        agent_vars1 = {
            "tech": VariableDefinition(
                type="categorical", values=["stone", "bronze"], default="stone"
            )
        }
        agent_vars2 = {
            "tech": VariableDefinition(
                type="categorical", values=["stone", "bronze", "iron"], default="stone"
            )
        }
        global_vars = {}

        hash1 = compute_schema_hash(agent_vars1, global_vars)
        hash2 = compute_schema_hash(agent_vars2, global_vars)

        assert hash1 != hash2

    def test_empty_schemas(self):
        """Empty schemas should produce valid hash."""
        agent_vars = {}
        global_vars = {}

        hash_value = compute_schema_hash(agent_vars, global_vars)

        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)
