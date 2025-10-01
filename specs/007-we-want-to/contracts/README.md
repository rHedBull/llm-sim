# Contracts: Abstract Agent and Global State System

**Feature**: Dynamic variable system for simulation state
**Date**: 2025-10-01

## Overview
This directory contains JSON Schema contracts that define the structure and validation rules for configuration files and checkpoint files in the abstract state variable system.

## Schemas

### 1. config-schema.json
**Purpose**: Validates the `state_variables` section of YAML simulation configs

**Validates**:
- Variable definition structure
- Type constraints (float, int, bool, categorical)
- Required fields per type
- Default value type matching

**Example Valid Config**:
```yaml
state_variables:
  agent_vars:
    gdp:
      type: float
      min: 0
      max: 1000000
      default: 1000.0
    tech_level:
      type: categorical
      values: [bronze, iron, steel]
      default: bronze
  global_vars:
    open_economy:
      type: bool
      default: true
```

**Example Invalid Config**:
```yaml
state_variables:
  agent_vars:
    gdp:
      type: unsupported_type  # ❌ Invalid: type must be float/int/bool/categorical
      default: 1000
    population:
      type: categorical
      # ❌ Invalid: missing required 'values' field for categorical
      default: "large"
```

**Usage in Tests**:
```python
import json
from jsonschema import validate, ValidationError

def test_config_schema_validation():
    with open('contracts/config-schema.json') as f:
        schema = json.load(f)

    # Valid config
    config = {
        "state_variables": {
            "agent_vars": {
                "gdp": {"type": "float", "min": 0, "default": 1000.0}
            },
            "global_vars": {
                "inflation": {"type": "float", "default": 0.02}
            }
        }
    }
    validate(instance=config, schema=schema)  # Should pass

    # Invalid config
    bad_config = {
        "state_variables": {
            "agent_vars": {
                "score": {"type": "complex", "default": 0}  # Invalid type
            },
            "global_vars": {}
        }
    }
    with pytest.raises(ValidationError):
        validate(instance=bad_config, schema=schema)
```

---

### 2. checkpoint-schema.json
**Purpose**: Validates checkpoint file structure with schema metadata

**Validates**:
- Metadata structure including `schema_hash` field
- State structure (turn, agents, global_state)
- schema_hash format (64-char hex SHA-256)

**Example Valid Checkpoint**:
```json
{
  "metadata": {
    "run_id": "abc123",
    "turn": 50,
    "timestamp": "2025-10-01T10:30:00Z",
    "schema_hash": "a3f2d1e4c5b6a7f8d9e0c1b2a3f4d5e6c7b8a9f0e1d2c3b4a5f6e7d8c9f0a1b2"
  },
  "state": {
    "turn": 50,
    "agents": {
      "Nation_A": {
        "name": "Nation_A",
        "gdp": 5000.0,
        "population": 1500000
      },
      "Nation_B": {
        "name": "Nation_B",
        "gdp": 7500.0,
        "population": 2000000
      }
    },
    "global_state": {
      "inflation": 0.03,
      "open_economy": true
    },
    "reasoning_chains": []
  }
}
```

**Example Invalid Checkpoint**:
```json
{
  "metadata": {
    "run_id": "abc123",
    "turn": 50,
    "timestamp": "2025-10-01T10:30:00Z",
    "schema_hash": "invalid"  // ❌ Invalid: must be 64-char hex
  },
  "state": {
    "turn": 50,
    // ❌ Invalid: missing required 'agents' field
    "global_state": {}
  }
}
```

**Usage in Tests**:
```python
def test_checkpoint_schema_validation():
    with open('contracts/checkpoint-schema.json') as f:
        schema = json.load(f)

    # Valid checkpoint
    checkpoint = {
        "metadata": {
            "run_id": "test123",
            "turn": 10,
            "timestamp": "2025-10-01T10:00:00Z",
            "schema_hash": "a" * 64  # Valid 64-char hex
        },
        "state": {
            "turn": 10,
            "agents": {"A": {"name": "A"}},
            "global_state": {},
            "reasoning_chains": []
        }
    }
    validate(instance=checkpoint, schema=schema)  # Should pass

    # Invalid checkpoint (missing schema_hash)
    bad_checkpoint = {
        "metadata": {
            "run_id": "test123",
            "turn": 10,
            "timestamp": "2025-10-01T10:00:00Z"
            # Missing schema_hash
        },
        "state": {"turn": 10, "agents": {}, "global_state": {}}
    }
    with pytest.raises(ValidationError):
        validate(instance=bad_checkpoint, schema=schema)
```

---

## Testing Strategy

### Contract Tests
Each schema should have dedicated contract tests that verify:

1. **Valid examples pass**: Multiple valid configurations/checkpoints
2. **Invalid examples fail**: Each validation rule tested with failing cases
3. **Edge cases**: Empty dicts, boundary values, optional fields

### Test Organization
```
tests/contract/
├── test_config_schema.py       # Tests for config-schema.json
└── test_checkpoint_schema.py   # Tests for checkpoint-schema.json
```

### Example Test Structure
```python
# tests/contract/test_config_schema.py
import pytest
from jsonschema import validate, ValidationError

class TestConfigSchema:
    @pytest.fixture
    def schema(self):
        with open('specs/007-we-want-to/contracts/config-schema.json') as f:
            return json.load(f)

    def test_valid_float_variable(self, schema):
        """Float variable with min/max should validate"""
        config = {
            "state_variables": {
                "agent_vars": {
                    "gdp": {"type": "float", "min": 0, "max": 1e6, "default": 1000}
                },
                "global_vars": {}
            }
        }
        validate(instance=config, schema=schema)

    def test_invalid_type_rejected(self, schema):
        """Unsupported type should fail validation"""
        config = {
            "state_variables": {
                "agent_vars": {
                    "score": {"type": "complex", "default": 0}
                },
                "global_vars": {}
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)

    def test_categorical_requires_values(self, schema):
        """Categorical type must have 'values' field"""
        config = {
            "state_variables": {
                "agent_vars": {
                    "level": {"type": "categorical", "default": "high"}
                    # Missing 'values'
                },
                "global_vars": {}
            }
        }
        with pytest.raises(ValidationError):
            validate(instance=config, schema=schema)
```

---

## Schema Evolution

### Adding New Variable Types
To add a new variable type (e.g., "string"):

1. Update `config-schema.json`:
   ```json
   "type": {
     "enum": ["float", "int", "bool", "categorical", "string"]
   }
   ```

2. Add type-specific validation rules in `allOf` section

3. Update contract tests with examples

4. Update data-model.md and implementation

### Breaking Changes
Changes that affect schema_hash computation:
- Adding/removing variable types
- Changing constraint semantics
- Modifying schema structure

These require version coordination between config and checkpoint schemas.

---

## References
- JSON Schema Specification: https://json-schema.org/
- Data Model: `../data-model.md`
- Feature Spec: `../spec.md`

---

*Contracts complete - ready for implementation*
