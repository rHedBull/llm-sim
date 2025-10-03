# Agent Creation Guide

**A comprehensive guide to creating custom agents for llm-sim simulations.**

---

## Table of Contents

1. [Overview](#overview)
2. [Agent Types](#agent-types)
3. [Creating a Simple Agent](#creating-a-simple-agent)
4. [Creating an LLM Agent](#creating-an-llm-agent)
5. [Working with State](#working-with-state)
6. [Partial Observability](#partial-observability)
7. [Agent-Initiated Lifecycle Changes](#agent-initiated-lifecycle-changes)
8. [Action Types](#action-types)
9. [Best Practices](#best-practices)
10. [Complete Examples](#complete-examples)

---

## Overview

Agents are the decision-making entities in llm-sim. Each agent:
- Observes the current simulation state
- Decides what action to take
- Returns an action for execution

The framework provides a three-tier inheritance hierarchy:

```
BaseAgent (abstract)
    ↓
LLMAgent (abstract, optional)
    ↓
YourCustomAgent (concrete implementation)
```

**When to use each:**
- **BaseAgent** - For rule-based or algorithmic agents
- **LLMAgent** - For agents that use LLM reasoning

---

## Agent Types

### BaseAgent

The fundamental interface all agents must implement:

```python
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState

class BaseAgent(ABC):
    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        """Decide what action to take based on current state."""
        pass
```

**Required:**
- `decide_action(state)` - Returns an `Action` based on observed state

### LLMAgent

Abstract pattern for LLM-based reasoning:

```python
from llm_sim.infrastructure.patterns import LLMAgent

class LLMAgent(BaseAgent):
    @abstractmethod
    async def decide_action_async(self, state: SimulationState) -> Action:
        """Async LLM-based decision making."""
        pass
```

**Provides:**
- Async LLM client integration
- Reasoning chain capture
- Timeout and retry logic
- Prompt building utilities

**Required:**
- `decide_action_async(state)` - Async version using LLM calls

---

## Creating a Simple Agent

### Step 1: Create Agent File

```bash
# In your implementation repository
mkdir -p src/my_sim/agents
touch src/my_sim/agents/trader.py
```

### Step 2: Implement BaseAgent

```python
# src/my_sim/agents/trader.py
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
import structlog

logger = structlog.get_logger()

class TraderAgent(BaseAgent):
    """A simple rule-based trading agent."""

    def __init__(self, name: str, risk_tolerance: float = 0.5):
        super().__init__(name)
        self.risk_tolerance = risk_tolerance
        logger.info("trader_initialized", agent=name, risk_tolerance=risk_tolerance)

    def decide_action(self, state: SimulationState) -> Action:
        """Decide whether to buy, sell, or hold."""
        # Get my current state
        my_state = state.agents[self.name]
        wealth = my_state.wealth

        # Get global state
        market_price = state.global_state.market_price

        # Simple rule-based logic
        if wealth > 1000 and market_price < 50:
            # Buy if we have wealth and price is low
            action_type = "buy"
            amount = wealth * self.risk_tolerance
        elif wealth < 500 and market_price > 100:
            # Sell if we're low on wealth and price is high
            action_type = "sell"
            amount = 100
        else:
            # Hold otherwise
            action_type = "hold"
            amount = 0

        logger.info(
            "action_decided",
            agent=self.name,
            action=action_type,
            wealth=wealth,
            market_price=market_price
        )

        return Action(
            agent_name=self.name,
            action_name=action_type,
            parameters={"amount": amount}
        )
```

### Step 3: Configure in YAML

```yaml
# config.yaml
agents:
  - name: Trader1
    type: trader  # Matches filename (trader.py → TraderAgent)
    config:
      risk_tolerance: 0.7

  - name: Trader2
    type: trader
    config:
      risk_tolerance: 0.3
```

---

## Creating an LLM Agent

### Step 1: Inherit from LLMAgent

```python
# src/my_sim/agents/llm_trader.py
from llm_sim.infrastructure.patterns import LLMAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class LlmTraderAgent(LLMAgent):
    """An LLM-powered trading agent."""

    def __init__(
        self,
        name: str,
        llm_client,
        system_prompt: str = None,
        **kwargs
    ):
        super().__init__(name, llm_client, **kwargs)
        self.system_prompt = system_prompt or self._default_system_prompt()

    def _default_system_prompt(self) -> str:
        return """You are a strategic trading agent in an economic simulation.
Your goal is to maximize your wealth through smart trading decisions.
You can buy, sell, or hold based on market conditions."""

    async def decide_action_async(self, state: SimulationState) -> Action:
        """Use LLM to decide trading action."""
        # Build prompt with current state
        prompt = self._build_prompt(state)

        # Call LLM
        response = await self.llm_client.generate_async(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.7
        )

        # Store reasoning chain
        self.last_reasoning = response

        # Parse action from LLM response
        action = self._parse_action(response)

        logger.info(
            "llm_action_decided",
            agent=self.name,
            action=action.action_name,
            reasoning_length=len(response)
        )

        return action

    def _build_prompt(self, state: SimulationState) -> str:
        """Build prompt with state information."""
        my_state = state.agents[self.name]

        prompt = f"""Current Turn: {state.global_state.turn}

Your State:
- Wealth: {my_state.wealth}
- Holdings: {my_state.holdings}

Market State:
- Price: {state.global_state.market_price}
- Trend: {state.global_state.trend}

Other Agents:
"""
        for agent_name, agent_state in state.agents.items():
            if agent_name != self.name:
                prompt += f"- {agent_name}: wealth={agent_state.wealth}\n"

        prompt += """
What action should you take? Choose one:
- buy <amount>
- sell <amount>
- hold

Respond with ONLY the action and amount, e.g., "buy 100" or "hold"
"""
        return prompt

    def _parse_action(self, llm_response: str) -> Action:
        """Parse LLM response into Action."""
        response_lower = llm_response.strip().lower()

        # Simple parsing logic
        if "buy" in response_lower:
            # Extract amount
            try:
                amount = float(response_lower.split("buy")[1].strip())
            except:
                amount = 100  # Default

            return Action(
                agent_name=self.name,
                action_name="buy",
                parameters={"amount": amount}
            )

        elif "sell" in response_lower:
            try:
                amount = float(response_lower.split("sell")[1].strip())
            except:
                amount = 100

            return Action(
                agent_name=self.name,
                action_name="sell",
                parameters={"amount": amount}
            )

        else:
            # Default to hold
            return Action(
                agent_name=self.name,
                action_name="hold",
                parameters={}
            )
```

### Step 2: Configure LLM Settings

```yaml
# config.yaml
agents:
  - name: AITrader1
    type: llm_trader
    config:
      system_prompt: |
        You are an aggressive trader seeking maximum returns.
        Take calculated risks for high rewards.
      temperature: 0.8

llm:
  model: "llama3.2"
  host: "http://localhost:11434"
  timeout: 30.0
```

---

## Working with State

### Accessing Your Own State

```python
def decide_action(self, state: SimulationState) -> Action:
    # Direct lookup by agent name
    my_state = state.agents[self.name]

    # Access your variables
    my_wealth = my_state.wealth
    my_position = my_state.position
```

### Accessing Other Agents

```python
def decide_action(self, state: SimulationState) -> Action:
    # Iterate over all agents
    for agent_name, agent_state in state.agents.items():
        if agent_name != self.name:
            competitor_wealth = agent_state.wealth
            # Process competitor data

    # Direct lookup
    if "Competitor1" in state.agents:
        competitor = state.agents["Competitor1"]
```

### Accessing Global State

```python
def decide_action(self, state: SimulationState) -> Action:
    # Global variables shared across all agents
    global_state = state.global_state

    interest_rate = global_state.interest_rate
    turn = global_state.turn
    total_wealth = global_state.total_wealth
```

### Checking Agent Existence

Since agents can be dynamically added/removed:

```python
def decide_action(self, state: SimulationState) -> Action:
    # Safe check before access
    if "Partner" in state.agents:
        partner_state = state.agents["Partner"]
        # Work with partner
    else:
        # Partner doesn't exist or was removed
        logger.warning("partner_not_found", agent=self.name)
```

---

## Partial Observability

When partial observability is enabled, the `state` you receive is filtered based on your observability configuration.

### Understanding Observed State

```python
def decide_action(self, state: SimulationState) -> Action:
    # state is already filtered for this agent

    # Agents you're "unaware" of won't appear in state.agents
    visible_agents = list(state.agents.keys())
    logger.info("visible_agents", agent=self.name, visible=visible_agents)

    # Variables you can see depend on observability level
    if "Competitor" in state.agents:
        competitor = state.agents["Competitor"]
        # external level: only external variables visible
        # insider level: all variables visible

        # Values may have noise applied
        noisy_wealth = competitor.wealth  # May differ from true value
```

### Handling Incomplete Information

```python
def decide_action(self, state: SimulationState) -> Action:
    # Be defensive about missing agents
    known_competitors = [
        name for name in state.agents.keys()
        if name != self.name
    ]

    if not known_competitors:
        # No visible competitors - act cautiously
        return Action(agent_name=self.name, action_name="hold")

    # Work with available information
    avg_competitor_wealth = sum(
        state.agents[name].wealth
        for name in known_competitors
    ) / len(known_competitors)
```

---

## Agent-Initiated Lifecycle Changes

Agents can request lifecycle changes by returning `LifecycleAction` instead of regular `Action`.

### Self-Removal

```python
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation

def decide_action(self, state: SimulationState) -> Action:
    my_state = state.agents[self.name]

    # Exit condition: wealth depleted
    if my_state.wealth <= 0:
        logger.info("agent_exiting", agent=self.name, reason="bankrupt")
        return LifecycleAction(
            operation=LifecycleOperation.REMOVE_AGENT,
            initiating_agent=self.name,
            target_agent_name=self.name
        )

    # Normal action
    return Action(...)
```

### Spawning New Agents

```python
def decide_action(self, state: SimulationState) -> Action:
    my_state = state.agents[self.name]

    # Spawn condition: successful milestone
    if my_state.wealth > 5000 and not hasattr(self, "spawned_partner"):
        logger.info("spawning_partner", agent=self.name)
        self.spawned_partner = True

        return LifecycleAction(
            operation=LifecycleOperation.ADD_AGENT,
            initiating_agent=self.name,
            target_agent_name=f"{self.name}_Partner",
            initial_state={
                "wealth": 1000.0,
                "parent": self.name
            }
        )

    # Normal action
    return Action(...)
```

### Self-Pause (Hibernation)

```python
def decide_action(self, state: SimulationState) -> Action:
    my_state = state.agents[self.name]

    # Pause condition: waiting for market conditions
    if state.global_state.market_volatility > 0.8:
        logger.info("agent_hibernating", agent=self.name)
        return LifecycleAction(
            operation=LifecycleOperation.PAUSE_AGENT,
            initiating_agent=self.name,
            target_agent_name=self.name,
            auto_resume_turns=5  # Wake up in 5 turns
        )

    # Normal action
    return Action(...)
```

### Combining Logic

```python
def decide_action(self, state: SimulationState) -> Action:
    """Decide between lifecycle change and regular action."""
    my_state = state.agents[self.name]

    # Priority 1: Exit if bankrupt
    if my_state.wealth <= 0:
        return self._exit()

    # Priority 2: Spawn if very successful
    if my_state.wealth > 10000 and self._should_spawn():
        return self._spawn_offspring()

    # Priority 3: Hibernate if market bad
    if state.global_state.market_trend == "bearish":
        return self._hibernate()

    # Priority 4: Normal trading action
    return self._decide_trade(state)
```

---

## Action Types

### Regular Action

Standard action for engine execution:

```python
from llm_sim.models.action import Action

action = Action(
    agent_name=self.name,
    action_name="trade",
    parameters={
        "action_type": "buy",
        "amount": 100,
        "target": "stock_xyz"
    }
)
```

### Lifecycle Action

Special action for agent population management:

```python
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation

# Add agent
lifecycle_action = LifecycleAction(
    operation=LifecycleOperation.ADD_AGENT,
    initiating_agent=self.name,
    target_agent_name="NewAgent",
    initial_state={"wealth": 500.0}
)

# Remove agent
lifecycle_action = LifecycleAction(
    operation=LifecycleOperation.REMOVE_AGENT,
    initiating_agent=self.name,
    target_agent_name="OldAgent"
)

# Pause agent
lifecycle_action = LifecycleAction(
    operation=LifecycleOperation.PAUSE_AGENT,
    initiating_agent=self.name,
    target_agent_name=self.name,
    auto_resume_turns=10  # Optional
)

# Resume agent (typically external control)
lifecycle_action = LifecycleAction(
    operation=LifecycleOperation.RESUME_AGENT,
    initiating_agent=self.name,
    target_agent_name="PausedAgent"
)
```

---

## Best Practices

### 1. Defensive State Access

```python
# Good - handles missing agents
if target_agent in state.agents:
    target_state = state.agents[target_agent]
else:
    logger.warning("target_not_found", target=target_agent)
    return self._default_action()

# Bad - crashes if agent removed
target_state = state.agents[target_agent]  # KeyError if missing
```

### 2. Structured Logging

```python
import structlog

logger = structlog.get_logger()

def decide_action(self, state: SimulationState) -> Action:
    # Log with structured context
    logger.info(
        "decision_started",
        agent=self.name,
        turn=state.global_state.turn,
        wealth=state.agents[self.name].wealth
    )

    # ... decision logic

    logger.info(
        "action_decided",
        agent=self.name,
        action=action.action_name,
        parameters=action.parameters
    )

    return action
```

### 3. Validate Your Assumptions

```python
def decide_action(self, state: SimulationState) -> Action:
    my_state = state.agents[self.name]

    # Validate state assumptions
    assert my_state.wealth >= 0, "Wealth should never be negative"
    assert self.name in state.agents, "Agent should exist in state"

    # Validate action before returning
    action = self._compute_action(state)
    assert action.agent_name == self.name, "Action must be from this agent"

    return action
```

### 4. Separate Concerns

```python
class TraderAgent(BaseAgent):
    """Well-structured agent with separated concerns."""

    def decide_action(self, state: SimulationState) -> Action:
        """Main decision entry point."""
        # Check lifecycle conditions first
        lifecycle_action = self._check_lifecycle(state)
        if lifecycle_action:
            return lifecycle_action

        # Normal action decision
        return self._decide_trade(state)

    def _check_lifecycle(self, state: SimulationState) -> LifecycleAction | None:
        """Check if lifecycle change needed."""
        my_state = state.agents[self.name]

        if my_state.wealth <= 0:
            return self._exit()

        if my_state.wealth > 10000:
            return self._spawn_partner()

        return None

    def _decide_trade(self, state: SimulationState) -> Action:
        """Decide trading action."""
        market_analysis = self._analyze_market(state)
        return self._execute_strategy(market_analysis)

    def _analyze_market(self, state: SimulationState) -> Dict:
        """Analyze market conditions."""
        # Market analysis logic
        pass

    def _execute_strategy(self, analysis: Dict) -> Action:
        """Execute trading strategy."""
        # Strategy execution
        pass
```

### 5. Handle Partial Observability

```python
def decide_action(self, state: SimulationState) -> Action:
    # Remember: state is filtered for you

    # Don't assume all agents are visible
    visible_agents = len(state.agents) - 1  # Excluding self
    logger.info("visible_agent_count", count=visible_agents)

    # Don't assume values are exact (noise may be applied)
    if "Competitor" in state.agents:
        # This value may have noise
        observed_wealth = state.agents["Competitor"].wealth

        # Use ranges or thresholds, not exact comparisons
        if observed_wealth > 1000:  # Good
            # ...

        # Avoid: if observed_wealth == 1000:  # Bad - noise makes this fragile
```

### 6. Graceful Degradation

```python
def decide_action(self, state: SimulationState) -> Action:
    try:
        # Attempt primary strategy
        return self._optimal_strategy(state)
    except KeyError as e:
        # Missing expected agent/data
        logger.warning("missing_data", error=str(e))
        return self._fallback_strategy(state)
    except Exception as e:
        # Unexpected error
        logger.error("decision_error", error=str(e))
        return self._safe_default_action()
```

---

## Complete Examples

### Example 1: Population Dynamics Agent

```python
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.lifecycle import LifecycleAction, LifecycleOperation
from llm_sim.models.state import SimulationState
import structlog

logger = structlog.get_logger()

class PopulationAgent(BaseAgent):
    """Agent that can reproduce or die based on resources."""

    def __init__(self, name: str, reproduction_threshold: float = 1000.0):
        super().__init__(name)
        self.reproduction_threshold = reproduction_threshold
        self.generation = 0
        self.offspring_count = 0

    def decide_action(self, state: SimulationState) -> Action:
        """Decide whether to reproduce, die, or gather resources."""
        my_state = state.agents[self.name]

        # Death condition
        if my_state.resources <= 0:
            logger.info("agent_dying", agent=self.name, generation=self.generation)
            return LifecycleAction(
                operation=LifecycleOperation.REMOVE_AGENT,
                initiating_agent=self.name,
                target_agent_name=self.name
            )

        # Reproduction condition
        if my_state.resources >= self.reproduction_threshold:
            self.offspring_count += 1
            offspring_name = f"{self.name}_gen{self.generation + 1}_{self.offspring_count}"

            logger.info(
                "agent_reproducing",
                agent=self.name,
                offspring=offspring_name
            )

            return LifecycleAction(
                operation=LifecycleOperation.ADD_AGENT,
                initiating_agent=self.name,
                target_agent_name=offspring_name,
                initial_state={
                    "resources": my_state.resources * 0.3,  # Transfer 30% to offspring
                    "generation": self.generation + 1,
                    "parent": self.name
                }
            )

        # Normal resource gathering
        return Action(
            agent_name=self.name,
            action_name="gather_resources",
            parameters={"effort": 1.0}
        )
```

### Example 2: Adaptive Strategy Agent

```python
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from typing import Dict
import structlog

logger = structlog.get_logger()

class AdaptiveAgent(BaseAgent):
    """Agent that adapts strategy based on performance."""

    STRATEGIES = ["aggressive", "moderate", "conservative"]

    def __init__(self, name: str):
        super().__init__(name)
        self.current_strategy = "moderate"
        self.performance_history = []
        self.last_wealth = 1000.0

    def decide_action(self, state: SimulationState) -> Action:
        """Decide action and adapt strategy based on performance."""
        my_state = state.agents[self.name]
        current_wealth = my_state.wealth

        # Track performance
        performance = current_wealth - self.last_wealth
        self.performance_history.append(performance)
        self.last_wealth = current_wealth

        # Adapt strategy every 10 turns
        if len(self.performance_history) >= 10:
            self._adapt_strategy()

        # Execute current strategy
        action = self._execute_strategy(state)

        logger.info(
            "adaptive_action",
            agent=self.name,
            strategy=self.current_strategy,
            performance=performance,
            wealth=current_wealth
        )

        return action

    def _adapt_strategy(self):
        """Adapt strategy based on recent performance."""
        avg_performance = sum(self.performance_history[-10:]) / 10

        if avg_performance > 50:
            # Doing well, can be more aggressive
            new_strategy = "aggressive"
        elif avg_performance < -50:
            # Losing money, be conservative
            new_strategy = "conservative"
        else:
            # Moderate performance, stay moderate
            new_strategy = "moderate"

        if new_strategy != self.current_strategy:
            logger.info(
                "strategy_adapted",
                agent=self.name,
                old_strategy=self.current_strategy,
                new_strategy=new_strategy,
                avg_performance=avg_performance
            )
            self.current_strategy = new_strategy

    def _execute_strategy(self, state: SimulationState) -> Action:
        """Execute action based on current strategy."""
        my_state = state.agents[self.name]
        market_price = state.global_state.market_price

        if self.current_strategy == "aggressive":
            # High risk, high reward
            if market_price < 60:
                return Action(
                    agent_name=self.name,
                    action_name="buy",
                    parameters={"amount": my_state.wealth * 0.8}
                )

        elif self.current_strategy == "conservative":
            # Low risk, preserve capital
            if market_price > 120:
                return Action(
                    agent_name=self.name,
                    action_name="sell",
                    parameters={"amount": 50}
                )

        else:  # moderate
            # Balanced approach
            if market_price < 80:
                return Action(
                    agent_name=self.name,
                    action_name="buy",
                    parameters={"amount": my_state.wealth * 0.3}
                )

        # Default: hold
        return Action(
            agent_name=self.name,
            action_name="hold",
            parameters={}
        )
```

### Example 3: Collaborative Agent Network

```python
from llm_sim.infrastructure.base import BaseAgent
from llm_sim.models.action import Action
from llm_sim.models.state import SimulationState
from typing import Set
import structlog

logger = structlog.get_logger()

class NetworkAgent(BaseAgent):
    """Agent that collaborates with trusted partners."""

    def __init__(self, name: str, team: str = None):
        super().__init__(name)
        self.team = team or "independent"
        self.trusted_partners: Set[str] = set()
        self.collaboration_history: Dict[str, int] = {}

    def decide_action(self, state: SimulationState) -> Action:
        """Decide action considering team and partner states."""
        my_state = state.agents[self.name]

        # Update trusted partners based on visible agents
        self._update_partnerships(state)

        # Gather team intelligence
        team_intelligence = self._gather_team_intelligence(state)

        # Decide action based on team context
        if team_intelligence["avg_wealth"] < 500:
            # Team struggling, collaborate
            action = self._collaborate(state, team_intelligence)
        else:
            # Team doing well, compete
            action = self._compete(state)

        logger.info(
            "network_action",
            agent=self.name,
            team=self.team,
            partners=len(self.trusted_partners),
            team_wealth=team_intelligence["avg_wealth"]
        )

        return action

    def _update_partnerships(self, state: SimulationState):
        """Update set of trusted partners based on visibility."""
        # Find team members in visible agents
        for agent_name in state.agents.keys():
            if agent_name == self.name:
                continue

            agent_state = state.agents[agent_name]
            # If same team and visible, trust them
            if hasattr(agent_state, "team") and agent_state.team == self.team:
                if agent_name not in self.trusted_partners:
                    logger.info("new_partner", agent=self.name, partner=agent_name)
                self.trusted_partners.add(agent_name)

    def _gather_team_intelligence(self, state: SimulationState) -> Dict:
        """Gather information about team members."""
        team_members = [
            state.agents[name]
            for name in self.trusted_partners
            if name in state.agents
        ]

        if not team_members:
            return {"avg_wealth": state.agents[self.name].wealth, "count": 1}

        total_wealth = sum(m.wealth for m in team_members)
        avg_wealth = total_wealth / len(team_members)

        return {
            "avg_wealth": avg_wealth,
            "count": len(team_members),
            "total_wealth": total_wealth
        }

    def _collaborate(self, state: SimulationState, intelligence: Dict) -> Action:
        """Collaborative action to help team."""
        return Action(
            agent_name=self.name,
            action_name="support_team",
            parameters={"investment": 100}
        )

    def _compete(self, state: SimulationState) -> Action:
        """Competitive action when team is strong."""
        return Action(
            agent_name=self.name,
            action_name="aggressive_trade",
            parameters={"amount": 200}
        )
```

---

## Next Steps

- **[Simulation Guide](SIMULATION_GUIDE.md)** - Configure simulations and observability
- **[Base Classes Reference](patterns/base_classes.md)** - Complete API documentation
- **[LLM Pattern Guide](patterns/llm_pattern.md)** - Advanced LLM integration
- **[Migration Guide](MIGRATION.md)** - Upgrading between versions

---

**Need examples?** Check the [llm-sim-economic](https://github.com/your-org/llm-sim-economic) repository for complete reference implementations.
