"""Atomic JSON file operations for Pydantic models."""

import os
import json
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel, ValidationError

from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError

T = TypeVar('T', bound=BaseModel)


class JSONStorage:
    """Atomic JSON file operations for Pydantic models."""

    @staticmethod
    def save_json(path: Path, data: BaseModel) -> None:
        """Save Pydantic model to JSON file atomically.

        Args:
            path: Target file path
            data: Pydantic model to serialize

        Raises:
            CheckpointSaveError: On I/O failure
        """
        try:
            # Ensure parent directory exists
            JSONStorage.ensure_directory(path.parent)

            # Write to temp file
            temp_path = Path(str(path) + ".tmp")
            json_data = data.model_dump_json(indent=2, exclude_none=False)

            with open(temp_path, 'w') as f:
                f.write(json_data)
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename
            temp_path.replace(path)

        except Exception as e:
            raise CheckpointSaveError(f"Failed to save to {path}: {e}") from e

    @staticmethod
    def load_json(path: Path, model: Type[T]) -> T:
        """Load and validate JSON file into Pydantic model.

        Args:
            path: Source file path
            model: Pydantic model class

        Returns:
            Validated model instance

        Raises:
            CheckpointLoadError: On file not found or validation error
        """
        try:
            if not path.exists():
                raise CheckpointLoadError(f"Checkpoint file not found: {path}")

            json_text = path.read_text()
            return model.model_validate_json(json_text)

        except FileNotFoundError as e:
            raise CheckpointLoadError(f"Checkpoint file not found: {path}") from e
        except json.JSONDecodeError as e:
            raise CheckpointLoadError(f"Invalid JSON in {path}: {e}") from e
        except ValidationError as e:
            raise CheckpointLoadError(f"Schema validation failed for {path}: {e}") from e
        except Exception as e:
            raise CheckpointLoadError(f"Failed to load {path}: {e}") from e

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Create directory and parents if needed.

        Args:
            path: Directory path

        Raises:
            CheckpointSaveError: On permission denied
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise CheckpointSaveError(f"Permission denied creating directory {path}") from e
        except Exception as e:
            raise CheckpointSaveError(f"Failed to create directory {path}: {e}") from e
