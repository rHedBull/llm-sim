# Contract: JSONStorage

**Component**: `src/llm_sim/persistence/storage.py`
**Purpose**: Atomic JSON file operations
**Type**: Low-level utility

## Interface

```python
from pathlib import Path
from typing import TypeVar, Type
from pydantic import BaseModel

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
        ...

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
        ...

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Create directory and parents if needed.

        Args:
            path: Directory path

        Raises:
            CheckpointSaveError: On permission denied
        """
        ...
```

## Contract Tests

**File**: `tests/contract/test_storage_contract.py`

### Test 1: Atomic Write Pattern
```python
def test_save_json_atomic(tmp_path):
    """Uses temp file + rename for atomic writes."""
    target = tmp_path / "test.json"
    data = create_test_model()

    # Mock rename to verify temp file used
    with patch('pathlib.Path.replace') as mock_replace:
        JSONStorage.save_json(target, data)
        mock_replace.assert_called_once()
        # Verify temp file argument
        args = mock_replace.call_args[0]
        assert str(args[0]).endswith('.tmp')
```

### Test 2: Save and Load Roundtrip
```python
def test_save_load_roundtrip(tmp_path):
    """Saved data can be loaded back."""
    path = tmp_path / "test.json"
    original = SimulationState(turn=5, agents={}, global_state={...})

    JSONStorage.save_json(path, original)
    loaded = JSONStorage.load_json(path, SimulationState)

    assert loaded.turn == original.turn
```

### Test 3: Load Raises on Missing File
```python
def test_load_json_missing_file(tmp_path):
    """Raises CheckpointLoadError when file not found."""
    with pytest.raises(CheckpointLoadError, match="not found"):
        JSONStorage.load_json(tmp_path / "missing.json", SimulationState)
```

### Test 4: Load Raises on Invalid JSON
```python
def test_load_json_invalid(tmp_path):
    """Raises CheckpointLoadError on JSON decode error."""
    path = tmp_path / "invalid.json"
    path.write_text("{ invalid }")

    with pytest.raises(CheckpointLoadError):
        JSONStorage.load_json(path, SimulationState)
```

### Test 5: Load Raises on Schema Mismatch
```python
def test_load_json_validation_error(tmp_path):
    """Raises CheckpointLoadError on Pydantic validation failure."""
    path = tmp_path / "bad_schema.json"
    path.write_text('{"wrong_field": 123}')

    with pytest.raises(CheckpointLoadError):
        JSONStorage.load_json(path, SimulationState)
```

### Test 6: Ensure Directory Creates Parents
```python
def test_ensure_directory_creates_parents(tmp_path):
    """Creates parent directories as needed."""
    deep_path = tmp_path / "a" / "b" / "c"

    JSONStorage.ensure_directory(deep_path)

    assert deep_path.exists()
    assert deep_path.is_dir()
```

### Test 7: Ensure Directory Idempotent
```python
def test_ensure_directory_idempotent(tmp_path):
    """Can be called multiple times safely."""
    path = tmp_path / "test_dir"

    JSONStorage.ensure_directory(path)
    JSONStorage.ensure_directory(path)  # Should not raise

    assert path.exists()
```

### Test 8: Ensure Directory Raises on Permission Denied
```python
def test_ensure_directory_permission_denied(tmp_path):
    """Raises CheckpointSaveError on permission denied."""
    # Make parent read-only
    tmp_path.chmod(0o444)

    with pytest.raises(CheckpointSaveError, match="Permission denied"):
        JSONStorage.ensure_directory(tmp_path / "new_dir")
```

## Behavior Specifications

- **Atomicity**: Uses `temp_file.replace(target)` pattern
- **Serialization**: Pydantic's `model_dump_json(indent=2)`
- **Deserialization**: Pydantic's `model_validate_json()`
- **Error Conversion**: All errors → CheckpointSaveError or CheckpointLoadError
- **fsync**: Explicitly syncs temp file before rename
