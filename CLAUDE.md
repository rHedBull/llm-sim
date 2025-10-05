# llm_sim Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-09-30

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
- 010-event-stream-the: Added Python 3.12 + Pydantic 2.x (data models), structlog 24.x (logging), httpx (async I/O), FastAPI (API server)
- 009-dynamic-agent-management: Added Python 3.12 + Pydantic 2.x (data models), PyYAML 6.x (config), structlog 24.x (logging)
- 008-partial-observability-agents: Added [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
