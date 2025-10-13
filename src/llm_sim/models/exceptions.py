"""Custom exceptions for the llm_sim models package."""

from typing import List


class ConfigValidationError(ValueError):
    """Raised when configuration validation fails."""

    pass


class SchemaCompatibilityError(ValueError):
    """Raised when checkpoint schema doesn't match current configuration schema."""

    pass


class ComplexTypeError(ValueError):
    """Raised when complex type validation fails."""

    pass


class CircularSchemaError(ValueError):
    """Raised when a circular reference is detected in schema definitions."""

    def __init__(self, cycle_path: List[str], field_path: List[str] | None = None):
        self.cycle_path = cycle_path
        self.field_path = field_path or []

        # Format cycle path
        cycle_str = " -> ".join(cycle_path)

        # Format field path (if available)
        if self.field_path:
            field_str = " -> ".join(
                f"{schema}.{field}" for schema, field in zip(cycle_path, self.field_path)
            )
            message = (
                f"Circular reference detected in schema definitions:\n"
                f"  Cycle: {cycle_str}\n"
                f"  Fields: {field_str}\n\n"
                f"Suggested fixes:\n"
                f"  1. Use Optional[ForwardRef] for back-references\n"
                f"  2. Use string IDs instead of nested objects\n"
                f"  3. Flatten the schema structure"
            )
        else:
            message = (
                f"Circular reference detected in schema definitions:\n"
                f"  Cycle: {cycle_str}\n\n"
                f"Suggested fixes:\n"
                f"  1. Use Optional[ForwardRef] for back-references\n"
                f"  2. Use string IDs instead of nested objects\n"
                f"  3. Flatten the schema structure"
            )

        super().__init__(message)


class DepthLimitError(ValueError):
    """Raised when nesting depth exceeds configured limits."""

    pass


def loc_to_dot_notation(loc: tuple[str | int, ...]) -> str:
    """Convert Pydantic error location tuple to dot notation.

    Examples:
        ('inventory', 'food') -> 'inventory.food'
        ('agents', 0, 'position') -> 'agents[0].position'
        ('nested', 'deeply', 1, 'field') -> 'nested.deeply[1].field'
    """
    path = ""
    for i, x in enumerate(loc):
        if isinstance(x, str):
            path += "." if i > 0 else ""
            path += x
        elif isinstance(x, int):
            path += f"[{x}]"
    return path


def format_validation_error(error_dict: dict) -> str:
    """Format validation error with clear field path.

    Args:
        error_dict: Pydantic error dict with 'loc' and 'msg' keys

    Returns:
        Formatted error message with dot notation path
    """
    field_path = loc_to_dot_notation(error_dict["loc"])
    msg = error_dict["msg"]
    return f"{field_path}: {msg}"
