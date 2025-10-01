"""Custom exceptions for persistence operations."""


class CheckpointError(Exception):
    """Base exception for checkpoint operations."""

    pass


class CheckpointSaveError(CheckpointError):
    """Raised when checkpoint save operation fails."""

    pass


class CheckpointLoadError(CheckpointError):
    """Raised when checkpoint load operation fails."""

    pass


class RunIDCollisionError(CheckpointError):
    """Raised when run ID collision cannot be resolved."""

    pass


class SchemaCompatibilityError(CheckpointError):
    """Raised when checkpoint schema_hash doesn't match current config."""

    pass
