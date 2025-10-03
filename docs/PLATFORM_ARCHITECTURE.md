# LLM-Sim Platform Architecture

**Vision:** Transform llm-sim from a simulation library into a complete platform with multi-simulation orchestration, real-time dashboard, and LLM control via MCP.

**Last Updated:** 2025-10-01

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Three-Tier System](#three-tier-system)
- [Repository Structure](#repository-structure)
- [Control Server Design](#control-server-design)
- [Implementation Phases](#implementation-phases)
- [Key Design Decisions](#key-design-decisions)
- [Technology Stack](#technology-stack)
- [Timeline & Next Steps](#timeline--next-steps)

---

## Architecture Overview

The platform consists of three distinct tiers:

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM / Human Users                         │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   [Dashboard]              [MCP Server]
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │   llm-sim-server        │
        │  (Control Plane)        │
        │  - SimulationManager    │
        │  - Process Pool         │
        │  - Status Tracker       │
        └────────────┬────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
   [economic-sim]          [climate-sim]
   (Domain Repos)          (Domain Repos)
        │                         │
        └────────────┬────────────┘
                     │
        ┌────────────▼────────────┐
        │      llm-sim            │
        │   (Core Framework)      │
        │   - Infrastructure      │
        │   - Orchestrator        │
        │   - Persistence         │
        └─────────────────────────┘
```

---

## Three-Tier System

### Tier 1: Framework Library (`llm-sim`)

**Purpose:** Pure infrastructure - base classes, orchestration, persistence

**Responsibilities:**
- Provide base classes (`BaseAgent`, `BaseEngine`, `BaseValidator`)
- LLM abstraction patterns (`LLMAgent`, `LLMEngine`, `LLMValidator`)
- State management and serialization
- Checkpoint system with schema validation
- Component discovery mechanism
- Simulation orchestration (single simulation runner)

**What it does NOT contain:**
- ❌ Concrete agent/engine/validator implementations
- ❌ Domain-specific logic
- ❌ Example configurations
- ❌ Multi-simulation management

**Distribution:** PyPI package or git dependency

```python
# Users install and import:
pip install llm-sim
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.orchestrator import SimulationOrchestrator
```

### Tier 2: Domain Implementation Repos (`llm-sim-*`)

**Purpose:** Concrete implementations for specific simulation domains

**Examples:**
- `llm-sim-economic` - Economic simulations (nations, markets, trade)
- `llm-sim-climate` - Climate policy simulations
- `llm-sim-biological` - Ecosystem/evolution simulations
- `llm-sim-social` - Social network dynamics

**Structure:**
```
llm-sim-economic/
├── src/economic_sim/
│   ├── agents/
│   │   ├── nation.py          # NationAgent(BaseAgent)
│   │   ├── trader.py
│   │   └── central_bank.py
│   ├── engines/
│   │   ├── economic.py        # EconomicEngine(BaseEngine)
│   │   └── market_engine.py
│   ├── validators/
│   │   └── econ_validator.py
│   └── scenarios/             # Pre-configured YAML files
│       ├── growth.yaml
│       ├── recession.yaml
│       ├── trade_war.yaml
│       └── stimulus.yaml
├── main.py                    # CLI: python main.py scenarios/growth.yaml
├── pyproject.toml
│   # dependencies = ["llm-sim>=0.1.0"]
└── tests/
```

**Key point:** Each domain repo depends on `llm-sim` framework but is otherwise independent.

### Tier 3: Control Plane (`llm-sim-server`)

**Purpose:** Domain-agnostic orchestration, monitoring, and control

**Responsibilities:**
- Manage multiple concurrent simulations (up to 5 in parallel)
- Track simulation lifecycle (queued/running/completed/failed)
- Provide REST API for programmatic control
- Real-time WebSocket streaming of simulation progress
- MCP server for LLM-based control
- Web dashboard for human monitoring
- Query simulation results and checkpoints

**Key insight:** Control server is **domain-agnostic**. It:
- Points to any simulation repo using `llm-sim`
- Discovers components via the framework's discovery mechanism
- Runs simulations in isolated processes
- Monitors via checkpoint polling

---

## Repository Structure

### 1. `llm-sim/` - Framework (THIS REPO - NEEDS CLEANUP)

**Current state:** Mixed framework + implementations

**Target state:** Pure framework only

```
llm-sim/
├── src/llm_sim/
│   ├── infrastructure/        ✅ KEEP - base classes
│   │   ├── base/
│   │   │   ├── agent.py
│   │   │   ├── engine.py
│   │   │   └── validator.py
│   │   └── patterns/          ✅ KEEP - LLM abstractions
│   │       ├── llm_agent.py
│   │       ├── llm_engine.py
│   │       └── llm_validator.py
│   ├── models/                ✅ KEEP
│   │   ├── state.py
│   │   ├── config.py
│   │   ├── action.py
│   │   ├── checkpoint.py
│   │   └── exceptions.py
│   ├── persistence/           ✅ KEEP
│   │   ├── checkpoint_manager.py
│   │   ├── storage.py
│   │   └── schema_hash.py
│   ├── orchestrator.py        ✅ KEEP - single sim runner
│   ├── discovery.py           ✅ KEEP - component loading
│   ├── utils/                 ✅ KEEP
│   │   ├── llm_client.py
│   │   └── logging.py
│   └── implementations/       ❌ REMOVE → move to llm-sim-economic
├── tests/                     ✅ KEEP - framework tests only
│   ├── unit/
│   ├── integration/
│   └── contract/
├── examples/                  ❌ REMOVE → move to llm-sim-economic
├── main.py                    ❌ REMOVE → move to llm-sim-economic
├── docs/                      ✅ KEEP - framework docs
├── pyproject.toml             ✅ KEEP - framework dependencies
└── README.md                  ✅ UPDATE - clarify it's a framework
```

**Action Required (Phase 0):**
1. Extract `implementations/` → `llm-sim-economic/src/economic_sim/`
2. Extract `examples/` → `llm-sim-economic/scenarios/`
3. Extract `main.py` → `llm-sim-economic/main.py`
4. Remove extracted directories from `llm-sim`
5. Update README to clarify library purpose

### 2. `llm-sim-economic/` - Economic Domain (NEW REPO)

**Purpose:** Reference implementation and economic simulation domain

```
llm-sim-economic/
├── src/economic_sim/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── nation.py           # From llm-sim/implementations/agents/nation.py
│   │   ├── econ_llm_agent.py   # From llm-sim/implementations/agents/econ_llm_agent.py
│   │   └── trader.py           # Future: new agents
│   ├── engines/
│   │   ├── __init__.py
│   │   ├── economic.py         # From llm-sim/implementations/engines/economic.py
│   │   └── econ_llm_engine.py  # From llm-sim/implementations/engines/econ_llm_engine.py
│   ├── validators/
│   │   ├── __init__.py
│   │   ├── always_valid.py     # From llm-sim/implementations/validators/always_valid.py
│   │   └── econ_llm_validator.py
│   └── scenarios/              # From llm-sim/examples/
│       ├── basic_economic.yaml
│       ├── llm_economic.yaml
│       ├── hybrid_simulation.yaml
│       ├── quick_test.yaml
│       └── extended_test.yaml
├── main.py                     # From llm-sim/main.py
├── pyproject.toml
│   # [project]
│   # name = "llm-sim-economic"
│   # dependencies = ["llm-sim>=0.1.0", "pydantic>=2.0", ...]
├── tests/                      # Domain-specific tests
├── README.md                   # Economic simulation usage
└── .gitignore
```

**Setup:**
```bash
cd llm-sim-economic
pip install -e .
python main.py scenarios/basic_economic.yaml
```

### 3. `llm-sim-server/` - Control Plane (NEW REPO)

**Purpose:** Multi-simulation orchestration and monitoring

```
llm-sim-server/
├── src/llm_sim_server/
│   ├── __init__.py
│   ├── manager/
│   │   ├── __init__.py
│   │   ├── simulation_manager.py   # Core: multi-sim lifecycle
│   │   ├── repo_registry.py        # Track registered repos
│   │   ├── process_pool.py         # Process management
│   │   └── status_tracker.py       # Real-time status aggregation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py                  # FastAPI application
│   │   ├── routes.py               # REST endpoints
│   │   ├── websocket.py            # Real-time streaming
│   │   └── models.py               # API request/response models
│   ├── mcp/
│   │   ├── __init__.py
│   │   └── server.py               # FastMCP server
│   └── storage/
│       ├── __init__.py
│       └── query.py                # Read output/ directory
├── dashboard/                      # React frontend
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── SimulationList.jsx
│   │   │   ├── SimulationDetail.jsx
│   │   │   ├── StatusBadge.jsx
│   │   │   └── ChartView.jsx
│   │   ├── views/
│   │   │   ├── Dashboard.jsx
│   │   │   ├── SimulationPage.jsx
│   │   │   └── ConfigEditor.jsx
│   │   └── api/
│   │       ├── client.js
│   │       └── websocket.js
│   ├── package.json
│   ├── vite.config.js
│   └── index.html
├── config.yaml                     # Server configuration
│   # simulation_repos:
│   #   - name: economic
│   #     path: ../llm-sim-economic
│   #     python_path: economic_sim
│   #   - name: climate
│   #     path: ../llm-sim-climate
│   #     python_path: climate_sim
├── pyproject.toml
│   # dependencies = [
│   #   "llm-sim>=0.1.0",
│   #   "fastapi>=0.100.0",
│   #   "fastmcp>=2.0.0",
│   #   "uvicorn>=0.20.0",
│   #   "websockets>=10.0",
│   # ]
├── tests/
├── README.md
└── docker-compose.yml              # Optional: containerized deployment
```

---

## Control Server Design

### Core Component: SimulationManager

```python
# manager/simulation_manager.py
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional
import sys
import importlib

class SimulationManager:
    """Manages lifecycle of multiple concurrent simulations."""

    def __init__(
        self,
        max_concurrent: int = 5,
        output_root: Path = Path("output"),
        repo_registry: RepoRegistry = None
    ):
        self.pool = ProcessPoolExecutor(max_workers=max_concurrent)
        self.active_sims: Dict[str, SimulationHandle] = {}
        self.status_tracker = StatusTracker(output_root)
        self.repo_registry = repo_registry
        self.output_root = output_root

    async def start_simulation(
        self,
        repo_name: str,
        config_path: str
    ) -> str:
        """Start new simulation in subprocess.

        Args:
            repo_name: Registered simulation repo (e.g., "economic")
            config_path: Relative path to config (e.g., "scenarios/growth.yaml")

        Returns:
            run_id: Unique simulation identifier
        """
        # Get repo configuration
        repo = self.repo_registry.get(repo_name)

        # Resolve full config path
        full_config_path = Path(repo.path) / config_path

        # Submit to process pool
        future = self.pool.submit(
            _run_simulation_subprocess,
            repo_path=repo.path,
            python_path=repo.python_path,
            config_path=str(full_config_path),
            output_root=self.output_root
        )

        # Track simulation
        run_id = self._extract_run_id_from_future(future)
        self.active_sims[run_id] = SimulationHandle(
            run_id=run_id,
            future=future,
            repo_name=repo_name,
            config_path=config_path
        )

        return run_id

    async def get_status(self, run_id: str) -> SimStatus:
        """Get real-time status by reading checkpoints.

        Args:
            run_id: Simulation identifier

        Returns:
            Current simulation status with latest state
        """
        return self.status_tracker.get_status(run_id)

    async def cancel_simulation(self, run_id: str) -> bool:
        """Cancel running simulation.

        Args:
            run_id: Simulation to cancel

        Returns:
            True if successfully cancelled
        """
        if run_id in self.active_sims:
            handle = self.active_sims[run_id]
            handle.future.cancel()
            return True
        return False

    async def list_simulations(
        self,
        repo_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SimInfo]:
        """List all simulations with optional filters.

        Args:
            repo_name: Optional filter by repository
            status: Optional filter by status (running/completed/failed)

        Returns:
            List of simulation metadata
        """
        return self.status_tracker.list_simulations(
            repo_name=repo_name,
            status=status
        )


def _run_simulation_subprocess(
    repo_path: str,
    python_path: str,
    config_path: str,
    output_root: Path
):
    """Function executed in subprocess to run simulation.

    Args:
        repo_path: Path to simulation repo
        python_path: Python import path (e.g., "economic_sim")
        config_path: Full path to YAML config
        output_root: Where to save results
    """
    # Add repo to Python path for discovery
    sys.path.insert(0, repo_path)

    # Import framework
    from llm_sim.orchestrator import SimulationOrchestrator

    # Run simulation
    orchestrator = SimulationOrchestrator.from_yaml(
        config_path,
        output_root=output_root
    )
    result = orchestrator.run()

    return result
```

### Status Tracking via Checkpoint Polling

```python
# manager/status_tracker.py
class StatusTracker:
    """Tracks simulation status by polling checkpoints."""

    def __init__(self, output_root: Path):
        self.output_root = output_root

    def get_status(self, run_id: str) -> SimStatus:
        """Get status by reading latest checkpoint.

        Reads output/{run_id}/checkpoints/last.json
        """
        checkpoint_path = self.output_root / run_id / "checkpoints" / "last.json"

        if not checkpoint_path.exists():
            return SimStatus(status="queued", turn=0)

        # Read checkpoint
        with open(checkpoint_path) as f:
            checkpoint = json.load(f)

        # Check if simulation is complete
        result_path = self.output_root / run_id / "result.json"
        if result_path.exists():
            status = "completed"
        else:
            status = "running"

        return SimStatus(
            status=status,
            run_id=run_id,
            turn=checkpoint["state"]["turn"],
            state=checkpoint["state"],
            timestamp=checkpoint["timestamp"]
        )

    def list_simulations(
        self,
        repo_name: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[SimInfo]:
        """List all simulations by scanning output directory."""
        simulations = []

        for run_dir in self.output_root.iterdir():
            if not run_dir.is_dir():
                continue

            sim_status = self.get_status(run_dir.name)

            # Apply filters
            if status and sim_status.status != status:
                continue

            simulations.append(SimInfo(
                run_id=run_dir.name,
                status=sim_status.status,
                current_turn=sim_status.turn,
                # Parse metadata from run_id or result.json
            ))

        return simulations
```

### REST API Endpoints

```python
# api/routes.py
from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM-Sim Control Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/simulations")
async def start_simulation(request: StartSimRequest):
    """Start a new simulation.

    Body:
        {
            "repo": "economic",
            "config": "scenarios/growth.yaml"
        }

    Returns:
        {"run_id": "...", "status": "queued"}
    """
    run_id = await manager.start_simulation(
        repo_name=request.repo,
        config_path=request.config
    )
    return {"run_id": run_id, "status": "queued"}

@app.get("/api/simulations")
async def list_simulations(
    repo: Optional[str] = None,
    status: Optional[str] = None
):
    """List all simulations with optional filters.

    Query params:
        repo: Filter by repository name
        status: Filter by status (running/completed/failed)

    Returns:
        [
            {
                "run_id": "...",
                "status": "running",
                "repo": "economic",
                "current_turn": 45,
                "max_turns": 100
            },
            ...
        ]
    """
    return await manager.list_simulations(repo_name=repo, status=status)

@app.get("/api/simulations/{run_id}")
async def get_simulation(run_id: str):
    """Get detailed simulation status.

    Returns:
        {
            "run_id": "...",
            "status": "running",
            "current_turn": 45,
            "max_turns": 100,
            "state": {
                "agents": {...},
                "global_state": {...}
            }
        }
    """
    status = await manager.get_status(run_id)
    if not status:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return status

@app.delete("/api/simulations/{run_id}")
async def cancel_simulation(run_id: str):
    """Cancel a running simulation.

    Returns:
        {"success": true, "run_id": "..."}
    """
    success = await manager.cancel_simulation(run_id)
    if not success:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return {"success": success, "run_id": run_id}

@app.get("/api/simulations/{run_id}/results")
async def get_results(run_id: str):
    """Get final results for completed simulation.

    Returns full result.json contents
    """
    result_path = output_root / run_id / "result.json"
    if not result_path.exists():
        raise HTTPException(status_code=404, detail="Results not available")

    with open(result_path) as f:
        return json.load(f)

@app.websocket("/api/simulations/{run_id}/stream")
async def stream_progress(websocket: WebSocket, run_id: str):
    """WebSocket endpoint for real-time progress updates.

    Sends JSON messages every 1 second:
    {
        "type": "progress",
        "run_id": "...",
        "turn": 45,
        "state": {...}
    }
    """
    await websocket.accept()

    try:
        while True:
            status = await manager.get_status(run_id)

            await websocket.send_json({
                "type": "progress" if status.status == "running" else "complete",
                "run_id": run_id,
                "turn": status.turn,
                "status": status.status,
                "state": status.state
            })

            if status.status != "running":
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass
```

### MCP Server Interface

```python
# mcp/server.py
from fastmcp import FastMCP

mcp = FastMCP("llm-sim-control")

@mcp.tool()
async def start_simulation(repo: str, config: str) -> dict:
    """Start a new simulation from YAML config.

    Args:
        repo: Simulation repository name (e.g., "economic", "climate")
        config: Relative path to config file (e.g., "scenarios/growth.yaml")

    Returns:
        {"run_id": "...", "status": "queued"}

    Example:
        start_simulation(repo="economic", config="scenarios/growth.yaml")
    """
    run_id = await manager.start_simulation(
        repo_name=repo,
        config_path=config
    )
    return {"run_id": run_id, "status": "queued"}

@mcp.tool()
async def get_simulation_status(run_id: str) -> dict:
    """Get current status and progress of a simulation.

    Args:
        run_id: Unique simulation run identifier

    Returns:
        {
            "status": "running",
            "turn": 45,
            "max_turns": 100,
            "agents": {...},
            "global_state": {...}
        }

    Example:
        get_simulation_status(run_id="Economic_2agents_20251001_120000_01")
    """
    status = await manager.get_status(run_id)
    return status.dict()

@mcp.tool()
async def list_simulations(
    repo: Optional[str] = None,
    status: Optional[str] = None
) -> list:
    """List all simulations, optionally filtered by repo or status.

    Args:
        repo: Optional filter by repository name
        status: Optional filter (running/completed/failed/queued)

    Returns:
        [
            {
                "run_id": "...",
                "repo": "economic",
                "status": "running",
                "turn": 45
            },
            ...
        ]

    Example:
        list_simulations(status="running")
        list_simulations(repo="economic")
    """
    sims = await manager.list_simulations(repo_name=repo, status=status)
    return [s.dict() for s in sims]

@mcp.tool()
async def cancel_simulation(run_id: str) -> dict:
    """Cancel a running simulation.

    Args:
        run_id: Simulation identifier to cancel

    Returns:
        {"success": true, "run_id": "..."}

    Example:
        cancel_simulation(run_id="Economic_2agents_20251001_120000_01")
    """
    success = await manager.cancel_simulation(run_id)
    return {"success": success, "run_id": run_id}

@mcp.tool()
async def get_simulation_results(run_id: str) -> dict:
    """Get final results for a completed simulation.

    Args:
        run_id: Completed simulation identifier

    Returns:
        Full result.json contents including final state and statistics

    Example:
        get_simulation_results(run_id="Economic_2agents_20251001_120000_01")
    """
    result_path = output_root / run_id / "result.json"
    if not result_path.exists():
        return {"error": "Results not available - simulation may not be complete"}

    with open(result_path) as f:
        return json.load(f)

@mcp.resource("simulation://{run_id}/config")
async def get_config(run_id: str) -> str:
    """Get simulation configuration from result metadata."""
    result_path = output_root / run_id / "result.json"
    with open(result_path) as f:
        result = json.load(f)
    return yaml.dump(result["run_metadata"]["config_snapshot"])

@mcp.resource("simulation://{run_id}/checkpoints")
async def list_checkpoints(run_id: str) -> str:
    """List available checkpoints for a simulation."""
    checkpoint_dir = output_root / run_id / "checkpoints"
    checkpoints = sorted([
        f.stem for f in checkpoint_dir.glob("turn_*.json")
    ])
    return "\n".join(checkpoints)
```

**MCP Usage Example with Claude:**

```
User: "Start 3 economic simulations comparing different scenarios"

Claude:
I'll start three economic simulations with different scenarios.

→ start_simulation(repo="economic", config="scenarios/growth.yaml")
   Result: {"run_id": "Economic_2agents_20251001_120000_01", "status": "queued"}

→ start_simulation(repo="economic", config="scenarios/recession.yaml")
   Result: {"run_id": "Economic_2agents_20251001_120001_01", "status": "queued"}

→ start_simulation(repo="economic", config="scenarios/trade_war.yaml")
   Result: {"run_id": "Economic_2agents_20251001_120002_01", "status": "queued"}

I've started three simulations:
1. Growth scenario
2. Recession scenario
3. Trade war scenario

User: "Which one has the highest GDP after 50 turns?"

Claude:
→ list_simulations(status="running")
→ get_simulation_status(run_id="Economic_2agents_20251001_120000_01")
→ get_simulation_status(run_id="Economic_2agents_20251001_120001_01")
→ get_simulation_status(run_id="Economic_2agents_20251001_120002_01")

Based on current progress (turn 50):
- Growth scenario: total_economic_value = 4,500
- Recession scenario: total_economic_value = 1,800
- Trade war scenario: total_economic_value = 3,200

The growth scenario has the highest GDP at turn 50.
```

---

## Implementation Phases

### Phase 0: Repository Cleanup ✅ **COMPLETED**

**Goal:** Separate framework from implementations

**Duration:** 1 day

**Status:** COMPLETED (2025-10-01)

**Completed Tasks:**
1. ✅ Created new `llm-sim-economic` repository
2. ✅ Moved `src/llm_sim/implementations/` → `llm-sim-economic/implementations/`
3. ✅ Moved `examples/` → `llm-sim-economic/scenarios/`
4. ✅ Moved `main.py` → `llm-sim-economic/main.py`
5. ✅ Created `llm-sim-economic/pyproject.toml` with dependency on `llm-sim`
6. ✅ Modified orchestrator to support `implementations_root` parameter
7. ✅ Removed domain-specific implementations from framework
8. ✅ Removed domain-specific tests from framework:
   - Removed `tests/e2e/` (2 files → moved to economic repo)
   - Removed `tests/integration/` (15 files → moved to economic repo)
   - Removed domain-specific unit tests (4 files)
   - Removed domain-specific contract tests (3 files)
9. ✅ Moved all domain tests to `llm-sim-economic/tests/`
10. ✅ Updated framework README to clarify framework-only purpose

**Deliverable:** Clean separation - framework in one repo, reference implementation in another

**Validation:**
- ✅ `llm-sim` contains no concrete implementations
- ✅ `llm-sim-economic` runs successfully standalone
- ✅ Framework tests pass: 76 unit tests + 118 contract tests
- ✅ Economic repo tests pass: 14 e2e tests + 3 contract tests

**Key Technical Changes:**
- `SimulationOrchestrator` now accepts optional `implementations_root` parameter
- Discovery mechanism works with external domain repositories
- Economic repo properly configured with `uv` dependency management
- Tests separated by concern: framework vs domain-specific

---

### Phase 1: Simulation Manager

**Goal:** Multi-simulation orchestration layer

**Duration:** 2-3 days

**Tasks:**
1. Create `llm-sim-server` repository structure
2. Implement `RepoRegistry` class
   - Load repos from `config.yaml`
   - Validate repo paths and python modules
3. Implement `SimulationManager` core class
   - Process pool initialization
   - `start_simulation()` with subprocess spawning
   - Add repo path to `sys.path` for discovery
4. Implement `StatusTracker`
   - Poll checkpoint files (every 1-2 seconds)
   - Parse `last.json` and `result.json`
   - Track simulation lifecycle
5. Add `list_simulations()` and `get_status()` methods
6. Implement `cancel_simulation()` with process termination
7. Add resource limits (max 5 concurrent)
8. Unit tests for manager components
9. Integration test: start 5 parallel simulations

**Deliverable:** Python API to orchestrate multiple simulations

**Validation:**
- [ ] Can start 5 simulations concurrently
- [ ] Can query status of running simulations
- [ ] Can cancel running simulations
- [ ] Status correctly reflects checkpoint data

---

### Phase 2: REST API + WebSocket

**Goal:** HTTP interface for programmatic access

**Duration:** 2-3 days

**Tasks:**
1. Set up FastAPI application structure
2. Implement REST endpoints:
   - `POST /api/simulations` - Start new simulation
   - `GET /api/simulations` - List all (with filters)
   - `GET /api/simulations/{run_id}` - Get status
   - `DELETE /api/simulations/{run_id}` - Cancel
   - `GET /api/simulations/{run_id}/results` - Get final results
3. Implement WebSocket endpoint `/api/simulations/{run_id}/stream`
   - Poll checkpoint every 1 second
   - Broadcast JSON updates to connected clients
   - Handle client disconnection gracefully
4. Add CORS middleware for dashboard
5. Add error handling and validation
6. OpenAPI documentation (auto-generated by FastAPI)
7. Integration tests for all endpoints

**Deliverable:** Working REST API with real-time WebSocket streaming

**Validation:**
- [ ] Can start simulation via POST request
- [ ] Can list simulations with filters
- [ ] WebSocket streams updates every second
- [ ] API documentation available at `/docs`

---

### Phase 3: Dashboard (MVP)

**Goal:** Web UI for monitoring and control

**Duration:** 4-5 days

**Tech Stack:**
- React 18 with Vite
- TailwindCSS for styling
- Recharts for visualization
- Native WebSocket API

**Tasks:**

**Day 1: Project Setup**
1. Initialize React project with Vite
2. Set up TailwindCSS
3. Create basic layout (header, sidebar, main content)
4. Set up API client utility

**Day 2: Simulation List View**
1. Create `SimulationList` component
2. Fetch simulations from API (`GET /api/simulations`)
3. Display status badges (running/completed/failed)
4. Add progress bars (turn X / max_turns)
5. Quick action buttons (view, cancel)
6. Auto-refresh every 2 seconds

**Day 3: Start Simulation UI**
1. Create `StartSimulation` component
2. Repo selector dropdown
3. Config file selector
4. Form validation
5. Submit via `POST /api/simulations`
6. Show success/error feedback

**Day 4: Simulation Detail View**
1. Create `SimulationDetail` component
2. WebSocket connection to `/api/simulations/{id}/stream`
3. Real-time state display
4. Line chart for agent economic_strength over time (Recharts)
5. Global state metrics display
6. Checkpoint timeline

**Day 5: Polish & Testing**
1. Error states and loading spinners
2. Responsive design (mobile-friendly)
3. Dark mode toggle (optional)
4. End-to-end testing with Playwright
5. Build and serve static files

**Deliverable:** Functional web dashboard

**Validation:**
- [ ] Can view list of all simulations
- [ ] Can start new simulation from UI
- [ ] Real-time updates display correctly
- [ ] Charts render agent states over time
- [ ] Works on mobile browsers

---

### Phase 4: MCP Server

**Goal:** Enable LLM control of simulations

**Duration:** 2 days

**Tasks:**
1. Set up FastMCP integration
2. Define MCP tools:
   - `start_simulation(repo, config)` → run_id
   - `get_simulation_status(run_id)` → status dict
   - `list_simulations(repo?, status?)` → simulation list
   - `cancel_simulation(run_id)` → success
   - `get_simulation_results(run_id)` → results dict
3. Define MCP resources:
   - `simulation://{run_id}/config` → YAML config
   - `simulation://{run_id}/checkpoints` → checkpoint list
4. Connect MCP tools to `SimulationManager`
5. Test with Claude Desktop:
   - Add server to `claude_desktop_config.json`
   - Test starting simulations via chat
   - Test querying status
   - Test cancellation
6. Write MCP usage documentation

**Deliverable:** MCP server that Claude can use to control simulations

**Validation:**
- [ ] Claude can start simulations via MCP
- [ ] Claude can check simulation status
- [ ] Claude can list and filter simulations
- [ ] Claude can cancel simulations
- [ ] Claude can retrieve and analyze results

---

### Phase 5: Multi-Repo Support & Polish

**Goal:** Support multiple simulation domains, production-ready

**Duration:** 2-3 days

**Tasks:**
1. Enhance `RepoRegistry` for multiple repos
2. Dashboard improvements:
   - Repo filter dropdown
   - Group by repo in list view
   - Per-repo config templates
3. Add authentication (optional):
   - API key authentication
   - Rate limiting
4. Improve error handling and logging
5. Add health check endpoint (`/health`)
6. Docker Compose setup:
   ```yaml
   services:
     server:
       build: .
       ports:
         - "8000:8000"
       volumes:
         - ./output:/app/output
         - ../llm-sim-economic:/repos/economic
   ```
7. Deployment documentation
8. "Creating a Custom Simulation" tutorial

**Deliverable:** Production-ready platform supporting multiple domains

**Validation:**
- [ ] Can register and use multiple simulation repos
- [ ] Dashboard shows simulations from all repos
- [ ] Docker Compose brings up full stack
- [ ] Documentation covers all use cases

---

## Key Design Decisions

### 1. Discovery Mechanism

**Question:** How does control server find simulation components?

**Answer:** Via Python import path manipulation

```python
# In subprocess:
sys.path.insert(0, "/path/to/llm-sim-economic")

# Now framework's discovery can import:
from economic_sim.agents.nation import NationAgent
```

The existing `discovery.py` mechanism should work as-is since it uses `importlib.import_module()`.

**Alternative considered:** CLI invocation - simpler but less control

### 2. Process Management

**Question:** How to run multiple simulations in parallel?

**Answer:** `ProcessPoolExecutor` with process-based isolation

**Rationale:**
- Avoids Python GIL for CPU-bound simulations
- Isolation prevents cross-contamination
- Built-in futures API for tracking
- Simpler than Celery for this use case

**Alternative considered:** Threading - rejected due to GIL limitations

### 3. Status Tracking

**Question:** How to get real-time simulation progress?

**Answer:** Poll checkpoint files (`last.json`) every 1-2 seconds

**Rationale:**
- Stateless - no in-memory state to lose
- Works even if server restarts
- Leverages existing checkpoint system
- Simple implementation

**Alternatives considered:**
- Callback injection - requires framework changes
- Shared memory - complex IPC
- Message queue - overkill for this scale

### 4. Dashboard Data Flow

**Question:** How does dashboard get real-time updates?

**Answer:** WebSocket connection polling checkpoints

```
Dashboard ←─ WebSocket ←─ Server ←─ Poll every 1s ─→ last.json
```

**Rationale:**
- Bidirectional communication
- Low latency (1 second updates)
- Automatic reconnection
- Standard browser API

**Alternative considered:** Server-Sent Events - simpler but less flexible

### 5. Python Environments

**Question:** How to handle different dependencies per domain?

**Answer:** Start with shared environment, add containerization later

**Phase 1:** All repos share same Python environment
- Simpler setup
- Faster development
- Works if dependencies are compatible

**Phase 2 (future):** Docker containers per simulation
- Full isolation
- Independent dependency versions
- More complex deployment

### 6. Database vs Filesystem

**Question:** Store simulation metadata in database?

**Answer:** Stay filesystem-based (for now)

**Rationale:**
- Checkpoint system already uses files
- No new dependencies
- Stateless server design
- Simpler deployment

**When to add database:**
- Need complex queries (e.g., "find all simulations where GDP > X")
- 100+ concurrent simulations
- Need historical analytics

### 7. Dashboard: Multi-Repo View

**Question:** How to display simulations from multiple repos?

**Answer:** Unified list with repo filter

```
┌─────────────────────────────────────┐
│  All Simulations    [Filter: All ▾] │
├─────────────────────────────────────┤
│  economic • growth_scenario         │
│  ● Running • Turn 45/100            │
├─────────────────────────────────────┤
│  economic • recession_scenario      │
│  ✓ Completed • Turn 100/100         │
├─────────────────────────────────────┤
│  climate • paris_agreement          │
│  ● Running • Turn 67/200            │
└─────────────────────────────────────┘
```

Filter dropdown: All | Economic | Climate

**Alternative:** Separate tabs per repo - more clicks, less overview

### 8. Authentication

**Question:** How to secure the control server?

**Answer:** Phased approach based on deployment

**Phase 1 (local dev):** No authentication
- Single user
- Localhost only
- Fastest iteration

**Phase 2 (team deployment):** API keys
```python
# config.yaml
api_keys:
  - key: "sk_..."
    name: "Team Member 1"
```

**Phase 3 (production):** OAuth2
- GitHub/Google login
- Per-user permissions
- Audit logging

---

## Technology Stack

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **Framework** | Python | 3.12+ | Existing codebase, async support |
| **Process Management** | ProcessPoolExecutor | stdlib | Built-in, simple, effective |
| **API Server** | FastAPI | 0.100+ | Modern, async, auto docs, WebSocket |
| **MCP Server** | FastMCP | 2.0+ | Pythonic, production-ready, auth support |
| **Frontend** | React | 18+ | Mature, large ecosystem, good docs |
| **Build Tool** | Vite | 5+ | Fast dev server, optimized builds |
| **Styling** | TailwindCSS | 3+ | Utility-first, rapid development |
| **Charts** | Recharts | 2+ | React-native, composable, responsive |
| **HTTP Client** | fetch API | native | No dependencies, modern browsers |
| **WebSocket** | WebSocket API | native | No dependencies, standard |
| **Testing (backend)** | pytest | 8+ | Existing test suite |
| **Testing (frontend)** | Playwright | 1+ | E2E, cross-browser |
| **Containerization** | Docker | 24+ | Deployment, isolation (Phase 5) |

---

## Timeline & Next Steps

### Immediate Action (This Week)

**Phase 0: Repository Cleanup**
- [ ] Create `llm-sim-economic` repo
- [ ] Extract implementations and examples
- [ ] Test both repos independently
- [ ] Update documentation

**Estimated time:** 1 day

### Short Term (Next 2 Weeks)

**Phases 1-2: Core Control Server**
- [ ] Implement `SimulationManager`
- [ ] Build REST API + WebSocket
- [ ] Test with multiple concurrent simulations

**Estimated time:** 4-6 days

### Medium Term (Next Month)

**Phases 3-4: User Interfaces**
- [ ] Build React dashboard
- [ ] Implement MCP server
- [ ] End-to-end testing

**Estimated time:** 6-7 days

### Long Term (2+ Months)

**Phase 5: Production Ready**
- [ ] Multi-repo support
- [ ] Authentication
- [ ] Docker deployment
- [ ] Comprehensive documentation

**Estimated time:** 2-3 days

---

## Success Metrics

### Phase 0 Completion ✅
- ✅ Framework repo contains zero implementations
- ✅ Economic simulations run from separate repo
- ✅ All tests pass in both repos
- ✅ 76 framework unit tests + 118 contract tests passing
- ✅ 14 economic e2e tests + 3 contract tests passing
- ✅ Discovery mechanism works with external repos

### Phase 1 Completion done
- ✅ Can start 5 simulations concurrently
- ✅ Can query status of any simulation
- ✅ Can cancel running simulations

### Phase 2 Completion done
- ✅ REST API fully functional
- ✅ WebSocket streams real-time updates
- ✅ OpenAPI docs generated

### Phase 3 Completion in progress
- ✅ Dashboard displays all simulations
- ✅ Can start simulation from web UI
- ✅ Real-time charts update correctly

### Phase 4 Completion
- ✅ Claude can control simulations via MCP
- ✅ MCP tools work reliably
- ✅ Usage documented

### Phase 5 Completion
- ✅ Multi-repo support working
- ✅ Docker Compose deployment functional
- ✅ Production deployment guide complete

---

## Open Questions

1. **Checkpoint polling frequency:** 1 second? 2 seconds? Configurable?
   - **Recommendation:** Start with 1 second, make configurable later

2. **Max concurrent simulations:** Hard limit at 5? Configurable?
   - **Recommendation:** Configurable via `config.yaml`, default 5

3. **Simulation pause/resume:** Should we support pausing simulations?
   - **Recommendation:** Phase 6 feature - requires checkpoint loading

4. **Result retention:** How long to keep old simulation results?
   - **Recommendation:** Manual cleanup initially, add auto-cleanup in Phase 5

5. **Monitoring/Metrics:** Prometheus integration for server health?
   - **Recommendation:** Phase 5 - add `/metrics` endpoint

6. **Authentication:** Which auth provider for production?
   - **Recommendation:** Start with API keys, add OAuth2 when needed

---

## Related Documentation

- [Framework Architecture](./ARCHITECTURE.md) - Core framework design
- [Configuration Guide](./CONFIGURATION.md) - YAML config reference
- [Creating a Domain Repo](./CREATING_DOMAIN_REPO.md) - Tutorial (to be written)
- [API Reference](./API.md) - Framework API docs

---

**Document Status:** Draft - Ready for Phase 0 implementation

**Last Review:** 2025-10-01

**Next Review:** After Phase 0 completion
