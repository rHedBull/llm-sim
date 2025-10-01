# Compute Budget Simulation Model

**Feature Proposal:** Add compute budget constraints to turn-based simulations

**Key Insight:** Keep turn-based synchronous architecture, but model realistic "thinking time" through compute budgets

**Status:** Design Phase

**Last Updated:** 2025-10-01

---

## Table of Contents

- [Core Concept](#core-concept)
- [Architecture Comparison](#architecture-comparison)
- [Design](#design)
- [Implementation](#implementation)
- [LLM Integration](#llm-integration)
- [Use Cases](#use-cases)
- [Advantages Over Real-Time](#advantages-over-real-time)
- [Trade-offs](#trade-offs)
- [Timeline](#timeline)

---

## Core Concept

### The Problem

In current turn-based simulations:
- All agents decide simultaneously each turn
- LLM calls are "free" - no cost for thinking longer
- No modeling of compute/time constraints
- Agent that thinks 1 second vs 10 seconds has same outcome

**Reality:** Decision quality often correlates with time spent thinking.

### The Proposal

**Keep turn-based architecture** but add:
1. **Compute budget per agent** - How much "thinking time" they have
2. **Budget allocation** - Agents decide how much to spend per turn
3. **Budget tracking** - State tracks cumulative compute used
4. **Strategic trade-offs** - Spend more now vs save for later

**Example:**
```
Turn 1:
  Agent A: "This is routine, I'll think for 1 second" (fast decision)
  Agent B: "This is critical, I'll think for 10 seconds" (deep reasoning)

Both actions still apply simultaneously, but:
  - Agent A used 1 compute unit
  - Agent B used 10 compute units
  - Both have reduced budgets for future turns
```

---

## Architecture Comparison

### Option 1: Pure Real-Time (from REALTIME_SIMULATION.md)

```
Timeline: t=0.0s ──> t=2.3s ──> t=5.7s ──> t=8.9s ──> ...
                    Agent A     Agent B     Agent A
                    acts        acts        acts

- Continuous time
- Asynchronous agent actions
- Event queue
- Complex orchestration
```

**Pros:** Maximum realism
**Cons:** Complex, hard to debug, non-deterministic

### Option 2: Turn-Based (Current)

```
Turn 1         Turn 2         Turn 3
All agents  -> All agents -> All agents
act            act            act
simultaneously simultaneously simultaneously

- Discrete turns
- Synchronous actions
- Simple orchestration
```

**Pros:** Simple, deterministic, easy to debug
**Cons:** Unrealistic timing, no compute modeling

### Option 3: Turn-Based with Compute Budget (Proposed)

```
Turn 1                    Turn 2                    Turn 3
Agent A: 1s compute  -->  Agent A: 2s compute  -->  Agent A: 1s compute
Agent B: 10s compute -->  Agent B: 1s compute  -->  Agent B: 5s compute
                     ↓                         ↓                      ↓
All actions apply         All actions apply         All actions apply
simultaneously            simultaneously            simultaneously

Budget tracking:
Agent A: 100 total → 99 → 97 → 96
Agent B: 100 total → 90 → 89 → 84
```

**Pros:**
- ✅ Simple turn-based orchestration (no changes to orchestrator!)
- ✅ Models compute constraints
- ✅ Strategic resource allocation
- ✅ Deterministic (same seed → same result)
- ✅ Easy to debug

**Cons:**
- ❌ Still synchronous (all agents act per turn)
- ❌ Less realistic than true real-time

---

## Design

### Core Components

#### 1. Compute Budget in Agent State

```python
class AgentState(BaseModel):
    """Agent state with compute budget tracking."""

    name: str

    # Domain-specific fields (economic_strength, etc.)
    economic_strength: float = 0.0

    # Compute budget fields
    compute_budget_total: float = 100.0      # Initial allocation
    compute_budget_remaining: float = 100.0  # Current available
    compute_budget_used_this_turn: float = 0.0
    compute_budget_used_total: float = 0.0
```

**Configuration:**
```yaml
agents:
  - name: Agent_A
    type: nation
    initial_economic_strength: 1000.0
    compute_budget: 100.0  # Total "thinking time" across simulation

  - name: Agent_B
    type: nation
    initial_economic_strength: 1500.0
    compute_budget: 200.0  # More budget = can think longer/deeper
```

#### 2. Compute-Aware Action

```python
class Action(BaseModel):
    """Action with requested compute budget."""

    agent_name: str
    action_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

    # NEW: Compute budget request
    requested_compute: float = 1.0  # How much thinking time agent wants
    actual_compute: Optional[float] = None  # How much was actually used

    validated: bool = False
    validation_reason: str = ""
```

#### 3. Budget-Aware Agent Interface

```python
class BaseAgent(ABC):
    """Base agent with compute budget awareness."""

    def __init__(self, name: str, compute_budget: float = 100.0):
        self.name = name
        self.compute_budget_total = compute_budget

    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide action based on current state.

        Agent should:
        1. Check their remaining budget: state.agents[self.name].compute_budget_remaining
        2. Decide how much to spend this turn
        3. Return action with requested_compute set

        Returns:
            Action with requested_compute field
        """
        pass

    def get_remaining_budget(self, state: SimulationState) -> float:
        """Helper to get remaining compute budget."""
        return state.agents[self.name].compute_budget_remaining
```

#### 4. Budget Enforcement in Engine

```python
class BaseEngine(ABC):
    """Engine with compute budget enforcement."""

    def run_turn(self, actions: List[Action]) -> SimulationState:
        """Execute turn with budget tracking."""

        # Phase 1: Enforce budget constraints
        actions_with_budgets = []
        for action in actions:
            agent_state = self._state.agents[action.agent_name]

            # Clamp requested compute to available budget
            available = agent_state.compute_budget_remaining
            actual = min(action.requested_compute, available)

            action.actual_compute = actual
            actions_with_budgets.append(action)

            logger.info(
                "compute_allocated",
                agent=action.agent_name,
                requested=action.requested_compute,
                actual=actual,
                remaining_after=available - actual
            )

        # Phase 2: Apply actions
        new_state = self.apply_actions(actions_with_budgets)

        # Phase 3: Update budgets
        new_state = self._update_compute_budgets(new_state, actions_with_budgets)

        # Phase 4: Apply engine rules
        new_state = self.apply_engine_rules(new_state)

        return new_state

    def _update_compute_budgets(
        self,
        state: SimulationState,
        actions: List[Action]
    ) -> SimulationState:
        """Update agent compute budgets based on usage."""

        new_agents = {}
        for name, agent in state.agents.items():
            # Find this agent's action
            action = next((a for a in actions if a.agent_name == name), None)
            used = action.actual_compute if action else 0.0

            # Update budget
            new_agent = agent.model_copy(update={
                "compute_budget_remaining": agent.compute_budget_remaining - used,
                "compute_budget_used_this_turn": used,
                "compute_budget_used_total": agent.compute_budget_used_total + used
            })
            new_agents[name] = new_agent

        return state.model_copy(update={"agents": new_agents})
```

---

## Implementation

### Phase 1: Core Budget System (No LLM)

**Duration:** 2 days

**Tasks:**
1. Add compute budget fields to agent state model
2. Update `Action` model with `requested_compute` and `actual_compute`
3. Implement budget enforcement in `BaseEngine.run_turn()`
4. Add budget tracking to state updates
5. Update checkpoint system to save budget state
6. Unit tests for budget allocation and enforcement

**Deliverable:** Turn-based simulations track compute budgets

**Example test:**
```python
def test_compute_budget_enforcement():
    # Agent requests 10 compute but only has 5 remaining
    agent_state = AgentState(
        name="Agent_A",
        compute_budget_total=100.0,
        compute_budget_remaining=5.0
    )

    action = Action(
        agent_name="Agent_A",
        action_name="think_deeply",
        requested_compute=10.0  # Requests more than available
    )

    # Engine should clamp to available
    new_state = engine.run_turn([action])

    assert action.actual_compute == 5.0  # Clamped
    assert new_state.agents["Agent_A"].compute_budget_remaining == 0.0
```

### Phase 2: Strategic Agent Implementation

**Duration:** 2 days

**Tasks:**
1. Create `ComputeAwareNationAgent` example
2. Implement budget-aware decision logic
3. Add heuristics for when to spend more compute
4. Test with different budget allocation strategies
5. Add config option for compute budget per agent

**Example agent:**
```python
class ComputeAwareNationAgent(BaseAgent):
    """Agent that strategically allocates compute budget."""

    def __init__(
        self,
        name: str,
        compute_budget: float = 100.0,
        base_compute: float = 1.0,
        critical_threshold: float = 500.0
    ):
        super().__init__(name, compute_budget)
        self.base_compute = base_compute
        self.critical_threshold = critical_threshold

    def decide_action(self, state: SimulationState) -> Action:
        agent_state = state.agents[self.name]
        remaining = agent_state.compute_budget_remaining

        # Assess situation criticality
        economic_strength = agent_state.economic_strength
        is_critical = economic_strength < self.critical_threshold

        # Decide how much compute to use
        if is_critical and remaining > 10.0:
            # Critical situation - think deeply
            compute = min(10.0, remaining)
            strategy = self._deep_reasoning(state, compute)
        elif remaining > self.base_compute:
            # Normal situation - quick decision
            compute = self.base_compute
            strategy = self._fast_reasoning(state)
        else:
            # Low budget - minimal thinking
            compute = min(0.1, remaining)
            strategy = "maintain"  # Default action

        action = Action(
            agent_name=self.name,
            action_name=strategy,
            parameters={"strength": economic_strength},
            requested_compute=compute
        )

        logger.info(
            "decision_made",
            agent=self.name,
            compute_requested=compute,
            is_critical=is_critical,
            remaining_budget=remaining
        )

        return action

    def _fast_reasoning(self, state: SimulationState) -> str:
        """Quick heuristic decision (low compute)."""
        agent = state.agents[self.name]
        if agent.economic_strength > 1000:
            return "maintain"
        else:
            return "grow"

    def _deep_reasoning(self, state: SimulationState, compute: float) -> str:
        """Complex reasoning (high compute).

        In practice, this might involve:
        - More complex calculations
        - Looking ahead multiple turns
        - Analyzing other agents' strategies
        """
        # Placeholder - in real implementation, more complex logic
        agent = state.agents[self.name]

        # Simulate "thinking" proportional to compute
        # (In LLM version, this becomes prompt complexity)

        if agent.economic_strength < 300:
            return "emergency_growth"
        elif agent.economic_strength > 2000:
            return "diversify"
        else:
            return "grow"
```

**Test scenarios:**
```yaml
# scenarios/compute_budget_test.yaml
simulation:
  name: "Compute Budget Test"
  max_turns: 50

agents:
  # Rich thinker - lots of budget
  - name: Agent_Strategic
    type: compute_aware_nation
    compute_budget: 200.0
    initial_economic_strength: 1000.0

  # Poor thinker - limited budget
  - name: Agent_Reactive
    type: compute_aware_nation
    compute_budget: 20.0
    initial_economic_strength: 1000.0

# Question: Who performs better?
# Hypothesis: Strategic with more budget should make better decisions
```

### Phase 3: LLM Integration with Budget

**Duration:** 3 days

**Tasks:**
1. Create `ComputeAwareLLMAgent` base class
2. Map compute budget to LLM inference parameters:
   - Low compute → simple prompt, fast model, low temperature
   - High compute → complex prompt, larger model, higher temperature, more samples
3. Implement adaptive prompting based on budget
4. Add actual LLM call duration tracking
5. Test with Ollama

**LLM mapping strategies:**

#### Strategy A: Prompt Complexity

```python
class ComputeAwareLLMAgent(BaseAgent):
    def decide_action(self, state: SimulationState) -> Action:
        remaining = self.get_remaining_budget(state)

        # Decide compute allocation for this turn
        compute = self._decide_compute_allocation(state, remaining)

        # Build prompt based on compute level
        if compute < 1.0:
            prompt = self._build_simple_prompt(state)  # "Buy or sell?"
        elif compute < 5.0:
            prompt = self._build_normal_prompt(state)  # Include recent history
        else:
            prompt = self._build_complex_prompt(state)  # Full analysis with projections

        # Call LLM
        start_time = time.time()
        response = await self.llm_client.generate_async(prompt)
        actual_duration = time.time() - start_time

        # Parse action
        action = self._parse_action(response)
        action.requested_compute = compute
        action.actual_compute = actual_duration  # Real LLM time

        return action

    def _build_simple_prompt(self, state):
        """Minimal context - fast LLM call."""
        return f"""
You are {self.name}. Economic strength: {state.agents[self.name].economic_strength}.
Choose action: grow/maintain/decline
"""

    def _build_complex_prompt(self, state):
        """Full context - detailed reasoning."""
        agent = state.agents[self.name]
        history = self._get_history(state, last_n_turns=10)

        return f"""
You are {self.name} in an economic simulation.

Your status:
- Economic strength: {agent.economic_strength}
- Compute budget remaining: {agent.compute_budget_remaining}
- Total compute used: {agent.compute_budget_used_total}

Recent history:
{history}

Other agents:
{self._format_other_agents(state)}

Global state:
- Interest rate: {state.global_state.interest_rate}
- Total economic value: {state.global_state.total_economic_value}

Think carefully about:
1. Current position relative to others
2. Trend analysis from history
3. Optimal strategy given remaining budget
4. Long-term vs short-term trade-offs

Provide detailed reasoning, then choose action: grow/maintain/decline/invest/divest
"""
```

#### Strategy B: Model Selection

```python
class ComputeAwareLLMAgent(BaseAgent):
    def __init__(self, name: str, llm_client: LLMClient, **kwargs):
        super().__init__(name, **kwargs)
        self.llm_client = llm_client

        # Different models for different compute levels
        self.models = {
            "fast": "gemma2:2b",      # Low compute
            "normal": "gemma2:7b",    # Medium compute
            "deep": "llama3:70b"      # High compute
        }

    async def decide_action(self, state: SimulationState) -> Action:
        compute = self._decide_compute_allocation(state)

        # Select model based on compute
        if compute < 1.0:
            model = self.models["fast"]
        elif compute < 5.0:
            model = self.models["normal"]
        else:
            model = self.models["deep"]

        # Override LLM client model
        response = await self.llm_client.generate_async(
            prompt=self._build_prompt(state),
            model=model
        )

        return self._parse_action(response, requested_compute=compute)
```

#### Strategy C: Multi-Sampling

```python
class ComputeAwareLLMAgent(BaseAgent):
    async def decide_action(self, state: SimulationState) -> Action:
        compute = self._decide_compute_allocation(state)

        # More compute = more samples = better decision through voting
        num_samples = int(compute)  # 1 compute = 1 sample

        if num_samples == 1:
            # Single sample - fast
            response = await self.llm_client.generate_async(prompt)
            action = self._parse_action(response)
        else:
            # Multiple samples - vote for best action
            tasks = [
                self.llm_client.generate_async(prompt)
                for _ in range(num_samples)
            ]
            responses = await asyncio.gather(*tasks)

            # Vote on actions
            actions = [self._parse_action(r) for r in responses]
            action = self._vote(actions)  # Majority vote or best scored

        action.requested_compute = compute
        return action
```

**Example configuration:**
```yaml
agents:
  - name: Strategic_Thinker
    type: compute_aware_llm_agent
    compute_budget: 100.0
    initial_economic_strength: 1000.0
    llm_config:
      model: "gemma2:7b"
      temperature: 0.7
    compute_strategy: "adaptive"  # Varies prompt complexity

  - name: Fast_Reactor
    type: compute_aware_llm_agent
    compute_budget: 20.0
    initial_economic_strength: 1000.0
    llm_config:
      model: "gemma2:2b"  # Faster model
      temperature: 0.3
    compute_strategy: "fixed"  # Always uses 1.0 compute
```

### Phase 4: Dashboard Visualization

**Duration:** 1-2 days

**Tasks:**
1. Add compute budget visualization to dashboard
2. Show budget usage over time (line chart)
3. Highlight critical moments (when agent spent high compute)
4. Compare agent strategies (budget usage patterns)

**Dashboard view:**
```
┌─────────────────────────────────────────────┐
│ Agent_A Budget                              │
│ Remaining: 45.2 / 100.0  [████████░░] 45%  │
│                                             │
│ Budget Usage Over Time:                     │
│ 100│                                        │
│  90│\                                       │
│  80│ \                                      │
│  70│  \__                                   │
│  60│     \                                  │
│  50│      \___                              │
│  40│          \_____                        │
│  30│                \____                   │
│  20│                     \                  │
│  10│                      \___              │
│   0│───────────────────────────\─────────► │
│     0   10   20   30   40   50  Turn       │
│                                             │
│ High-compute decisions (>5):                │
│ • Turn 5: 10.0 compute (critical situation) │
│ • Turn 15: 8.0 compute (strategic choice)   │
│ • Turn 23: 12.0 compute (complex scenario)  │
└─────────────────────────────────────────────┘
```

### Phase 5: Analytics & Comparison

**Duration:** 1-2 days

**Tasks:**
1. Add compute efficiency metrics
2. Compare outcomes vs budget spent
3. ROI analysis (did spending more compute lead to better results?)
4. Export compute budget analytics

**Metrics:**
```python
class ComputeBudgetAnalytics:
    """Analyze compute budget efficiency."""

    @staticmethod
    def compute_roi(simulation_result: Dict) -> Dict[str, float]:
        """Calculate return on investment for compute budget.

        Returns:
            {
                "Agent_A": 2.5,  # 2.5x economic growth per compute unit
                "Agent_B": 1.8,
                ...
            }
        """
        roi = {}
        for agent_name, agent_final in simulation_result["final_state"].agents.items():
            agent_initial = simulation_result["history"][0].agents[agent_name]

            compute_spent = agent_final.compute_budget_used_total
            economic_gain = (
                agent_final.economic_strength - agent_initial.economic_strength
            )

            roi[agent_name] = economic_gain / compute_spent if compute_spent > 0 else 0

        return roi

    @staticmethod
    def critical_moments(simulation_result: Dict, threshold: float = 5.0) -> List[Dict]:
        """Find turns where agents used high compute."""
        moments = []

        for i, state in enumerate(simulation_result["history"]):
            for agent_name, agent in state.agents.items():
                if agent.compute_budget_used_this_turn >= threshold:
                    moments.append({
                        "turn": i,
                        "agent": agent_name,
                        "compute_used": agent.compute_budget_used_this_turn,
                        "economic_strength": agent.economic_strength,
                        "reason": "High compute decision"
                    })

        return moments
```

---

## LLM Integration

### Key Principle

**Compute budget represents reasoning depth/breadth, not just time.**

### Mapping Compute to LLM Behavior

| Compute | Prompt | Model | Strategy | Expected Time |
|---------|--------|-------|----------|--------------|
| 0.1-0.5 | Minimal context | gemma2:2b | Fast heuristic | <1s |
| 1.0 | Basic context | gemma2:7b | Normal decision | 1-3s |
| 5.0 | Full context + history | gemma2:7b | Deep reasoning | 5-8s |
| 10.0+ | Full context + multi-sample | llama3:70b or 3x samples | Strategic planning | 10-30s |

### Adaptive Prompting Example

```python
def _build_adaptive_prompt(self, state: SimulationState, compute: float) -> str:
    """Build prompt complexity based on compute budget."""

    base = f"You are {self.name}. Turn {state.turn}.\n"

    # Always include current state
    base += f"Economic strength: {state.agents[self.name].economic_strength}\n"

    # Add context based on compute level
    if compute >= 1.0:
        # Include global state
        base += f"\nGlobal state:\n{self._format_global_state(state)}\n"

    if compute >= 2.0:
        # Include other agents
        base += f"\nOther agents:\n{self._format_other_agents(state)}\n"

    if compute >= 5.0:
        # Include history
        history_length = min(int(compute), 10)
        base += f"\nRecent history ({history_length} turns):\n"
        base += self._format_history(state, last_n=history_length)

    if compute >= 10.0:
        # Include strategic analysis prompt
        base += """
\nPerform strategic analysis:
1. Analyze current position vs competitors
2. Identify risks and opportunities
3. Consider long-term implications
4. Evaluate multiple strategies
5. Choose optimal action
"""

    base += f"\nChoose action: {', '.join(self.available_actions)}\n"

    return base
```

### Budget Exhaustion Handling

```python
def decide_action(self, state: SimulationState) -> Action:
    remaining = self.get_remaining_budget(state)

    if remaining < 0.1:
        # Budget exhausted - fall back to simple heuristic (no LLM call)
        logger.warning("compute_budget_exhausted", agent=self.name)
        return self._default_action(state)

    # Normal LLM-based decision
    compute = min(self._desired_compute(state), remaining)
    return await self._llm_decide(state, compute)
```

---

## Use Cases

### 1. Economic Crisis Simulation

**Scenario:** Model how agents respond under pressure with limited resources

```yaml
simulation:
  name: "Crisis Response"
  max_turns: 100

agents:
  # Strategic player - manages budget carefully
  - name: Prudent_Bank
    type: compute_aware_llm_agent
    compute_budget: 50.0
    initial_economic_strength: 1000.0

  # Reactive player - spends budget quickly
  - name: Aggressive_Trader
    type: compute_aware_llm_agent
    compute_budget: 50.0
    initial_economic_strength: 1000.0

# Inject crisis at turn 30
engine:
  type: economic
  events:
    - turn: 30
      type: "market_crash"
      effect: "multiply_all_strength:0.5"
```

**Research question:** Does strategic compute allocation (saving budget for crises) outperform reactive spending?

### 2. Computational Resource Markets

**Scenario:** Agents can trade compute budget

```python
# Agent can buy/sell compute from others
action = Action(
    agent_name="Agent_A",
    action_name="buy_compute",
    parameters={
        "from_agent": "Agent_B",
        "amount": 5.0,
        "price": 100.0  # economic units
    }
)
```

**Interesting dynamics:**
- Rich agents buy compute from poor agents
- Compute market forms with supply/demand
- Strategic timing (when to buy compute?)

### 3. LLM Efficiency Research

**Scenario:** Compare different compute allocation strategies

```yaml
agents:
  - name: Always_Deep
    compute_budget: 100.0
    strategy: "fixed"  # Always uses 10 compute per turn

  - name: Adaptive
    compute_budget: 100.0
    strategy: "adaptive"  # Varies based on situation

  - name: Reactive
    compute_budget: 100.0
    strategy: "reactive"  # High compute when in danger
```

**Metrics:**
- Final economic strength
- Compute ROI (gain per compute unit)
- Decision quality over time

### 4. Multi-Agent Negotiation

**Scenario:** Complex negotiations require more compute

```python
def decide_action(self, state: SimulationState) -> Action:
    # Check if in negotiation phase
    if self._is_negotiating(state):
        # Negotiation is complex - use more compute
        compute = min(10.0, self.get_remaining_budget(state))
    else:
        # Normal turn - less compute
        compute = 1.0

    # LLM reasons about negotiation strategy
    prompt = self._build_negotiation_prompt(state, compute)
    ...
```

---

## Advantages Over Real-Time

### 1. Simpler Implementation

**Real-time:**
- Event queue
- Async event processing
- State synchronization
- ~1000 lines of orchestrator code

**Compute budget:**
- Minor changes to existing orchestrator
- Add budget tracking
- ~100 lines of new code

### 2. Deterministic

**Real-time:**
- Event ordering depends on exact timing
- LLM latency variations cause non-determinism
- Hard to reproduce bugs

**Compute budget:**
- Same seed → same result
- Budget allocation is deterministic
- Easy to reproduce

### 3. Easy Debugging

**Real-time:**
- Interleaved events
- Need event log viewer
- Time-based breakpoints

**Compute budget:**
- Step through turns as before
- Inspect budget state per turn
- Standard debugger works

### 4. Compatible with Existing Code

**Real-time:**
- New base classes
- New orchestrator
- Separate implementations

**Compute budget:**
- Extends existing base classes
- Reuses current orchestrator (minor changes)
- Backward compatible (budget optional)

### 5. No Event Queue Complexity

**Real-time:**
- Priority queue management
- Event cancellation
- Timestamp coordination

**Compute budget:**
- No event queue
- Simple turn counter
- Standard state updates

---

## Trade-offs

### What You Gain

✅ **Realistic resource constraints** - Models limited thinking time
✅ **Strategic depth** - Agents must allocate scarce resource
✅ **LLM efficiency modeling** - Different decisions have different costs
✅ **Research opportunities** - Study compute allocation strategies
✅ **Simple implementation** - Minor changes to existing system
✅ **Deterministic** - Reproducible results
✅ **Backward compatible** - Existing simulations still work

### What You Lose

❌ **Not truly real-time** - Still synchronous turns
❌ **Less realistic timing** - All agents still act simultaneously
❌ **No true parallelism** - Agents don't act asynchronously
❌ **Artificial budget** - Real world doesn't have "compute budgets"

### Comparison Matrix

| Feature | Turn-Based | Compute Budget | Real-Time |
|---------|-----------|----------------|-----------|
| Realism | Low | Medium | High |
| Complexity | Low | Low-Medium | High |
| Determinism | Yes | Yes | No |
| LLM Modeling | None | Good | Excellent |
| Debug Ease | Easy | Easy | Hard |
| Strategic Depth | Low | High | High |
| Implementation | ✅ Done | 1-2 weeks | 3-4 weeks |

---

## Timeline

### Phase 1: Core System (2 days)
- Add budget fields to state
- Implement budget enforcement
- Update engine
- Tests

### Phase 2: Example Agent (2 days)
- ComputeAwareNationAgent
- Strategic allocation logic
- Config integration

### Phase 3: LLM Integration (3 days)
- ComputeAwareLLMAgent
- Adaptive prompting
- Model selection
- Multi-sampling

### Phase 4: Visualization (1-2 days)
- Dashboard budget display
- Usage charts
- Critical moments

### Phase 5: Analytics (1-2 days)
- ROI metrics
- Strategy comparison
- Export tools

**Total: 1.5-2 weeks**

---

## Implementation Decision

### Recommendation: Implement Compute Budget First

**Rationale:**
1. **Faster to implement** (1.5-2 weeks vs 3-4 weeks for real-time)
2. **Achieves 80% of benefits** with 20% of complexity
3. **Non-breaking** - can add alongside existing system
4. **Validates concept** - if useful, can still add real-time later
5. **Research value** - interesting strategic dynamics

### Then Decide

After implementing compute budget, reassess:
- **If sufficient:** Stop here, focus on other features
- **If not:** Add real-time as separate mode for domains that need it

### Hybrid Future (Best of Both)

Long-term, could support both:
```yaml
simulation:
  mode: "turn_based_with_budget"  # This feature
  # OR
  mode: "realtime"  # Full event-driven (from REALTIME_SIMULATION.md)
```

Separate class hierarchies (Option 1 from real-time doc):
- `infrastructure/base/` - Turn-based with compute budget
- `infrastructure/realtime/` - Event-driven real-time

---

## Configuration Example

### Simple Config

```yaml
simulation:
  name: "Compute Budget Test"
  max_turns: 50
  checkpoint_interval: 10

agents:
  - name: Agent_A
    type: compute_aware_nation
    initial_economic_strength: 1000.0
    compute_budget: 100.0  # NEW: Total budget

  - name: Agent_B
    type: compute_aware_nation
    initial_economic_strength: 1500.0
    compute_budget: 50.0  # Half the budget

engine:
  type: economic
  interest_rate: 0.05

# State variables include budget fields automatically
state_variables:
  agent_vars:
    economic_strength:
      type: float
      default: 0.0
    compute_budget_total:
      type: float
      default: 100.0
    compute_budget_remaining:
      type: float
      default: 100.0
    compute_budget_used_this_turn:
      type: float
      default: 0.0
    compute_budget_used_total:
      type: float
      default: 0.0
```

### Advanced LLM Config

```yaml
agents:
  - name: Strategic_AI
    type: compute_aware_llm_agent
    initial_economic_strength: 1000.0

    # Compute budget
    compute_budget: 100.0
    compute_strategy: "adaptive"  # Varies by situation

    # LLM config
    llm_config:
      model: "gemma2:7b"
      temperature: 0.7

    # Compute-to-LLM mapping
    compute_mapping:
      low_threshold: 1.0  # Below this, use simple prompt
      high_threshold: 5.0  # Above this, use complex prompt

      low_prompt: "simple"
      medium_prompt: "normal"
      high_prompt: "strategic"

      multi_sample_threshold: 10.0  # Use voting above this
```

---

## Next Steps

1. **Review this design** with team/users
2. **Decide: Compute budget vs Real-time** (or both?)
3. **If approved:** Create feature branch
4. **Start Phase 1:** Core budget system
5. **Iterate:** Get feedback from example implementations

---

## Related Documents

- [Real-Time Simulation](./REALTIME_SIMULATION.md) - Full event-driven alternative
- [Platform Architecture](./PLATFORM_ARCHITECTURE.md) - Overall system
- [LLM Setup](./LLM_SETUP.md) - LLM integration guide

---

**Document Status:** Design Proposal - Awaiting Decision

**Recommendation:** ✅ **Implement compute budget first** - simpler, faster, achieves most benefits

**Alternative:** Real-time for domains that truly need asynchronous agents

**Long-term:** Support both modes in separate hierarchies
