# Features Implementation Roadmap

## Current Implementation Status

### ✅ Already Implemented
1. **Basic State Model**
   - GeopoliticalState with nations and relationships
   - Nation and Relationship models
   - Basic state transitions

2. **Basic Agent System**
   - Agent base class with abstract methods
   - BasicDiplomaticAgent implementation
   - Mock agents for testing

3. **Basic Validation**
   - Validator component
   - Basic validation rules

4. **Basic Game Engine**
   - Simple outcome processing
   - State updates based on actions

5. **Demo Systems**
   - File-based state persistence (JSON)
   - Basic simulation runners (demo.py, showcase_demo.py)
   - CSV export utility (extract_history.py)

### 🔄 Partially Implemented
1. **State Architecture**
   - ✅ Global state exists
   - ❌ Three-layer model not fully separated
   - ❌ Agent decision-making state not persistent

2. **Data Collection**
   - ✅ Basic action/outcome tracking
   - ❌ No database persistence
   - ❌ Limited metrics collection

---

## Feature Groups for Implementation

### Feature 1: Three-Layer State Architecture
**Priority: High** | **Complexity: Medium**

#### Specifications
- Separate Agent State into two parts:
  - Decision-Making State (agent memory/learning)
  - Game Values State (resources/attributes)
- Implement proper access controls
- Add state layer validation

#### Tasks
1. Refactor state models to support three layers
2. Create AgentMemory class for decision-making state
3. Update Agent base class to use both state types
4. Add access control enforcement in StateManager
5. Update existing agents to use new architecture

#### Files to Modify
- `src/llm_sim/state/models.py` - Add new state models
- `src/llm_sim/agents/base.py` - Update Agent interface
- `src/llm_sim/state/manager.py` - Add access controls

---

### Feature 2: State Persistence & Checkpointing
**Priority: High** | **Complexity: Low**

#### Specifications
- Standardized state file format with versioning
- Compression support for large simulations
- Resume from any saved turn
- State file indexing for quick discovery

#### Tasks
1. Create StateSerializer with version support
2. Add compression options (gzip/bzip2)
3. Implement checkpoint/resume functionality
4. Create state file index manager
5. Add integrity checks (checksums)

#### Files to Create
- `src/llm_sim/persistence/serializer.py`
- `src/llm_sim/persistence/checkpoint.py`
- `src/llm_sim/persistence/index.py`

---

### Feature 3: Database Persistence Layer
**Priority: Medium** | **Complexity: High**

#### Specifications
- Real-time data collection during simulation
- Structured storage for analysis
- Support for SQLite (dev) and PostgreSQL (prod)
- Efficient bulk inserts

#### Tasks
1. Design database schema (using SQLAlchemy)
2. Create DatabaseCollector class
3. Add hooks to simulation engine
4. Implement bulk insert optimization
5. Create migration system
6. Add query interfaces

#### Files to Create
- `src/llm_sim/db/models.py` - SQLAlchemy models
- `src/llm_sim/db/collector.py` - Data collection
- `src/llm_sim/db/queries.py` - Common queries
- `migrations/` - Database migrations

---

### Feature 4: Plugin Architecture
**Priority: Low** | **Complexity: Medium**

#### Specifications
- Dynamic loading of simulation types
- Pluggable agent strategies
- Custom validation rules
- Configurable game engines

#### Tasks
1. Create plugin base classes
2. Implement plugin discovery mechanism
3. Add configuration system for plugins
4. Create example plugins
5. Document plugin API

#### Files to Create
- `src/llm_sim/plugins/base.py`
- `src/llm_sim/plugins/loader.py`
- `plugins/simulations/` - Simulation plugins
- `plugins/agents/` - Agent plugins

---

### Feature 5: Advanced Agent Strategies
**Priority: Medium** | **Complexity: Medium**

#### Specifications
- Rule-based agents with configurable logic
- LLM-reasoning agents (using Ollama/OpenAI)
- Learning agents that improve over time
- Hybrid strategies

#### Tasks
1. Create RuleBasedAgent class
2. Implement LLMReasoningAgent with prompts
3. Add learning mechanism to agents
4. Create strategy mixer for hybrid agents
5. Add performance tracking

#### Files to Create
- `src/llm_sim/agents/rule_based.py`
- `src/llm_sim/agents/llm_reasoning.py`
- `src/llm_sim/agents/learning.py`
- `src/llm_sim/agents/hybrid.py`

---

### Feature 6: Simulation Types System
**Priority: Medium** | **Complexity: High**

#### Specifications
- Configurable simulation domains
- Domain-specific value sets
- Custom game engines per type
- Flexible time scales

#### Tasks
1. Create SimulationType base class
2. Implement economic simulation type
3. Implement military simulation type
4. Create configuration system
5. Add domain-specific validators

#### Files to Create
- `src/llm_sim/simulations/base.py`
- `src/llm_sim/simulations/economic.py`
- `src/llm_sim/simulations/military.py`
- `src/llm_sim/simulations/config.py`

---

### Feature 7: Training Data Pipeline
**Priority: Low** | **Complexity: Medium**

#### Specifications
- Export to standard ML formats
- SARNS tuple generation
- Performance metrics tracking
- Strategy effectiveness analysis

#### Tasks
1. Create training data extractor
2. Implement SARNS formatter
3. Add performance analyzers
4. Create export to TensorFlow/PyTorch formats
5. Build evaluation metrics

#### Files to Create
- `src/llm_sim/ml/extractor.py`
- `src/llm_sim/ml/formatters.py`
- `src/llm_sim/ml/metrics.py`

---

### Feature 8: Real-time Monitoring
**Priority: Low** | **Complexity: Low**

#### Specifications
- Live metrics dashboard
- WebSocket for real-time updates
- Performance profiling
- Alert system for critical events

#### Tasks
1. Create metrics collector
2. Implement WebSocket server
3. Build simple web dashboard
4. Add alerting rules
5. Create performance profiler

#### Files to Create
- `src/llm_sim/monitoring/collector.py`
- `src/llm_sim/monitoring/server.py`
- `src/llm_sim/monitoring/dashboard/`

---

## Implementation Order

### Phase 1: Core Architecture (1-2 weeks)
1. **Feature 1**: Three-Layer State Architecture
2. **Feature 2**: State Persistence & Checkpointing

### Phase 2: Data & Persistence (2-3 weeks)
3. **Feature 3**: Database Persistence Layer
4. **Feature 7**: Training Data Pipeline (basic)

### Phase 3: Extensibility (2-3 weeks)
5. **Feature 6**: Simulation Types System
6. **Feature 5**: Advanced Agent Strategies

### Phase 4: Advanced Features (2-3 weeks)
7. **Feature 4**: Plugin Architecture
8. **Feature 8**: Real-time Monitoring

---

## Next Steps

1. **Immediate** (This Week):
   - Start with Feature 1: Three-Layer State Architecture
   - Create detailed design doc for state separation
   - Write tests for new state model

2. **Short Term** (Next 2 Weeks):
   - Complete Feature 2: State Persistence
   - Begin Feature 3: Database design

3. **Medium Term** (Next Month):
   - Have Phase 1 & 2 complete
   - Start on simulation types

---

## Dependencies

### Required Libraries (Not Yet Added)
```toml
# For Database (Feature 3)
sqlalchemy = "^2.0"
alembic = "^1.13"  # migrations
psycopg2-binary = "^2.9"  # PostgreSQL

# For Monitoring (Feature 8)
fastapi = "^0.104"
uvicorn = "^0.24"
websockets = "^12.0"

# For ML Pipeline (Feature 7)
numpy = "^1.24"
pandas = "^2.0"
```

### Development Tools Needed
- Database viewer (e.g., DBeaver)
- API testing tool (e.g., Postman)
- Performance profiler

---

## Risk Factors

1. **Three-Layer State**: May break existing code
   - Mitigation: Extensive testing, gradual migration

2. **Database Performance**: Could slow down simulations
   - Mitigation: Async writes, bulk operations

3. **Plugin System**: Complex to get right
   - Mitigation: Start simple, iterate

4. **LLM Integration**: External dependency
   - Mitigation: Fallback to rule-based agents