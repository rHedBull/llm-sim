# llm_sim Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-06

## Active Technologies
- Python 3.12 + Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama Python client (new), httpx (for async LLM calls) (004-new-feature-i)
- Python 3.12 + Pydantic 2.x, PyYAML 6.x, structlog 24.x, ollama, httpx (005-we-want-to)
- File system (YAML configs, Python modules) (005-we-want-to)
- Python 3.12 + Pydantic 2.x (serialization), PyYAML 6.x (config), structlog 24.x (logging) (006-persistent-storage-specifically)
- File system (JSON files in `output/` directory) (006-persistent-storage-specifically)
- Python 3.12 + Pydantic 2.x (data modeling), PyYAML 6.x (config parsing), structlog 24.x (logging) (007-we-want-to)
- File system (JSON checkpoint files in `output/` directory) (007-we-want-to)
- Python 3.12 + Pydantic 2.x (data models), PyYAML 6.x (config), structlog 24.x (logging) (009-dynamic-agent-management)
- Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), httpx (async I/O), FastAPI (API server) (010-event-stream-the)
- File system (JSONL files in output/{run_id}/events*.jsonl) (010-event-stream-the)
- Python 3.12 + structlog 24.x (existing), Python stdlib contextvars (011-logging-improvements-enhanced)
- N/A (logging only - outputs to stdout/files) (011-logging-improvements-enhanced)
- Python 3.12 + Pydantic 2.x (state models), PyYAML 6.x (config), structlog 24.x (logging), NetworkX (graph algorithms for shortest path) (012-spatial-maps)
- File system (YAML configs, JSON checkpoints for spatial state persistence) (012-spatial-maps)
- Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), aiofiles (async I/O for async mode) (013-event-writer-fix)
- File system (JSONL files in `output/{run_id}/events.jsonl`) (013-event-writer-fix)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.12: Follow standard conventions

## Recent Changes
- 013-event-writer-fix: Added Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), aiofiles (async I/O for async mode)
- 012-spatial-maps: Added Python 3.12 + Pydantic 2.x (state models), PyYAML 6.x (config), structlog 24.x (logging), NetworkX (graph algorithms for shortest path)
- 011-logging-improvements-enhanced: Added Python 3.12 + structlog 24.x (existing), Python stdlib contextvars

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
