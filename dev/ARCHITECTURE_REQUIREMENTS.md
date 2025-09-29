# System Architecture Requirements

## Core Architectural Principles
- **Separation of Concerns**: Simulation dynamics vs Decision-making strategies
- **Reusability**: Agent implementations work across all simulation types
- **Extensibility**: Easy to add new simulation types and agent strategies
- **Data Collection**: Built-in support for metrics and training data capture

## State Architecture

### Three-Layer State Model

#### 1. Global State (Environment State)
**Purpose**: Represents the shared world/environment all agents operate in
- **Characteristics**:
  - Read-only for agents
  - Updated only by game engine after processing actions
  - Contains shared resources, global events, world conditions
  - Defines environmental constraints and rules
- **Examples**:
  - Global market prices
  - Weather/climate conditions
  - Available world resources
  - International laws/treaties in effect
  - Global crisis events

#### 2. Agent State (Two-Part Structure)

##### 2.1 Decision-Making State (Agent Memory)
**Purpose**: Agent's private workspace for improving decisions
- **Characteristics**:
  - Fully controlled by the agent
  - Persists across turns
  - Agent can read/write freely
  - Not validated by game engine
  - Used for learning and strategy
- **Examples**:
  - Historical observations
  - Pattern recognition data
  - Strategy parameters
  - Learned opponent behaviors
  - Internal goals and plans
  - Custom variables/flags
  - Decision trees or weights

##### 2.2 Game Values State (Agent Resources)
**Purpose**: Agent's resources and attributes in the game
- **Characteristics**:
  - Read-only for agents
  - Modified only by game engine
  - Subject to validation rules
  - Defines what agent can do
  - Simulation-specific values
- **Examples**:
  - Economic: money, debt, trade capacity
  - Military: troops, equipment, territories
  - Demographic: population, happiness, education
  - Diplomatic: reputation, alliances, treaties
  - Resources: oil, food, minerals

### State Management Rules

#### Initialization
- Simulation configuration defines which game values exist
- Each simulation type specifies its tracked values
- Agents start with empty decision-making state
- Game values initialized from scenario configuration

#### State Access Patterns
**Agents CAN**:
- Read global state
- Read own game values
- Read/write own decision-making state
- See other agents' public game values (configurable)

**Agents CANNOT**:
- Modify global state
- Modify own game values
- Access other agents' decision-making state
- See other agents' private game values (if configured)

#### State Updates
**Each Turn**:
1. Agents receive current global state
2. Agents receive own complete state (both parts)
3. Agents update decision-making state as needed
4. Agents submit actions based on analysis
5. Game engine validates actions
6. Game engine updates game values based on outcomes
7. Game engine updates global state
8. Complete state snapshot saved to file

### State Persistence and Checkpointing

#### Turn-Based State Files
- **Complete Snapshot Per Turn**: Each turn generates a state file containing:
  - Full global state
  - All agents' complete states (both decision-making and game values)
  - Turn metadata (number, timestamp, processing time)
  - Actions taken this turn
  - Outcomes generated
  - Random seeds for reproducibility

#### State File Features
- **Serialization Format**: JSON, MessagePack, or Protocol Buffers for efficiency
- **Compression**: Optional compression for large simulations
- **Versioning**: Schema version for backward compatibility
- **Checksums**: Integrity verification for state files

#### Use Cases for State Files
- **Simulation Resume**: Restart from any saved turn
- **Replay Analysis**: Step through simulation history
- **Debugging**: Investigate specific turn behaviors
- **Training Data**: Extract state sequences for ML
- **Branching Scenarios**: Create alternate timelines from any point
- **Fault Recovery**: Resume after system failures

#### State File Management
- **Storage Strategy**:
  - Configurable retention (keep all, every N turns, or last X turns)
  - Hierarchical storage (recent in fast storage, older archived)
  - Incremental/differential saves option for efficiency
- **File Naming**: `{simulation_id}_turn_{number}_{timestamp}.state`
- **Metadata Index**: Separate index file for quick state file discovery

## Simulation System Requirements

### Simulation Type Definition
- Each simulation type defines its own domain (economic, military, demographic, ecological, etc.)
- Specifies which metrics/values to track (money, population, resources, territory, etc.)
- Defines the dynamics and rules of that domain
- Determines the granularity level (city, nation, continent, global)
- Specifies time scales and turn progression rules

### Simulation-Specific Value Sets

#### Configuration Defines
- Which game values each agent tracks
- Initial values for each metric
- Value ranges and constraints
- Update rules and formulas
- Visibility rules (public/private)

#### Value Categories
- **Quantitative**: Numeric values (money, population)
- **Categorical**: States/statuses (ally/neutral/enemy)
- **Boolean**: Flags (at_war, has_nuclear)
- **Complex**: Structured data (trade_agreements[])

### Game Engine Flexibility
- Each simulation type has its own specialized game engine
- Engines understand domain-specific action processing
- Conflict resolution appropriate to the domain
- Outcome calculation based on simulation dynamics
- State transition rules specific to simulation type
- Responsible for updating agent game values and global state

## Agent System Requirements

### Agent Strategy Types
- Random agents for baseline behavior
- Rule-based agents with configurable logic
- Reasoning agents using LLM-based decision making
- AI agents using trained models
- Hybrid agents combining multiple strategies

### Agent Capabilities
- Receive simulation state in generic format
- Maintain internal persistent state across turns
- Make decisions independent of simulation type
- Return actions in standardized format
- Work with any simulation type without modification

### Data Collection Infrastructure
- Automatic recording of all state observations
- Capture of agent analysis and reasoning process
- Storage of actions taken and their parameters
- Recording of outcomes and rewards received
- Time-series tracking of agent performance
- Separate tracking of decision-making state evolution
- Game value trajectories per agent

### Training Data Requirements
- Standardized export formats for ML pipelines
- State-action-reward-next-state (SARNS) tuples
- Metadata about simulation context
- Agent decision reasoning traces
- Performance metrics over time
- Decision-making state snapshots for strategy learning
- Correlation data between agent memory and action success

### Data Collection Implications

#### For Training
- Complete state snapshots each turn (all three layers)
- Decision-making state evolution patterns
- Action-outcome correlations with state context
- Game value trajectories
- Strategy effectiveness metrics

#### For Analysis
- Decision-making patterns and memory usage
- Strategy effectiveness across different simulations
- Resource utilization efficiency
- State-action mappings
- Learning progression over time

## Integration Requirements

### Configuration System
- Simulation templates defining complete setups
- Agent pool specifications (which agents, how many)
- Scenario definitions with initial conditions
- Validation rule sets per simulation type
- Runtime parameter overrides

### Metrics and Monitoring
- Real-time performance tracking per agent
- Simulation-wide aggregate metrics
- Comparison across different agent strategies
- Validation success/failure rates
- Resource usage and timing statistics

### Experimentation Support
- Run same scenario with different agent mixes
- A/B testing of agent strategies
- Parameter sweeps for optimization
- Reproducible runs with seed control
- Batch execution capabilities

## Technical Requirements

### Modularity
- Plugin architecture for new simulation types
- Plugin architecture for new agent strategies
- Composable validation rules
- Swappable game engines
- Configurable output formatters

### Performance
- Efficient state representation
- Parallelizable agent decision-making
- Scalable to many agents
- Optimized history storage
- Fast state transitions

### Observability
- Detailed logging per component
- Trace agent decision paths
- Monitor simulation progression
- Debug action validation failures
- Profile performance bottlenecks

This architecture enables running diverse simulations (economic, military, demographic) with the same pool of agent implementations (random, rule-based, AI), while collecting comprehensive training data for future agent improvement.

## Data Export and Analysis

### Time-Series Data Extraction
Since state files contain only point-in-time snapshots, analysis tools must reconstruct history by reading multiple files.

#### State File Clarification
- Each state file is a complete snapshot at one turn
- No cumulative history stored in individual files
- Keeps file sizes small and consistent
- Simplifies state management

#### History Reconstruction Utility
Simple extractor that:
1. Loads all state files from a session directory
2. Reads files in chronological order (by turn number)
3. Builds complete time-series data
4. Exports to CSV for analysis

#### Extractable Time-Series Data
- **Agent Metrics Over Time**
  - GDP, military strength, population per turn
  - Resources and policies evolution
  - Action success rates

- **Relationship Evolution**
  - Trust levels trajectory
  - Trade volume changes
  - Diplomatic status transitions

- **Action Sequences**
  - What action was taken when
  - By which agent against which target
  - Success/failure outcomes
  - Enables causation analysis

- **Global Trends**
  - System-wide aggregates per turn
  - Emergence detection (wars, alliances)
  - Stability indicators

#### Simple CSV Export Format
```bash
python extract_history.py --session outputs/simulation_results/session_20250922_081310
```

Generates:
- `agents_timeline.csv` - One row per agent per turn
- `relationships_timeline.csv` - One row per relationship per turn
- `actions_log.csv` - One row per action taken
- `global_metrics.csv` - System aggregates per turn

#### Benefits
- No changes to core simulation
- State files remain simple snapshots
- Analysis complexity isolated to export tools
- Users can analyze in any tool (Excel, Python, R)

## Database Persistence Requirements

### Purpose
Provide persistent, queryable storage for simulation data to enable:
- Real-time analytics during simulations
- Historical analysis across multiple runs
- Pattern detection and machine learning
- Performance tracking and comparison

### What to Store in Database

#### Core Simulation Data (Required)
1. **Simulation Sessions**
   - Session ID, start/end time, configuration
   - Simulation type and scenario name
   - Total turns completed, final status

2. **Actions Table**
   - Action ID, session ID, turn number, timestamp
   - Agent ID, action type, target
   - Priority, confidence, success/failure
   - Full reasoning text (for analysis)
   - Validation status and score

3. **State Snapshots** (Selective)
   - Turn-level summaries only (not full state)
   - Key metrics per agent per turn
   - Relationship metrics per turn
   - Global aggregates per turn

4. **Outcomes Table**
   - Outcome ID, triggering action ID
   - Outcome type, affected entities
   - Magnitude of change
   - Success/failure flag

#### What NOT to Store in Database
- Full state JSON blobs (keep in files for replay)
- Temporary calculation values
- Debug/trace information
- Raw LLM responses (unless specifically needed)

### When to Store Data

#### Real-time Writes (During Simulation)
- **After each action decision**: Store action with context
- **After validation**: Update action with validation result
- **After outcome processing**: Store outcomes linked to actions
- **End of turn**: Store turn summary metrics

#### Batch Writes (Post-Simulation)
- Agent performance statistics
- Relationship evolution summaries
- Pattern analysis results

### Storage Strategy

#### Hybrid Approach
1. **Database**: Structured, queryable data for analysis
2. **File System**: Complete state snapshots for replay
3. **Relationship**: Database references file paths for full states

#### Database Requirements
- Support for time-series queries
- Efficient bulk inserts for turn data
- Foreign key relationships (actions → outcomes)
- Indexing on session_id, turn_number, agent_id
- Text search capability for reasoning/descriptions

#### Data Retention
- Active simulations: Full detail in database
- Completed simulations: Configurable retention
  - Keep summary data indefinitely
  - Archive detailed records after N days
  - Option to export before deletion

### Query Patterns to Support

#### Analysis Queries
- "Show all actions by agent X in session Y"
- "Compare success rates across different agent types"
- "Find all diplomatic actions that led to war"
- "Track trust evolution between specific nations"
- "Identify action patterns before relationship changes"

#### Performance Queries
- "Average decision time per agent type"
- "Validation pass/fail rates by action type"
- "Most successful strategies by scenario"

#### Training Data Queries
- "Extract all state-action-outcome sequences"
- "Get all decisions made in similar contexts"
- "Find high-confidence actions that failed"

### Database Schema Considerations

#### Tables Needed
- sessions (id, type, config, start_time, end_time)
- agents (id, session_id, type, config)
- actions (id, session_id, turn, agent_id, type, target, ...)
- validations (action_id, is_valid, score, reason)
- outcomes (id, action_id, type, magnitude, success)
- turn_metrics (session_id, turn, agent_id, metrics_json)
- relationships (session_id, turn, nation_a, nation_b, trust, trade)

#### Indexing Strategy
- Primary: id fields
- Foreign keys: all _id references
- Composite: (session_id, turn_number)
- Search: action_type, outcome_type
- Performance: created_at timestamps

### Integration Points

#### Simulation Engine Hooks
- Pre-action: Log decision context
- Post-validation: Store validation result
- Post-outcome: Link outcomes to actions
- Turn-end: Calculate and store metrics

#### Analysis Tools
- Direct SQL access for ad-hoc queries
- Python/R connectors for analysis
- Export capabilities to CSV/Parquet
- Real-time dashboards via database views

### Benefits Over File-Only Approach
- Query specific data without loading all files
- Real-time monitoring during long simulations
- Cross-simulation pattern analysis
- Efficient aggregations and statistics
- Causation chain tracking via foreign keys  