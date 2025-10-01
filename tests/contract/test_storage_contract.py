"""Contract tests for JSONStorage."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import BaseModel

from llm_sim.persistence.storage import JSONStorage
from llm_sim.persistence.exceptions import CheckpointSaveError, CheckpointLoadError


class TestModel(BaseModel):
    """Test model for serialization."""

    turn: int
    value: str


def test_save_json_uses_atomic_write(tmp_path):
    """Test save_json uses temp file + rename pattern."""
    target = tmp_path / "test.json"
    data = TestModel(turn=5, value="test")

    with patch.object(Path, "replace") as mock_replace:
        JSONStorage.save_json(target, data)
        mock_replace.assert_called_once()


def test_load_json_returns_validated_model(tmp_path):
    """Test load_json returns validated Pydantic model."""
    path = tmp_path / "test.json"
    original = TestModel(turn=5, value="test")

    JSONStorage.save_json(path, original)
    loaded = JSONStorage.load_json(path, TestModel)

    assert isinstance(loaded, TestModel)
    assert loaded.turn == 5
    assert loaded.value == "test"


def test_load_json_raises_on_missing_file(tmp_path):
    """Test load_json raises CheckpointLoadError on missing file."""
    with pytest.raises(CheckpointLoadError, match="not found"):
        JSONStorage.load_json(tmp_path / "missing.json", TestModel)


def test_load_json_raises_on_invalid_json(tmp_path):
    """Test load_json raises CheckpointLoadError on invalid JSON."""
    path = tmp_path / "invalid.json"
    path.write_text("{ invalid json }")

    with pytest.raises(CheckpointLoadError):
        JSONStorage.load_json(path, TestModel)


def test_load_json_raises_on_schema_mismatch(tmp_path):
    """Test load_json raises CheckpointLoadError on schema mismatch."""
    path = tmp_path / "bad_schema.json"
    path.write_text('{"wrong_field": 123}')

    with pytest.raises(CheckpointLoadError):
        JSONStorage.load_json(path, TestModel)


def test_ensure_directory_creates_parents(tmp_path):
    """Test ensure_directory creates parent directories."""
    deep_path = tmp_path / "a" / "b" / "c"

    JSONStorage.ensure_directory(deep_path)

    assert deep_path.exists()
    assert deep_path.is_dir()


def test_ensure_directory_is_idempotent(tmp_path):
    """Test ensure_directory can be called multiple times."""
    path = tmp_path / "test_dir"

    JSONStorage.ensure_directory(path)
    JSONStorage.ensure_directory(path)  # Should not raise

    assert path.exists()


def test_ensure_directory_raises_on_permission_denied(tmp_path):
    """Test ensure_directory raises CheckpointSaveError on permission denied."""
    # Make parent read-only
    tmp_path.chmod(0o444)

    with pytest.raises(CheckpointSaveError, match="Permission denied"):
        JSONStorage.ensure_directory(tmp_path / "new_dir")

    # Cleanup
    tmp_path.chmod(0o755)
