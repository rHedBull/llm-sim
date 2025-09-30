# LLM Simulation Framework

A turn-based multi-agent simulation framework with LLM-based reasoning capabilities.

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run basic simulation (rule-based)
python main.py examples/quick_test.yaml

# Run LLM-based simulation (requires Ollama)
ollama pull gemma3:1b
python main.py config_llm_example.yaml
```

## Features

- **LLM-based reasoning**: Agents, validators, and engines powered by local LLMs via Ollama
- **Rule-based fallback**: Traditional rule-based components for simpler scenarios
- **YAML configuration**: Simple declarative configuration
- **Extensible architecture**: Three-tier inheritance (Base → LLM Abstract → Concrete)
- **Full observability**: Structured logging with reasoning chain traces

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) - System design and components
- [Configuration Guide](docs/CONFIGURATION.md) - How to configure simulations
- [LLM Setup](docs/LLM_SETUP.md) - Setting up Ollama and LLM-based reasoning
- [API Reference](docs/API.md) - Extending the framework

## Requirements

**Basic simulations:**
- Python 3.12+
- Dependencies: pydantic, PyYAML, structlog

**LLM simulations:**
- All basic requirements
- Ollama (local LLM server)
- Additional deps: ollama, httpx, tenacity

## Development

```bash
# Run tests
pytest tests/ --cov=src

# Run tests with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Type checking
mypy src/
```

## License

This project is part of the LLM simulation framework.