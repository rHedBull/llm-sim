"""Custom exceptions for the llm_sim models package."""


class ConfigValidationError(ValueError):
    """Raised when configuration validation fails."""

    pass


class SchemaCompatibilityError(ValueError):
    """Raised when checkpoint schema doesn't match current configuration schema."""

    pass
