"""Schema hash computation for checkpoint compatibility validation."""

import hashlib
import json
from typing import Dict

from llm_sim.models.config import VariableDefinition


def compute_schema_hash(
    agent_vars: Dict[str, VariableDefinition], global_vars: Dict[str, VariableDefinition]
) -> str:
    """Compute deterministic hash of variable schema for checkpoint compatibility.

    Args:
        agent_vars: Agent variable definitions
        global_vars: Global variable definitions

    Returns:
        64-character hex string (SHA-256 hash)
    """
    # Build schema dict with sorted keys for determinism
    schema = {
        "agent_vars": {
            name: {
                "type": vd.type,
                "min": vd.min,
                "max": vd.max,
                "values": vd.values,
            }
            for name, vd in sorted(agent_vars.items())
        },
        "global_vars": {
            name: {
                "type": vd.type,
                "min": vd.min,
                "max": vd.max,
                "values": vd.values,
            }
            for name, vd in sorted(global_vars.items())
        },
    }

    # Serialize to JSON with sorted keys
    schema_json = json.dumps(schema, sort_keys=True)

    # Compute SHA-256 hash
    return hashlib.sha256(schema_json.encode()).hexdigest()
