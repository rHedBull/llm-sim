# Real-Time Simulation Architecture

**Feature Proposal:** Add event-driven real-time simulation mode alongside existing turn-based system

**Status:** Design Phase

**Last Updated:** 2025-10-01

---

## Table of Contents

- [Overview](#overview)
- [Current Architecture (Turn-Based)](#current-architecture-turn-based)
- [Proposed Architecture (Real-Time)](#proposed-architecture-real-time)
- [Key Differences](#key-differences)
- [Design Options](#design-options)
- [Implementation Strategy](#implementation-strategy)
- [LLM Integration Challenges](#llm-integration-challenges)
- [State & Checkpointing](#state--checkpointing)
- [API Changes](#api-changes)
- [Trade-offs & Considerations](#trade-offs--considerations)
- [Use Cases](#use-cases)
- [Timeline](#timeline)

---

## Overview

### Current System: Turn-Based Synchronous

The current `llm-sim` framework operates in **discrete turns**:
1. All agents receive the same state
2. All agents decide actions synchronously (or async but wait for all)
3. Validator validates all actions
4. Engine applies all actions + rules atomically
5. Turn counter increments, repeat

**Clock model:** Integer turn counter (`turn: int`)

**Time semantics:** One "turn" = abstract time unit (could be 1 second, 1 day, 1 year)

### Proposed System: Real-Time Event-Driven

The real-time mode operates with a **continuous clock**:
1. Simulation starts with `t=0.0` (wall-clock or simulated time)
2. Agents can act asynchronously at any time `t`
3. Events are scheduled and processed based on timestamps
4. Engine continuously updates state based on event stream
5. LLMs can "think" and respond with variable latency

**Clock model:** Floating-point timestamp (`time: float` in seconds)

**Time semantics:** Explicit time intervals (e.g., `t=5.3s` means 5.3 seconds into simulation)

---

## Current Architecture (Turn-Based)

### Orchestrator Flow

```python
# orchestrator.py _run_sync()
state = engine.initialize_state()  # turn=0

while not engine.check_termination(state):
    # Phase 1: All agents decide (synchronous)
    for agent in agents:
        agent.receive_state(state)

    actions = [agent.decide_action(state) for agent in agents]

    # Phase 2: Validate all actions
    validated_actions = validator.validate_actions(actions, state)

    # Phase 3: Apply all actions + engine rules atomically
    state = engine.run_turn(validated_actions)

    # turn increments inside run_turn()
```

**Key characteristics:**
- ✅ Deterministic (same inputs → same outputs)
- ✅ Easy to debug (step through turns)
- ✅ Simple checkpointing (save after each turn)
- ✅ No race conditions
- ❌ Unrealistic timing (all agents act simultaneously)
- ❌ No variable latency (all decisions take "one turn")
- ❌ LLM response time not modeled

### State Model

```python
class SimulationState(BaseModel):
    turn: int                          # Discrete turn counter
    agents: Dict[str, BaseModel]       # Agent states
    global_state: BaseModel            # World state
    reasoning_chains: List[...]        # LLM traces
```

### Engine Interface

```python
class BaseEngine(ABC):
    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute one discrete turn."""
        new_state = self.apply_actions(actions)
        new_state = self.apply_engine_rules(new_state)
        return new_state
```

---

## Proposed Architecture (Real-Time)

### Event-Driven Model

```
Timeline (continuous):
t=0.0s ──┬──> t=2.3s ──┬──> t=3.7s ──┬──> t=5.1s ──┬──> ...
         │             │             │             │
      [Event]       [Event]       [Event]       [Event]
    Agent1 acts   Agent2 acts   Engine rule   Agent1 acts
    "buy stock"   "sell stock"  "update       "check prices"
                                 prices"
```

**Events** are timestamped actions/updates that modify state.

### Event Types

1. **Agent Actions** - Decisions from agents (e.g., "buy stock at t=2.3s")
2. **Engine Events** - Periodic rules (e.g., "apply interest every 10s")
3. **External Events** - Injected by control server (e.g., "market crash at t=50s")
4. **Scheduled Events** - Pre-planned (e.g., "agent will decide again at t=15.0s")

### Core Components

#### 1. Event Queue (Priority Queue)

```python
from queue import PriorityQueue
from dataclasses import dataclass, field
from typing import Any

@dataclass(order=True)
class Event:
    """Timestamped event in the simulation."""

    timestamp: float = field(compare=True)      # When event occurs
    priority: int = field(default=0, compare=True)  # Tie-breaker
    event_type: str = field(compare=False)      # "agent_action", "engine_rule", etc.
    data: Any = field(compare=False)            # Event payload (Action, etc.)

class EventQueue:
    """Priority queue for event-driven simulation."""

    def __init__(self):
        self.queue = PriorityQueue()
        self.current_time = 0.0

    def schedule(self, event: Event):
        """Add event to queue."""
        self.queue.put(event)

    def next_event(self) -> Event:
        """Get next event and advance clock."""
        event = self.queue.get()
        self.current_time = event.timestamp
        return event

    def peek_time(self) -> float:
        """Get timestamp of next event without removing."""
        return self.queue.queue[0].timestamp if not self.queue.empty() else float('inf')
```

#### 2. Real-Time State Model

```python
class RealTimeSimulationState(BaseModel):
    """State for real-time simulations."""

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    # Time tracking
    timestamp: float                    # Current simulation time (seconds)
    elapsed_real_time: float           # Wall-clock time elapsed (for metrics)

    # State
    agents: Dict[str, BaseModel]       # Agent states
    global_state: BaseModel            # World state

    # Event tracking
    pending_events: int                # Number of events in queue
    processed_events: int              # Total events processed

    # LLM tracking (optional)
    reasoning_chains: List[LLMReasoningChain] = Field(default_factory=list)
    agents_thinking: List[str] = Field(default_factory=list)  # Agents currently calling LLM
```

#### 3. Real-Time Engine Base Class

```python
class BaseRealTimeEngine(ABC):
    """Abstract base for real-time event-driven engines."""

    def __init__(self, config: SimulationConfig):
        self.config = config
        self.event_queue = EventQueue()
        self._state: Optional[RealTimeSimulationState] = None

    @abstractmethod
    def initialize_state(self) -> RealTimeSimulationState:
        """Create initial state at t=0."""
        pass

    @abstractmethod
    def process_event(self, event: Event, state: RealTimeSimulationState) -> RealTimeSimulationState:
        """Process single event and return new state.

        Args:
            event: Event to process (contains timestamp, type, data)
            state: Current state before event

        Returns:
            New state after processing event
        """
        pass

    @abstractmethod
    def schedule_engine_events(self, current_time: float, state: RealTimeSimulationState):
        """Schedule periodic engine events (e.g., interest calculations).

        Args:
            current_time: Current simulation time
            state: Current state

        Side effects:
            Adds events to self.event_queue
        """
        pass

    @abstractmethod
    def check_termination(self, state: RealTimeSimulationState) -> bool:
        """Check if simulation should end.

        Args:
            state: Current state

        Returns:
            True if simulation should terminate
        """
        pass
```

#### 4. Real-Time Agent Base Class

```python
class BaseRealTimeAgent(ABC):
    """Abstract base for agents in real-time simulations."""

    def __init__(self, name: str):
        self.name = name
        self._current_state: Optional[RealTimeSimulationState] = None
        self._next_decision_time: Optional[float] = None

    @abstractmethod
    async def decide_action_async(
        self,
        state: RealTimeSimulationState,
        current_time: float
    ) -> Optional[Action]:
        """Decide action asynchronously at given time.

        Args:
            state: Current simulation state
            current_time: Current simulation time

        Returns:
            Action to take, or None if no action

        Note:
            This method can take variable time to execute (LLM calls).
            The timestamp of the returned action should reflect when
            the decision completes, not when it started.
        """
        pass

    @abstractmethod
    def get_next_decision_time(self, current_time: float, state: RealTimeSimulationState) -> float:
        """Get next time this agent wants to make a decision.

        Args:
            current_time: Current simulation time
            state: Current state

        Returns:
            Future timestamp when agent will act again

        Examples:
            - Periodic: return current_time + 10.0  # every 10 seconds
            - Reactive: return current_time + 1.0 if state.needs_attention else float('inf')
            - Random: return current_time + random.uniform(5, 15)
        """
        pass

    def receive_state(self, state: RealTimeSimulationState):
        """Receive state update (called on every event)."""
        self._current_state = state
```

#### 5. Real-Time Orchestrator

```python
class RealTimeOrchestrator:
    """Orchestrator for real-time event-driven simulations."""

    def __init__(
        self,
        config: SimulationConfig,
        engine: BaseRealTimeEngine,
        agents: List[BaseRealTimeAgent],
        validator: BaseValidator,
        time_scale: float = 1.0,  # Speed multiplier (1.0 = real-time, 0.1 = slow-mo, 10.0 = fast-forward)
        max_sim_time: float = 3600.0,  # Max simulation time (seconds)
    ):
        self.config = config
        self.engine = engine
        self.agents = agents
        self.validator = validator
        self.time_scale = time_scale
        self.max_sim_time = max_sim_time

        self.start_time = datetime.now()
        self.real_time_elapsed = 0.0

    async def run(self) -> Dict[str, Any]:
        """Run real-time simulation."""
        logger.info("realtime_simulation_starting", max_sim_time=self.max_sim_time)

        # Initialize state
        state = self.engine.initialize_state()

        # Schedule initial agent decision events
        for agent in self.agents:
            decision_time = agent.get_next_decision_time(0.0, state)
            self.engine.event_queue.schedule(Event(
                timestamp=decision_time,
                event_type="agent_decision",
                data={"agent": agent}
            ))

        # Schedule initial engine events
        self.engine.schedule_engine_events(0.0, state)

        # Main event loop
        while not self.engine.check_termination(state):
            # Get next event
            if self.engine.event_queue.queue.empty():
                logger.info("event_queue_empty", stopping=True)
                break

            event = self.engine.event_queue.next_event()
            current_time = event.timestamp

            # Check termination by time
            if current_time > self.max_sim_time:
                logger.info("max_sim_time_reached", time=current_time)
                break

            # Process event based on type
            if event.event_type == "agent_decision":
                state = await self._process_agent_decision(event, state, current_time)

            elif event.event_type == "engine_rule":
                state = self.engine.process_event(event, state)

            elif event.event_type == "external":
                state = self.engine.process_event(event, state)

            # Update all agents with new state
            for agent in self.agents:
                agent.receive_state(state)

            # Optional: Sleep to match time_scale (for visualization)
            if self.time_scale < float('inf'):
                await self._sync_with_real_time(current_time)

            # Checkpoint periodically
            if self._should_checkpoint(current_time):
                self._save_checkpoint(state)

        logger.info("realtime_simulation_complete", final_time=state.timestamp)
        return {"final_state": state, "elapsed_sim_time": state.timestamp}

    async def _process_agent_decision(
        self,
        event: Event,
        state: RealTimeSimulationState,
        current_time: float
    ) -> RealTimeSimulationState:
        """Process agent decision event."""
        agent = event.data["agent"]

        # Agent decides action (may call LLM - takes real time)
        decision_start = datetime.now()
        action = await agent.decide_action_async(state, current_time)
        decision_duration = (datetime.now() - decision_start).total_seconds()

        logger.info(
            "agent_decision_completed",
            agent=agent.name,
            sim_time=current_time,
            decision_duration=decision_duration,
            has_action=action is not None
        )

        if action:
            # Validate action
            validated = await self.validator.validate_actions([action], state)

            # Create action event (timestamp = when decision completes)
            action_time = current_time + (decision_duration * self.time_scale)
            action_event = Event(
                timestamp=action_time,
                event_type="agent_action",
                data={"action": validated[0]}
            )
            self.engine.event_queue.schedule(action_event)

        # Schedule next decision for this agent
        next_time = agent.get_next_decision_time(current_time, state)
        if next_time < self.max_sim_time:
            self.engine.event_queue.schedule(Event(
                timestamp=next_time,
                event_type="agent_decision",
                data={"agent": agent}
            ))

        return state

    async def _sync_with_real_time(self, sim_time: float):
        """Sleep to maintain time_scale ratio."""
        expected_real_time = sim_time / self.time_scale
        actual_real_time = (datetime.now() - self.start_time).total_seconds()

        if expected_real_time > actual_real_time:
            sleep_duration = expected_real_time - actual_real_time
            await asyncio.sleep(sleep_duration)
```

---

## Key Differences

| Aspect | Turn-Based | Real-Time Event-Driven |
|--------|-----------|----------------------|
| **Time Model** | Discrete integer turns | Continuous float timestamps |
| **Synchronization** | All agents act per turn | Agents act asynchronously |
| **State Updates** | Atomic per turn | Per event |
| **LLM Latency** | Hidden (all decisions wait) | Explicit (affects when action occurs) |
| **Determinism** | Fully deterministic | Depends on LLM timing, event ordering |
| **Debugging** | Easy (step through turns) | Complex (interleaved events) |
| **Checkpointing** | After each turn | Time-based or event-count-based |
| **Realism** | Low (simultaneous actions) | High (realistic timing) |

---

## Design Options

### Option 1: Separate Class Hierarchies

**Approach:** Create parallel class hierarchies for real-time

```
infrastructure/
├── base/
│   ├── agent.py           # BaseAgent (turn-based)
│   ├── engine.py          # BaseEngine (turn-based)
│   └── validator.py       # BaseValidator (shared)
└── realtime/
    ├── agent.py           # BaseRealTimeAgent
    ├── engine.py          # BaseRealTimeEngine
    └── orchestrator.py    # RealTimeOrchestrator
```

**Pros:**
- ✅ Clean separation - no breaking changes to existing code
- ✅ Each hierarchy optimized for its model
- ✅ Easy to maintain both modes independently

**Cons:**
- ❌ Code duplication between hierarchies
- ❌ Harder to switch between modes
- ❌ Domain implementations must implement both if supporting both modes

**Recommendation:** ✅ **Preferred approach** - Keeps existing system stable

### Option 2: Unified Hybrid Base Classes

**Approach:** Single base classes that support both modes

```python
class BaseAgent(ABC):
    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Turn-based decision (synchronous)."""
        pass

    async def decide_action_async(
        self,
        state: Union[SimulationState, RealTimeSimulationState],
        current_time: Optional[float] = None
    ) -> Optional[Action]:
        """Real-time decision (async, optional implementation)."""
        raise NotImplementedError("Agent does not support real-time mode")
```

**Pros:**
- ✅ Single implementation can support both modes
- ✅ Less code duplication
- ✅ Easier to compare same domain in different modes

**Cons:**
- ❌ More complex base classes
- ❌ Risk of breaking existing implementations
- ❌ Confusion about which methods to implement

**Recommendation:** ❌ **Not recommended** - Too complex, fragile

### Option 3: Mode Flag in Config

**Approach:** Single codebase with runtime mode selection

```yaml
simulation:
  name: "Economic Sim"
  mode: "realtime"  # or "turn_based"
  max_sim_time: 3600.0  # for realtime
  # max_turns: 100      # for turn_based
```

**Pros:**
- ✅ Easy to switch modes via config
- ✅ Single codebase

**Cons:**
- ❌ Complex runtime branching
- ❌ Hard to type-check correctly
- ❌ Risk of mode-specific bugs

**Recommendation:** ❌ **Not recommended** - Too much conditional logic

---

## Implementation Strategy

### Phase 1: Core Real-Time Infrastructure (Foundation)

**Goal:** Add real-time base classes without modifying existing system

**Duration:** 3-4 days

**Tasks:**
1. Create `infrastructure/realtime/` module
2. Implement `Event` and `EventQueue` classes
3. Implement `BaseRealTimeEngine` abstract class
4. Implement `BaseRealTimeAgent` abstract class
5. Implement `RealTimeSimulationState` model
6. Implement `RealTimeOrchestrator`
7. Unit tests for event queue and orchestrator

**Deliverable:** Real-time framework ready for domain implementations

**Validation:**
- [ ] Event queue correctly orders events by timestamp
- [ ] Orchestrator processes events in correct order
- [ ] Can run simple test simulation with mock agents

### Phase 2: Example Implementation

**Goal:** Prove real-time system with concrete example

**Duration:** 2-3 days

**Tasks:**
1. Create `RealTimeEconomicEngine` in `llm-sim-economic` repo
2. Create `RealTimeNationAgent` with periodic decisions
3. Add real-time config: `scenarios/realtime_economic.yaml`
4. Implement engine events (e.g., interest calculation every 10s)
5. Test: run 60-second simulation with 3 agents

**Example Agent:**
```python
class RealTimeNationAgent(BaseRealTimeAgent):
    def __init__(self, name: str, decision_interval: float = 10.0):
        super().__init__(name)
        self.decision_interval = decision_interval

    async def decide_action_async(self, state, current_time):
        # Simple: buy if affordable, sell if rich
        if state.agents[self.name].economic_strength > 1000:
            return Action(self.name, "sell", {"amount": 100})
        else:
            return Action(self.name, "buy", {"amount": 50})

    def get_next_decision_time(self, current_time, state):
        return current_time + self.decision_interval
```

**Deliverable:** Working real-time economic simulation

**Validation:**
- [ ] Simulation runs for 60 simulated seconds
- [ ] Agents make decisions at correct intervals
- [ ] Engine events (interest) fire periodically
- [ ] Final state is consistent

### Phase 3: LLM Integration

**Goal:** Add LLM-based real-time agents with realistic latency

**Duration:** 2-3 days

**Tasks:**
1. Create `RealTimeLLMAgent` base class (extends `BaseRealTimeAgent`)
2. Handle LLM timeout scenarios
3. Add "thinking" state tracking (which agents are currently calling LLM)
4. Implement interruption mechanism (agent can cancel in-flight LLM call)
5. Add reasoning chain capture for real-time decisions
6. Test with actual Ollama LLM

**Example:**
```python
class RealTimeLLMAgent(BaseRealTimeAgent):
    def __init__(self, name: str, llm_client: LLMClient, decision_interval: float = 30.0):
        super().__init__(name)
        self.llm_client = llm_client
        self.decision_interval = decision_interval

    async def decide_action_async(self, state, current_time):
        prompt = self._build_prompt(state, current_time)

        try:
            # Call LLM with timeout
            response = await asyncio.wait_for(
                self.llm_client.generate_async(prompt),
                timeout=10.0  # Max 10s real-time for decision
            )

            action = self._parse_action(response)
            return action

        except asyncio.TimeoutError:
            logger.warning("llm_timeout", agent=self.name, time=current_time)
            return None  # No action this cycle

    def get_next_decision_time(self, current_time, state):
        # Periodic decisions every 30 simulated seconds
        return current_time + self.decision_interval
```

**Deliverable:** LLM agents working in real-time simulations

**Validation:**
- [ ] LLM latency correctly reflected in action timestamps
- [ ] Timeout handling works (simulation doesn't hang)
- [ ] Reasoning chains captured in state
- [ ] Agents can reason about "current time"

### Phase 4: Checkpointing & Persistence

**Goal:** Extend checkpoint system for real-time sims

**Duration:** 2 days

**Tasks:**
1. Extend `CheckpointManager` to handle real-time states
2. Add time-based checkpointing (every N seconds)
3. Add event-count-based checkpointing (every M events)
4. Serialize event queue state (for resumption)
5. Test checkpoint save/load with event queue restoration

**Checkpoint format:**
```json
{
  "metadata": {
    "run_id": "...",
    "timestamp": 127.5,
    "event_count": 342,
    "mode": "realtime"
  },
  "state": {
    "timestamp": 127.5,
    "agents": {...},
    "global_state": {...},
    "pending_events": 5
  },
  "event_queue": [
    {"timestamp": 128.0, "type": "agent_decision", "data": {...}},
    {"timestamp": 130.0, "type": "engine_rule", "data": {...}}
  ]
}
```

**Deliverable:** Real-time simulations can checkpoint and resume

**Validation:**
- [ ] Can save checkpoint mid-simulation
- [ ] Can restore from checkpoint and continue
- [ ] Event queue restored correctly
- [ ] No event duplication or loss

### Phase 5: Control Server Integration

**Goal:** Make control server work with real-time simulations

**Duration:** 2 days

**Tasks:**
1. Update `SimulationManager` to detect simulation mode
2. Add real-time status tracking (current simulation time, events/sec)
3. Update WebSocket streaming for real-time metrics
4. Add "pause/resume" controls for real-time sims
5. Update dashboard to show real-time vs turn-based differently

**Dashboard view:**
```
┌──────────────────────────────────────┐
│ Economic Sim (Real-Time)             │
│ ⏱️ Sim Time: 127.5s / 300.0s         │
│ ⚡ Events: 342 total, 2.7/sec        │
│ 🤔 Agent_A thinking... (5.2s)        │
│ 📊 [Real-time chart updating...]     │
└──────────────────────────────────────┘
```

**Deliverable:** Control server fully supports real-time simulations

**Validation:**
- [ ] Can start real-time simulation from dashboard
- [ ] Real-time metrics display correctly
- [ ] Can pause/resume real-time simulation
- [ ] WebSocket streams real-time events

---

## LLM Integration Challenges

### Challenge 1: Variable Latency

**Problem:** LLM calls take 1-10 seconds of real time, creating realistic "thinking time"

**Solution:** Model LLM latency explicitly in simulation time

```python
# In RealTimeOrchestrator._process_agent_decision()
decision_start_real = datetime.now()
action = await agent.decide_action_async(state, current_time)
decision_duration_real = (datetime.now() - decision_start_real).total_seconds()

# Map real time to simulation time
decision_duration_sim = decision_duration_real * self.time_scale

# Action happens in future
action.timestamp = current_time + decision_duration_sim
```

**Effect:** Agent can't act instantly - realistic delay between "I want to buy" and "I buy"

### Challenge 2: Parallel Reasoning

**Problem:** Multiple agents can call LLMs in parallel (real concurrency)

**Solution:** Use `asyncio.gather()` for concurrent LLM calls

```python
async def _process_multiple_agent_decisions(self, events, state, current_time):
    """Process multiple agent decisions in parallel."""

    # Start all LLM calls concurrently
    decision_tasks = [
        agent.decide_action_async(state, current_time)
        for event in events
        for agent in [event.data["agent"]]
    ]

    # Wait for all to complete
    actions = await asyncio.gather(*decision_tasks, return_exceptions=True)

    # Handle results and exceptions
    for action in actions:
        if isinstance(action, Exception):
            logger.error("agent_decision_failed", error=action)
        elif action:
            self._schedule_action_event(action)
```

**Benefit:** Realistic - multiple agents "think" simultaneously

### Challenge 3: Time-Aware Prompts

**Problem:** LLMs need to reason about current time and timing

**Solution:** Include temporal context in prompts

```python
def _build_prompt(self, state: RealTimeSimulationState, current_time: float) -> str:
    return f"""
You are {self.name} in an economic simulation.

Current simulation time: {current_time:.1f} seconds
Your last decision was at: {self.last_decision_time:.1f} seconds ({current_time - self.last_decision_time:.1f}s ago)

Current state:
- Your economic strength: {state.agents[self.name].economic_strength}
- Market interest rate: {state.global_state.interest_rate}

You can make decisions at most every 30 seconds of simulation time.
What action do you want to take RIGHT NOW?
"""
```

**Effect:** LLM understands it's in a temporal context

### Challenge 4: Stale Decisions

**Problem:** Agent starts deciding at `t=10s`, LLM takes 5s real-time, but world changed at `t=12s`

**Solution:** Validate state version or timestamp

```python
async def decide_action_async(self, state, current_time):
    state_snapshot = state
    snapshot_time = current_time

    # Call LLM (takes time)
    action = await self.llm_client.generate_async(...)

    # Check if state is still current
    if self._current_state.timestamp > snapshot_time + 1.0:
        logger.warning(
            "stale_decision",
            agent=self.name,
            snapshot_time=snapshot_time,
            current_time=self._current_state.timestamp
        )
        return None  # Abort stale decision

    return action
```

**Alternative:** Re-validate action against current state before executing

### Challenge 5: Timeouts

**Problem:** LLM might hang or take too long

**Solution:** Hard timeout with fallback

```python
async def decide_action_async(self, state, current_time):
    try:
        action = await asyncio.wait_for(
            self._call_llm(state, current_time),
            timeout=self.max_decision_time  # e.g., 10 seconds
        )
        return action

    except asyncio.TimeoutError:
        logger.error("llm_timeout", agent=self.name, time=current_time)

        # Fallback: return safe default action
        return self._default_action(state)
```

---

## State & Checkpointing

### State Comparison

**Turn-based state:**
```json
{
  "turn": 45,
  "agents": {...},
  "global_state": {...}
}
```

**Real-time state:**
```json
{
  "timestamp": 127.5,
  "elapsed_real_time": 23.4,
  "agents": {...},
  "global_state": {...},
  "pending_events": 5,
  "processed_events": 342,
  "agents_thinking": ["Agent_A", "Agent_C"]
}
```

### Checkpoint Strategy

**Time-based:** Save every N simulation seconds
```python
if current_time - last_checkpoint_time >= checkpoint_interval:
    save_checkpoint(state)
```

**Event-based:** Save every M events
```python
if state.processed_events % checkpoint_event_interval == 0:
    save_checkpoint(state)
```

**Hybrid:** Time-based OR event-based (whichever comes first)

### Resume Capability

To resume a real-time simulation:
1. Load checkpoint state
2. Restore event queue from checkpoint
3. Re-schedule future agent decisions
4. Continue from `state.timestamp`

```python
def resume_from_checkpoint(checkpoint_path: str) -> RealTimeOrchestrator:
    checkpoint = load_checkpoint(checkpoint_path)

    # Restore state
    state = checkpoint["state"]

    # Restore event queue
    for event_data in checkpoint["event_queue"]:
        event = Event(**event_data)
        orchestrator.engine.event_queue.schedule(event)

    # Resume
    return orchestrator.run()
```

---

## API Changes

### Configuration Changes

**Add simulation mode to config:**
```yaml
simulation:
  name: "Real-Time Economic Sim"
  mode: "realtime"              # NEW: "turn_based" or "realtime"

  # Real-time specific
  max_sim_time: 300.0           # Run for 300 simulated seconds
  time_scale: 1.0               # 1.0 = real-time, 10.0 = 10x speed
  checkpoint_interval: 30.0     # Checkpoint every 30 sim seconds

  # Turn-based specific (ignored in realtime)
  # max_turns: 100
  # checkpoint_interval: 10
```

### Agent Configuration

```yaml
agents:
  - name: Agent_A
    type: realtime_nation        # Different agent type
    decision_interval: 30.0      # Decide every 30 sim seconds
    max_decision_time: 10.0      # Max 10 real seconds per decision
```

### Engine Configuration

```yaml
engine:
  type: realtime_economic
  interest_interval: 10.0        # Apply interest every 10 sim seconds
  market_update_interval: 5.0    # Update prices every 5 sim seconds
```

---

## Trade-offs & Considerations

### Determinism

**Turn-based:** Fully deterministic
- Same seed → same results
- Easy to reproduce bugs

**Real-time:** Partially non-deterministic
- LLM latency varies
- Event ordering depends on exact timing
- Harder to reproduce bugs

**Mitigation:**
- Record event stream for replay
- Use fixed random seeds
- Mock LLM latency for testing

### Debugging

**Turn-based:** Easy
- Step through turn by turn
- Inspect state after each turn

**Real-time:** Complex
- Interleaved events
- Need event log viewer
- Time-based breakpoints difficult

**Mitigation:**
- Comprehensive event logging
- Event replay tools
- Slow-motion mode (`time_scale < 1.0`)

### Performance

**Turn-based:** Predictable
- Fixed computation per turn
- Can run as fast as possible

**Real-time:** Variable
- Depends on LLM call frequency
- Limited by real-time constraints

**Mitigation:**
- `time_scale > 1.0` for faster sims
- Async LLM calls for parallelism
- Event queue optimization

### Complexity

**Turn-based:** Simple
- ~500 lines for orchestrator
- Easy to understand flow

**Real-time:** Complex
- ~1000+ lines for orchestrator
- Event queue, async, timing

**Mitigation:**
- Good documentation
- Example implementations
- Keep turn-based mode for simple use cases

---

## Use Cases

### When to Use Turn-Based

1. **Abstract strategic simulations** - Timing doesn't matter (e.g., chess-like games)
2. **Simple testing** - Quick iteration, easy debugging
3. **Reproducibility critical** - Scientific experiments
4. **No LLM latency modeling** - Don't care about "thinking time"

**Examples:**
- Board game simulations
- Abstract economic models (quarters, years)
- Algorithm testing

### When to Use Real-Time

1. **Realistic timing matters** - Want to model actual time constraints
2. **LLM response time is part of simulation** - Decision speed affects outcomes
3. **Continuous processes** - Market prices, physics, resource depletion
4. **Parallel agent reasoning** - Agents think and act independently

**Examples:**
- Trading simulations (HFT vs slow traders)
- Real-time strategy games
- Crisis response simulations (speed matters)
- Multi-agent systems with communication delays

### Hybrid Use Case

**Scenario:** Strategic turn-based game with real-time mini-games

- Overall game: turn-based (turns = days)
- Combat within turn: real-time (seconds)

This would require mode switching - complex but possible.

---

## Timeline

### Minimum Viable Real-Time Support

**Goal:** Can run simple real-time simulation with fixed-interval agents

**Timeline:** 1-2 weeks

**Includes:**
- Phase 1: Core infrastructure
- Phase 2: Example implementation
- Basic documentation

**Excludes:**
- LLM integration
- Checkpointing
- Control server support

### Full Real-Time Feature

**Goal:** Production-ready with LLM, checkpointing, control server

**Timeline:** 3-4 weeks

**Includes all phases:**
- Phase 1-5 complete
- Comprehensive testing
- Documentation
- Migration guide

---

## Open Questions

### 1. Time Scale

**Question:** Should `time_scale` be configurable at runtime?

**Use case:** Start at 1x to observe, then speed up to 10x once stable

**Options:**
- Fixed in config (simpler)
- Runtime control via API (flexible)

**Recommendation:** Start with fixed, add runtime control in Phase 5

### 2. Event Ordering

**Question:** How to handle events at same timestamp?

**Options:**
- FIFO (first scheduled wins)
- Priority field (explicit ordering)
- Agent name alphabetical (deterministic tie-breaker)

**Recommendation:** Use priority field for explicit control

### 3. State Consistency

**Question:** Can agents see partially-updated state?

**Scenario:** Agent A acts at t=10.0, Agent B decides at t=10.0 before A's action processed

**Options:**
- Atomic event processing (no partial state)
- Optimistic concurrency (agents see stale state, validate before commit)

**Recommendation:** Atomic events (simpler, more predictable)

### 4. External Events

**Question:** Can control server inject events mid-simulation?

**Use case:** "Market crash at t=120s" or "New agent joins"

**Implementation:** Add API endpoint to add events to queue

**Recommendation:** Phase 5 feature - very useful for experiments

### 5. Visualization

**Question:** How to visualize real-time simulation progress?

**Options:**
- Same as turn-based (checkpoint polling)
- Event stream to dashboard
- Real-time chart updates

**Recommendation:** Event stream (more responsive)

---

## Related Documents

- [Platform Architecture](./PLATFORM_ARCHITECTURE.md) - Overall system design
- [Configuration Guide](./CONFIGURATION.md) - YAML config reference
- [LLM Integration](./LLM_SETUP.md) - LLM setup and usage

---

## Next Steps

**Before implementation:**
1. Review this design doc
2. Decide on Option 1 vs Option 2 for class hierarchy
3. Prioritize use cases (which domains need real-time first?)
4. Validate with a prototype

**To start implementation:**
1. Create feature branch: `feature/realtime-simulation`
2. Begin Phase 1: Core infrastructure
3. Write tests alongside implementation
4. Document as you go

---

**Document Status:** Design Proposal - Awaiting Review

**Author:** AI Assistant

**Review Date:** TBD

**Decision:** Pending
