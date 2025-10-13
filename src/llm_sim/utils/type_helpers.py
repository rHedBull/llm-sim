"""Type introspection and validation helpers for complex data types."""

from typing import Any, Optional, get_origin, get_args, Union
from pydantic import BaseModel
import structlog

from llm_sim.models.exceptions import DepthLimitError

logger = structlog.get_logger(__name__)

# Maximum nesting depths per spec
MAX_DICT_DEPTH = 4
MAX_LIST_DEPTH = 3
MAX_OVERALL_DEPTH = 10


def get_type_annotation(var_def: "VariableDefinition") -> type:  # noqa: F821
    """Convert VariableDefinition to Python type annotation.

    Args:
        var_def: Variable definition from config

    Returns:
        Python type annotation for the variable
    """
    # Import here to avoid circular dependency
    from llm_sim.models.config import VariableDefinition  # noqa: F401
    from typing import Literal

    # Scalar types (existing)
    if var_def.type == "float":
        return float
    elif var_def.type == "int":
        return int
    elif var_def.type == "bool":
        return bool
    elif var_def.type == "categorical":
        return str

    # Complex types
    elif var_def.type == "dict":
        if var_def.schema:
            # Fixed schema mode - will be handled by create_nested_model_from_schema
            return dict  # Placeholder, actual type created in state.py
        else:
            # Dynamic keys mode
            key_type = str if var_def.key_type == "str" else int
            value_type = _resolve_value_type(var_def.value_type)
            return dict[key_type, value_type]

    elif var_def.type == "list":
        item_type = _resolve_value_type(var_def.item_type)
        return list[item_type]

    elif var_def.type == "tuple":
        if var_def.item_types:
            element_types = [_resolve_value_type(t) for t in var_def.item_types]
            return tuple[tuple(element_types)]  # type: ignore
        return tuple

    elif var_def.type == "str":
        return str

    elif var_def.type == "object":
        # Will be handled by create_nested_model_from_schema
        return dict  # Placeholder

    else:
        raise ValueError(f"Unsupported type: {var_def.type}")


def _resolve_value_type(value_type: Any) -> type:
    """Resolve a value_type specification to a Python type.

    Args:
        value_type: Either a string type name or a VariableDefinition

    Returns:
        Python type annotation
    """
    from llm_sim.models.config import VariableDefinition

    if isinstance(value_type, str):
        # String type name
        type_map = {
            "float": float,
            "int": int,
            "bool": bool,
            "str": str,
        }
        return type_map.get(value_type, str)
    elif isinstance(value_type, VariableDefinition):
        # Nested VariableDefinition
        return get_type_annotation(value_type)
    else:
        return str  # Fallback


def introspect_type(annotation: type) -> dict[str, Any]:
    """Extract structure information from a type annotation.

    Args:
        annotation: Type annotation to introspect

    Returns:
        Dict with keys: 'origin', 'args', 'is_model', 'is_union', 'is_optional'
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    info = {
        "origin": origin,
        "args": args,
        "is_model": isinstance(annotation, type)
        and issubclass(annotation, BaseModel),  # type: ignore
        "is_union": origin is Union,
        "is_optional": origin is Union and type(None) in args,
    }

    return info


def unwrap_optional(field_type: type) -> type:
    """Remove Optional wrapper from a type annotation.

    Examples:
        Optional[int] -> int
        Union[int, None] -> int
        int -> int (unchanged)

    Args:
        field_type: Type annotation to unwrap

    Returns:
        Unwrapped type annotation
    """
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union:
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]

    return field_type


def check_nesting_depth(
    field_type: type,
    current_depth: int,
    max_depth: int,
    field_path: str,
    container_type: str,  # 'dict' or 'list'
) -> None:
    """Recursively check nesting depth of complex types.

    Args:
        field_type: Type to check (may be generic like dict[str, dict[str, int]])
        current_depth: Current depth level (starts at 0)
        max_depth: Maximum allowed depth
        field_path: Dot-notation path for error reporting
        container_type: 'dict' or 'list' to track separately

    Raises:
        DepthLimitError: If nesting exceeds max_depth
    """
    if current_depth > max_depth:
        raise DepthLimitError(
            f"Nesting depth exceeds limit for {container_type} at '{field_path}': "
            f"{current_depth} > {max_depth}"
        )

    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is dict:
        # Check dict nesting depth
        if container_type == "dict" or current_depth == 0:
            # dict[str, T] - recurse into value type
            if len(args) >= 2:
                check_nesting_depth(
                    args[1],
                    current_depth + 1,
                    max_depth,
                    f"{field_path}.<value>",
                    "dict",
                )

    elif origin is list or origin is tuple:
        # Check list/tuple nesting depth
        if container_type == "list" or current_depth == 0:
            # list[T] - recurse into item type
            if args:
                item_type = (
                    args[0]
                    if origin is list
                    else args[0]
                    if len(args) == 2 and args[1] is ...
                    else None
                )
                if item_type:
                    check_nesting_depth(
                        item_type,
                        current_depth + 1,
                        max_depth,
                        f"{field_path}[*]",
                        "list",
                    )

    elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
        # Nested model - check its fields
        for field_name, field_info in field_type.model_fields.items():
            check_nesting_depth(
                field_info.annotation,
                current_depth,  # Don't increment for object nesting, only for collections
                max_depth,
                f"{field_path}.{field_name}",
                container_type,
            )


def detect_schema_cycle(
    schema_name: str,
    schema_graph: dict[str, list[str]],
    visited: set[str],
    rec_stack: set[str],
    path: list[str],
) -> Optional[list[str]]:
    """Detect cycles in schema dependency graph using DFS.

    Args:
        schema_name: Current schema being explored
        schema_graph: Dict mapping schema names to their dependencies
        visited: Set of all visited schemas
        rec_stack: Set of schemas in current recursion stack
        path: Current path for cycle reporting

    Returns:
        List of schema names forming the cycle, or None if no cycle
    """
    visited.add(schema_name)
    rec_stack.add(schema_name)
    path.append(schema_name)

    # Explore dependencies
    for dependency in schema_graph.get(schema_name, []):
        if dependency not in visited:
            cycle = detect_schema_cycle(dependency, schema_graph, visited, rec_stack, path)
            if cycle:
                return cycle
        elif dependency in rec_stack:
            # Back edge found - cycle detected
            cycle_start = path.index(dependency)
            return path[cycle_start:] + [dependency]

    # Backtrack
    rec_stack.remove(schema_name)
    path.pop()
    return None
