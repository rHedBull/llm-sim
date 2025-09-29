# StateManager Integration & Database Persistence Plan

## Current Architecture Issues

### 1. StateManager is Underutilized
- **Created but not used** in SimulationCoordinator
- Only used indirectly through GameEngine
- Missing key integration points for state history, rollback, and persistence

### 2. No Database Persistence
- States only stored in memory (`List[GeopoliticalState]`)
- No ability to resume simulations
- No historical analysis capabilities
- Lost data on crashes

## Proposed Architecture

### Layer 1: Proper StateManager Integration

The StateManager should be the **single source of truth** for all state operations:

```python
# SimulationCoordinator should use StateManager directly:
class SimulationCoordinator:
    async def initialize_simulation(self, config):
        # Initialize state through StateManager
        initial_state = self.state_manager.create_state(config.initial_state)
        self.state_manager.initialize_state(initial_state)
        self.current_state = self.state_manager.get_current_state()

    async def process_turn(self):
        # All state transitions through StateManager
        new_state = await self.game_engine.process_turn(actions, current_state)
        self.state_manager.add_state(new_state)

        # Checkpoint periodically
        if turn_number % 5 == 0:
            await self.state_manager.save_checkpoint()
```

### Layer 2: Database Persistence

Add database support to StateManager for production use:

```python
class StateManager:
    def __init__(self, db_config: Optional[DatabaseConfig] = None):
        self._state_history: List[GeopoliticalState] = []
        self.db_enabled = db_config is not None
        if self.db_enabled:
            self.db = StateDatabase(db_config)

    async def add_state(self, state: GeopoliticalState):
        """Add state to history and optionally persist to database"""
        self._state_history.append(state)

        if self.db_enabled:
            await self.db.save_state(state)

    async def save_checkpoint(self, checkpoint_name: str = None):
        """Save current simulation state to database"""
        if not self.db_enabled:
            return

        checkpoint = {
            'name': checkpoint_name or f"checkpoint_{datetime.now().isoformat()}",
            'turn_number': self.get_current_state().turn_number,
            'state': self.serialize_state(self.get_current_state()),
            'history_size': len(self._state_history)
        }
        await self.db.save_checkpoint(checkpoint)

    async def load_checkpoint(self, checkpoint_name: str):
        """Load simulation from database checkpoint"""
        if not self.db_enabled:
            raise RuntimeError("Database not configured")

        checkpoint = await self.db.load_checkpoint(checkpoint_name)
        self._state_history = await self.db.load_history(
            up_to_turn=checkpoint['turn_number']
        )
        return self.deserialize_state(checkpoint['state'])
```

## Database Schema Design

### Tables

#### 1. simulations
```sql
CREATE TABLE simulations (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP,
    config JSONB,
    status VARCHAR(50),
    metadata JSONB
);
```

#### 2. states
```sql
CREATE TABLE states (
    id UUID PRIMARY KEY,
    simulation_id UUID REFERENCES simulations(id),
    turn_number INTEGER,
    timestamp TIMESTAMP,
    state_data JSONB,  -- Full state serialized
    state_hash VARCHAR(64),  -- For integrity checking
    created_at TIMESTAMP
);
```

#### 3. checkpoints
```sql
CREATE TABLE checkpoints (
    id UUID PRIMARY KEY,
    simulation_id UUID REFERENCES simulations(id),
    name VARCHAR(255),
    turn_number INTEGER,
    state_id UUID REFERENCES states(id),
    created_at TIMESTAMP,
    metadata JSONB
);
```

#### 4. state_transitions
```sql
CREATE TABLE state_transitions (
    id UUID PRIMARY KEY,
    simulation_id UUID REFERENCES simulations(id),
    from_state_id UUID REFERENCES states(id),
    to_state_id UUID REFERENCES states(id),
    actions JSONB,
    outcomes JSONB,
    processing_time_ms INTEGER,
    created_at TIMESTAMP
);
```

## Implementation Benefits

### 1. Production Features
- **Crash Recovery**: Resume from last checkpoint
- **Time Travel**: Replay from any point
- **Analytics**: Query historical patterns
- **Debugging**: Inspect state at any turn
- **Auditing**: Complete state history

### 2. Performance Benefits
- **Lazy Loading**: Only load states as needed
- **Pagination**: Handle long simulations
- **Parallel Simulations**: Multiple runs with shared checkpoints
- **Caching**: In-memory cache with DB backing

### 3. Testing Benefits
- **Reproducibility**: Exact state replay
- **Regression Testing**: Compare outcomes across versions
- **Performance Testing**: Benchmark with real data

## Implementation Steps

### Phase 1: Fix StateManager Integration (2 hours)
1. Update SimulationCoordinator to use StateManager properly
2. Implement state history tracking
3. Add basic checkpoint/restore in memory
4. Fix related integration tests

### Phase 2: Add Database Layer (4 hours)
1. Design database schema
2. Add SQLAlchemy models or similar
3. Implement StateDatabase class
4. Add async save/load methods
5. Add connection pooling

### Phase 3: Integration & Testing (2 hours)
1. Update configuration to support DB settings
2. Add migration scripts
3. Create integration tests with test database
4. Add performance benchmarks

## Configuration Example

```yaml
simulation:
  state_management:
    persistence:
      enabled: true
      type: postgresql  # or sqlite for development
      connection:
        host: localhost
        port: 5432
        database: llm_sim
        username: sim_user
      options:
        pool_size: 10
        checkpoint_interval: 5  # turns
        compress_states: true
        retention_days: 90
```

## Testing Strategy

1. **Unit Tests**: Mock database, test StateManager logic
2. **Integration Tests**: Use SQLite in-memory for fast tests
3. **E2E Tests**: Full PostgreSQL with test data
4. **Performance Tests**: Benchmark large state operations

## Expected Outcomes

After implementation:
- All state-related integration tests passing
- Checkpoint/restore functionality working
- Database persistence optional but fully functional
- Foundation for production deployment
- Better debugging and analysis capabilities

## Notes

- Database is **optional** - system works without it
- Start with SQLite for simplicity, migrate to PostgreSQL for production
- Consider using Alembic for database migrations
- Add metrics for state operation performance