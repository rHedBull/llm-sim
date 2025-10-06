# Logging Improvement Plan

**Status:** Current logging setup has critical issues for production server deployment
**Current Rating:** 4/10
**Target Rating:** 9/10 (production-ready)

---

## Problem Summary

### Critical Issue: Logging Framework Incompatibility

- **llm_sim** uses `structlog` (structured logging)
- **llm-sim-server** uses Python's stdlib `logging`
- **Result:** Fragmented, inconsistent logs that cannot be aggregated or correlated

### Current Problems

1. **Fragmented Output**
   - llm_sim outputs JSON: `{"event": "simulation_starting", "timestamp": "2025-10-06T09:08:33.123Z", ...}`
   - Server outputs plaintext: `2025-10-06 09:08:33 - llm_sim_server.api.main - INFO - API started`
   - Cannot parse or search effectively

2. **No Request/Simulation Correlation**
   - API requests cannot be traced to simulation execution
   - Missing request IDs, correlation IDs
   - Cannot debug: "Which API call triggered this simulation error?"

3. **Subprocess Logging Isolation**
   - Simulations run in separate processes
   - Their logs may be lost or written separately
   - No unified view of system behavior

4. **Missing Server-Critical Features**
   - No HTTP request/response logging
   - No slow request warnings
   - No error rate tracking
   - No resource usage metrics

---

## Solution: Unified Structured Logging

### Architecture

```
┌─────────────────────────────────────────────────┐
│         Unified structlog Configuration        │
│  (shared between llm_sim and llm-sim-server)   │
└─────────────────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
┌───────▼────────┐            ┌────────▼─────────┐
│  llm-sim-server│            │     llm_sim      │
│   (FastAPI)    │            │  (subprocess)    │
│                │            │                  │
│ • HTTP logs    │            │ • Simulation logs│
│ • Request IDs  │────────────▶ • Same request ID│
│ • Correlation  │  pass via  │ • Bound context  │
└────────────────┘  subprocess └──────────────────┘
        │                               │
        └───────────────┬───────────────┘
                        ▼
              ┌─────────────────┐
              │  Unified Output │
              │  • Console      │
              │  • JSON (prod)  │
              │  • Log aggregator│
              └─────────────────┘
```

---

## Implementation Plan

### Phase 1: Standardize on structlog (CRITICAL)

#### 1.1 llm-sim-server: Migrate to structlog

**File:** `llm-sim-server/src/llm_sim_server/utils/logging.py` (NEW)

```python
"""Shared logging configuration for server and simulations."""

import os
import structlog

def configure_server_logging(level: str = "INFO", format: str = "auto") -> None:
    """Configure unified structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ('json', 'console', or 'auto' - auto-detect from env)
    """
    # Auto-detect format from environment
    if format == "auto":
        format = "json" if os.getenv("ENVIRONMENT") == "production" else "console"

    processors = [
        # Add contextvars first (for request_id, run_id, etc.)
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                pad_event=35,  # Align event names
            )
        )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)
```

#### 1.2 Update llm-sim-server/api/main.py

**Replace:**
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**With:**
```python
from llm_sim_server.utils.logging import configure_server_logging, get_logger

# Configure at module level (before app creation)
configure_server_logging(level="INFO", format="auto")

logger = get_logger(__name__)
```

#### 1.3 Update all llm-sim-server files

Replace all instances of:
- `import logging` → `from llm_sim_server.utils.logging import get_logger`
- `logging.getLogger(__name__)` → `get_logger(__name__)`

**Files to update:**
- `src/llm_sim_server/manager/simulation_manager.py`
- `src/llm_sim_server/manager/status_tracker.py`
- `src/llm_sim_server/registry/repo_registry.py`
- All route handlers

---

### Phase 2: Add Request Correlation (HIGH PRIORITY)

#### 2.1 Request ID Middleware

**File:** `llm-sim-server/src/llm_sim_server/api/middleware.py` (NEW)

```python
"""FastAPI middleware for request tracking."""

import uuid
import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests and bind to log context."""

    async def dispatch(self, request: Request, call_next):
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Bind to context for this request
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else None,
        )

        # Add to request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        # Clear context
        structlog.contextvars.clear_contextvars()

        return response
```

#### 2.2 HTTP Request Logging Middleware

**File:** `llm-sim-server/src/llm_sim_server/api/middleware.py` (ADD)

```python
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    """Log all HTTP requests and responses with timing."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log incoming request
        logger.info(
            "http_request_started",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params) if request.query_params else None,
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Log response
        log_method = logger.info
        if response.status_code >= 500:
            log_method = logger.error
        elif response.status_code >= 400:
            log_method = logger.warning
        elif duration_ms > 1000:  # Slow request warning
            log_method = logger.warning

        log_method(
            "http_request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            slow_request=duration_ms > 1000,
        )

        return response
```

#### 2.3 Register Middleware in main.py

```python
from llm_sim_server.api.middleware import RequestIDMiddleware, HTTPLoggingMiddleware

app = FastAPI(...)

# Add middleware (order matters - RequestID first!)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(HTTPLoggingMiddleware)
app.add_middleware(CORSMiddleware, ...)
```

---

### Phase 3: Unified Subprocess Logging (HIGH PRIORITY)

#### 3.1 Update llm_sim logging config

**File:** `llm_sim/src/llm_sim/utils/logging.py`

**Enhance to support context binding:**

```python
"""Logging configuration for the simulation."""

import structlog

def configure_logging(
    level: str = "INFO",
    format: str = "json",
    bind_context: dict = None
) -> structlog.BoundLogger:
    """Configure structured logging for the simulation.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        format: Output format ('json' or 'console')
        bind_context: Optional context to bind (e.g., run_id, request_id)

    Returns:
        Logger with bound context
    """
    processors = [
        structlog.contextvars.merge_contextvars,  # Add this!
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if format == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(
            structlog.dev.ConsoleRenderer(
                colors=True,
                pad_event=35,
            )
        )

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get logger and bind context if provided
    logger = structlog.get_logger()
    if bind_context:
        logger = logger.bind(**bind_context)

    return logger

def get_logger(name: str) -> structlog.BoundLogger:
    """Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return structlog.get_logger(name)
```

#### 3.2 Update Orchestrator to accept context

**File:** `llm_sim/src/llm_sim/orchestrator.py`

```python
class SimulationOrchestrator:
    def __init__(
        self,
        config: SimulationConfig,
        # ... existing params ...
        log_context: dict = None,  # NEW
    ) -> None:
        """Initialize orchestrator with configuration.

        Args:
            config: Simulation configuration
            # ... existing params ...
            log_context: Optional logging context (request_id, etc.)
        """
        self.config = config
        self.output_root = output_root

        # Configure logging with context
        self._configure_logging(log_context)

        # ... rest of init ...

    def _configure_logging(self, bind_context: dict = None) -> None:
        """Configure logging with optional context binding."""
        if self.config.logging:
            logger = configure_logging(
                level=self.config.logging.level,
                format=self.config.logging.format,
                bind_context=bind_context
            )
        else:
            logger = configure_logging(
                level="INFO",
                format="json",
                bind_context=bind_context
            )

        # Bind run_id to logger
        self.logger = logger.bind(run_id=self.run_id)

    @classmethod
    def from_yaml(
        cls,
        path: str,
        output_root: Path = Path("output"),
        implementations_root: Optional[Path] = None,
        event_verbosity: VerbosityLevel = VerbosityLevel.ACTION,
        log_context: dict = None,  # NEW
    ) -> "SimulationOrchestrator":
        """Load configuration from YAML file and create orchestrator.

        Args:
            # ... existing params ...
            log_context: Optional logging context for correlation
        """
        with open(path, "r") as f:
            config_data = yaml.safe_load(f)

        config = SimulationConfig(**config_data)
        return cls(
            config,
            output_root=output_root,
            implementations_root=implementations_root,
            event_verbosity=event_verbosity,
            log_context=log_context,  # Pass through
        )
```

#### 3.3 Update SimulationManager subprocess execution

**File:** `llm-sim-server/src/llm_sim_server/manager/simulation_manager.py`

```python
def _run_simulation_subprocess(
    run_id: str,
    repo_path: Path,
    config_yaml_path: Path,
    output_root: Path,
    request_id: str = None,  # NEW - passed from API
):
    """Execute simulation in subprocess with logging context."""
    import sys
    sys.path.insert(0, str(repo_path))

    from llm_sim.orchestrator import SimulationOrchestrator

    # Build log context for correlation
    log_context = {
        "run_id": run_id,
        "subprocess": True,
    }
    if request_id:
        log_context["request_id"] = request_id

    try:
        # Create orchestrator with logging context
        orchestrator = SimulationOrchestrator.from_yaml(
            path=str(config_yaml_path),
            output_root=output_root,
            implementations_root=repo_path / "implementations",
            log_context=log_context,  # Pass context
        )

        result = orchestrator.run()
        return result

    except Exception as e:
        logger.error(
            "simulation_subprocess_failed",
            run_id=run_id,
            error=str(e),
            exc_info=True,
        )
        raise

# Update start_simulation to pass request_id
def start_simulation(
    self,
    repo_name: str,
    config_yaml_path: Path,
    run_id: str | None = None,
    request_id: str | None = None,  # NEW
) -> str:
    """Start a new simulation in isolated subprocess.

    Args:
        repo_name: Name of repository (from registry)
        config_yaml_path: Path to simulation configuration YAML
        run_id: Optional custom run ID (auto-generated if None)
        request_id: Optional request ID for correlation
    """
    # ... validation code ...

    # Start subprocess with context
    process = Process(
        target=_run_simulation_subprocess,
        args=(
            run_id,
            repo_path,
            config_yaml_path,
            self.output_dir,
            request_id,  # Pass through
        ),
    )

    # ... rest of method ...
```

#### 3.4 Update API routes to pass request_id

**File:** `llm-sim-server/src/llm_sim_server/api/routes/simulations.py`

```python
@router.post("/simulations", response_model=CreateSimulationResponse)
async def create_simulation(
    request: Request,  # Add this
    body: CreateSimulationRequest,
) -> CreateSimulationResponse:
    """Create and start a new simulation."""

    # Extract request_id from middleware
    request_id = request.state.request_id

    # Pass to simulation service
    run_id = simulation_service.create_simulation(
        repo_name=body.repo_name,
        config_yaml=body.config_yaml,
        request_id=request_id,  # Pass through
    )

    # ... rest of endpoint ...
```

---

### Phase 4: Enhanced Logging Features (MEDIUM PRIORITY)

#### 4.1 Slow Request Warnings

Already included in `HTTPLoggingMiddleware` (Phase 2.2)

#### 4.2 Error Rate Tracking

**File:** `llm-sim-server/src/llm_sim_server/api/metrics.py` (NEW)

```python
"""Simple in-memory metrics tracking."""

from collections import defaultdict, deque
from datetime import datetime, timedelta
import threading

class MetricsTracker:
    """Track basic API metrics."""

    def __init__(self, window_minutes: int = 5):
        self.window = timedelta(minutes=window_minutes)
        self.errors = deque()  # (timestamp, endpoint)
        self.requests = deque()  # (timestamp, endpoint, duration_ms)
        self.lock = threading.Lock()

    def record_request(self, endpoint: str, duration_ms: float, status_code: int):
        """Record a completed request."""
        now = datetime.now()

        with self.lock:
            # Clean old entries
            cutoff = now - self.window
            while self.requests and self.requests[0][0] < cutoff:
                self.requests.popleft()

            self.requests.append((now, endpoint, duration_ms, status_code))

            # Track errors separately
            if status_code >= 400:
                while self.errors and self.errors[0][0] < cutoff:
                    self.errors.popleft()
                self.errors.append((now, endpoint))

    def get_error_rate(self) -> float:
        """Get error rate in last window."""
        with self.lock:
            if not self.requests:
                return 0.0

            error_count = len(self.errors)
            total_count = len(self.requests)

            return error_count / total_count if total_count > 0 else 0.0

    def get_avg_duration(self, endpoint: str = None) -> float:
        """Get average request duration."""
        with self.lock:
            filtered = [
                r for r in self.requests
                if endpoint is None or r[1] == endpoint
            ]

            if not filtered:
                return 0.0

            return sum(r[2] for r in filtered) / len(filtered)

# Global metrics instance
metrics = MetricsTracker()
```

Add to `HTTPLoggingMiddleware`:

```python
from llm_sim_server.api.metrics import metrics

class HTTPLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # ... existing code ...

        # Record metrics
        metrics.record_request(
            endpoint=request.url.path,
            duration_ms=duration_ms,
            status_code=response.status_code,
        )

        # Check error rate and log if high
        error_rate = metrics.get_error_rate()
        if error_rate > 0.1:  # 10% error rate
            logger.warning(
                "high_error_rate_detected",
                error_rate=round(error_rate, 3),
                window_minutes=5,
            )

        return response
```

#### 4.3 Resource Usage Logging

**File:** `llm-sim-server/src/llm_sim_server/manager/simulation_manager.py`

```python
import psutil

def _monitor_simulation_resources(self, run_id: str, process: Process):
    """Monitor and log resource usage of simulation subprocess."""
    try:
        p = psutil.Process(process.pid)

        while process.is_alive():
            try:
                cpu_percent = p.cpu_percent(interval=1.0)
                mem_mb = p.memory_info().rss / 1024 / 1024

                logger.debug(
                    "simulation_resources",
                    run_id=run_id,
                    cpu_percent=round(cpu_percent, 1),
                    memory_mb=round(mem_mb, 1),
                )

                # Warning for high usage
                if cpu_percent > 80 or mem_mb > 1024:
                    logger.warning(
                        "simulation_high_resource_usage",
                        run_id=run_id,
                        cpu_percent=round(cpu_percent, 1),
                        memory_mb=round(mem_mb, 1),
                    )

            except psutil.NoSuchProcess:
                break

            time.sleep(10)  # Check every 10 seconds

    except Exception as e:
        logger.error("resource_monitoring_failed", run_id=run_id, error=str(e))

# Start monitoring thread when subprocess starts
def start_simulation(self, ...):
    # ... existing code ...

    process.start()

    # Start resource monitoring in background thread
    monitor_thread = threading.Thread(
        target=self._monitor_simulation_resources,
        args=(run_id, process),
        daemon=True,
    )
    monitor_thread.start()

    # ... rest of method ...
```

#### 4.4 WebSocket Connection Tracking

**File:** `llm-sim-server/src/llm_sim_server/api/routes/stream.py`

Add connection tracking:

```python
from collections import defaultdict

# Track active connections per run_id
active_connections = defaultdict(set)

@router.websocket("/simulations/{run_id}/stream")
async def stream_simulation_events(websocket: WebSocket, run_id: str):
    await websocket.accept()

    # Track connection
    active_connections[run_id].add(websocket)
    connection_count = len(active_connections[run_id])

    logger.info(
        "websocket_connected",
        run_id=run_id,
        active_connections=connection_count,
    )

    try:
        # ... existing stream logic ...
    finally:
        # Remove connection
        active_connections[run_id].discard(websocket)
        logger.info(
            "websocket_disconnected",
            run_id=run_id,
            active_connections=len(active_connections[run_id]),
        )
```

---

### Phase 5: Production Configuration (LOW PRIORITY)

#### 5.1 Environment-based Configuration

**File:** `llm-sim-server/.env.example` (NEW)

```bash
# Logging Configuration
ENVIRONMENT=development  # or 'production'
LOG_LEVEL=INFO
LOG_FORMAT=auto  # 'console', 'json', or 'auto'

# Optional: External log aggregation
# LOG_AGGREGATOR_URL=http://loki:3100/loki/api/v1/push
# LOG_AGGREGATOR_ENABLED=false
```

#### 5.2 Update logging config to read environment

```python
import os

def configure_server_logging(
    level: str = None,
    format: str = None
) -> None:
    """Configure logging from environment or params."""

    level = level or os.getenv("LOG_LEVEL", "INFO")
    format = format or os.getenv("LOG_FORMAT", "auto")

    if format == "auto":
        env = os.getenv("ENVIRONMENT", "development")
        format = "json" if env == "production" else "console"

    # ... rest of config ...
```

#### 5.3 Log Aggregation (Optional)

For production deployments with ELK, Loki, etc.:

```python
# Add custom processor for external shipping
class LogAggregatorProcessor:
    """Ship logs to external aggregator."""

    def __init__(self, url: str):
        self.url = url
        self.session = httpx.AsyncClient()

    def __call__(self, logger, method_name, event_dict):
        # Ship to aggregator asynchronously
        asyncio.create_task(self._ship_log(event_dict))
        return event_dict

    async def _ship_log(self, event_dict):
        try:
            await self.session.post(self.url, json=event_dict)
        except Exception as e:
            # Don't fail logging if aggregator is down
            print(f"Log shipping failed: {e}", file=sys.stderr)

# Add to processors if enabled
if os.getenv("LOG_AGGREGATOR_ENABLED") == "true":
    processors.insert(0, LogAggregatorProcessor(
        url=os.getenv("LOG_AGGREGATOR_URL")
    ))
```

---

## Testing Plan

### Unit Tests

```python
# tests/test_logging_correlation.py

def test_request_id_propagation():
    """Test request_id flows from API to subprocess."""
    # Mock API request with request_id
    # Start simulation
    # Verify simulation logs contain same request_id
    pass

def test_log_context_binding():
    """Test context binding in structlog."""
    logger = get_logger(__name__)
    bound_logger = logger.bind(run_id="test-123")
    # Verify log output contains run_id
    pass

def test_subprocess_logging_isolation():
    """Test subprocess logs don't interfere."""
    # Start two simulations
    # Verify logs are properly separated by run_id
    pass
```

### Integration Tests

```python
# tests/integration/test_log_aggregation.py

async def test_end_to_end_logging():
    """Test API request → simulation → log correlation."""
    client = TestClient(app)

    # Make API request
    response = client.post("/simulations", json={...})
    request_id = response.headers["X-Request-ID"]
    run_id = response.json()["run_id"]

    # Wait for simulation
    # ...

    # Parse logs
    logs = parse_json_logs(log_output)

    # Verify correlation
    api_logs = [l for l in logs if l["request_id"] == request_id]
    sim_logs = [l for l in logs if l["run_id"] == run_id]

    assert len(api_logs) > 0
    assert len(sim_logs) > 0

    # Verify same request_id in simulation logs
    sim_with_request = [l for l in sim_logs if l.get("request_id") == request_id]
    assert len(sim_with_request) > 0
```

---

## Deployment Checklist

### llm_sim

- [ ] Update `utils/logging.py` with context binding support
- [ ] Update `orchestrator.py` to accept `log_context` parameter
- [ ] Update all `logger = structlog.get_logger()` to `structlog.get_logger(__name__)`
- [ ] Test subprocess logging with bound context

### llm-sim-server

- [ ] Add `structlog` to dependencies
- [ ] Create `utils/logging.py` with unified config
- [ ] Replace all `logging` imports with structlog
- [ ] Add `RequestIDMiddleware`
- [ ] Add `HTTPLoggingMiddleware`
- [ ] Update `simulation_manager.py` to pass `request_id` to subprocess
- [ ] Update API routes to extract and pass `request_id`
- [ ] Add metrics tracking (optional)
- [ ] Add resource monitoring (optional)
- [ ] Configure environment-based logging

### Testing

- [ ] Unit test context binding
- [ ] Unit test request ID propagation
- [ ] Integration test full correlation flow
- [ ] Load test with multiple concurrent simulations
- [ ] Verify log output format (console vs JSON)

### Documentation

- [ ] Update README with logging configuration
- [ ] Document correlation ID usage
- [ ] Add troubleshooting guide for logs
- [ ] Document metrics/monitoring features

---

## Expected Results

### Before (Current State)

```
# Server log (plaintext)
2025-10-06 09:08:33 - llm_sim_server.api.main - INFO - API started

# Simulation log (JSON, separate)
{"event": "simulation_starting", "timestamp": "2025-10-06T09:08:33.123Z", "name": "demo"}

# No correlation possible
```

### After (Target State)

```
# Unified console output (development)
2025-10-06 09:08:33 [info     ] http_request_started          method=POST path=/simulations request_id=abc-123
2025-10-06 09:08:33 [info     ] simulation_starting           method=POST path=/simulations request_id=abc-123 run_id=demo-20251006-090833 subprocess=true name=demo
2025-10-06 09:08:34 [info     ] turn_completed                request_id=abc-123 run_id=demo-20251006-090833 subprocess=true turn=1
2025-10-06 09:08:35 [info     ] simulation_completed          request_id=abc-123 run_id=demo-20251006-090833 subprocess=true final_turn=10
2025-10-06 09:08:35 [info     ] http_request_completed        method=POST path=/simulations request_id=abc-123 status_code=201 duration_ms=2043.5

# Unified JSON output (production)
{"event": "http_request_started", "timestamp": "2025-10-06T09:08:33.000Z", "method": "POST", "path": "/simulations", "request_id": "abc-123"}
{"event": "simulation_starting", "timestamp": "2025-10-06T09:08:33.123Z", "request_id": "abc-123", "run_id": "demo-20251006-090833", "subprocess": true, "name": "demo"}
...

# Easy to grep/filter by request_id or run_id
# Can trace entire request lifecycle
```

---

## Performance Impact

- **Minimal:** structlog is highly optimized
- **Context binding:** Near-zero overhead
- **JSON serialization:** ~5-10μs per log entry
- **Subprocess overhead:** Negligible (one-time setup)

**Recommendation:** Enable DEBUG logging only for specific components in production

---

## Maintenance

### Adding New Log Events

```python
# Always use structured logging
logger.info(
    "event_name",
    key1=value1,
    key2=value2,
    # Context (request_id, run_id) automatically included
)

# Never use f-strings
logger.info(f"Event: {value}")  # ❌ BAD - not structured

# Use structured keys
logger.info("event_name", value=value)  # ✅ GOOD
```

### Log Levels

- **DEBUG:** Detailed diagnostic info (observations, minor events)
- **INFO:** General informational events (requests, completions)
- **WARNING:** Unexpected but handled situations (slow requests, high error rate)
- **ERROR:** Error conditions that need attention (failures, exceptions)

### Monitoring

Watch for these log events in production:
- `high_error_rate_detected` - Error rate >10%
- `simulation_high_resource_usage` - CPU >80% or Memory >1GB
- `http_request_completed` with `slow_request=true` - Request >1s
- `event_queue_full_dropping` - Event writer dropping events

---

## Timeline Estimate

- **Phase 1 (Standardize):** 4-6 hours
- **Phase 2 (Correlation):** 3-4 hours
- **Phase 3 (Subprocess):** 4-6 hours
- **Phase 4 (Features):** 4-8 hours (optional)
- **Phase 5 (Production):** 2-3 hours
- **Testing:** 4-6 hours

**Total:** 21-33 hours (2-4 days)

---

## Success Criteria

✅ All logs use structlog (no stdlib logging)
✅ Request IDs propagate from API → subprocess
✅ Logs can be filtered by `request_id` or `run_id`
✅ Console output is readable with colors/alignment
✅ JSON output is valid and parseable
✅ HTTP requests/responses are logged with timing
✅ Slow requests (>1s) are flagged
✅ Subprocess logs include correlation context
✅ No log messages are lost during normal operation
✅ Performance overhead is <5% (negligible)

---

**Current Status:** 4/10 (fragmented, incompatible)
**Target Status:** 9/10 (production-ready, unified, traceable)
