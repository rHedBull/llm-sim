# LLM Integration Architecture

**Feature**: 004-new-feature-i
**Date**: 2025-09-30

This document explains the three-tier inheritance architecture for LLM integration.

---

## Three-Tier Inheritance Pattern

### Overview

All components (Agent, Validator, Engine) follow the same three-tier pattern:

```
Base (existing ABC)
  → LLM Abstract Layer (new ABC, adds LLM infrastructure)
    → Concrete Domain Implementation (new concrete class)
```

**Purpose**: Separate concerns between:
1. **Base interface** (simulation contract)
2. **LLM infrastructure** (client management, retry, logging)
3. **Domain logic** (economic, military, social, etc.)

---

## Agent Hierarchy

```python
# Tier 1: Base (existing, no changes)
class Agent(ABC):
    """Base simulation agent interface"""
    @abstractmethod
    def decide_action(self, state: SimulationState) -> Action:
        pass

# Tier 2: LLM Infrastructure (new abstract)
class LLMAgent(Agent):
    """Adds LLM reasoning infrastructure to Agent"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def decide_action(self, state: SimulationState) -> Action:
        # Generic LLM workflow (domain-agnostic)
        prompt = self._construct_prompt(state)  # abstract, domain-specific
        decision = await self.llm_client.call_with_retry(prompt, PolicyDecision)
        self._log_reasoning(decision)
        return self._create_action(decision)

    @abstractmethod
    def _construct_prompt(self, state: SimulationState) -> str:
        """Subclass provides domain-specific prompt"""
        pass

    @abstractmethod
    def _validate_decision(self, decision: PolicyDecision) -> bool:
        """Subclass provides domain-specific validation"""
        pass

# Tier 3: Economic Domain (new concrete)
class EconLLMAgent(LLMAgent):
    """Economic policy agent"""
    def _construct_prompt(self, state: SimulationState) -> str:
        return f"""You are an economic advisor.
        Current GDP: {state.gdp}%
        Current Inflation: {state.inflation}%
        Propose ONE economic policy action."""

    def _validate_decision(self, decision: PolicyDecision) -> bool:
        # Check if action mentions economic keywords
        return any(kw in decision.action for kw in ['rate', 'fiscal', 'tax', 'trade'])
```

**Key Benefits**:
- `LLMAgent` handles LLM client, retry, logging (reusable)
- `EconLLMAgent` only defines economic prompts and validation (focused)
- Future domains (military, social) extend `LLMAgent` with their own prompts

---

## Validator Hierarchy

```python
# Tier 1: Base (existing, no changes)
class Validator(ABC):
    """Base simulation validator interface"""
    @abstractmethod
    def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        pass

# Tier 2: LLM Infrastructure (new abstract)
class LLMValidator(Validator):
    """Adds LLM validation infrastructure"""
    def __init__(self, llm_client: LLMClient, permissive: bool = True):
        self.llm_client = llm_client
        self.permissive = permissive

    async def validate_actions(self, actions: List[Action], state: SimulationState) -> List[Action]:
        # Generic LLM validation workflow
        for action in actions:
            prompt = self._construct_validation_prompt(action)  # abstract, domain-specific
            result = await self.llm_client.call_with_retry(prompt, ValidationResult)
            action.validated = result.is_valid
            action.validation_result = result
            self._log_reasoning(result)
        return actions

    @abstractmethod
    def _construct_validation_prompt(self, action: Action) -> str:
        """Subclass provides domain-specific validation prompt"""
        pass

    @abstractmethod
    def _get_domain_description(self) -> str:
        """Subclass defines domain boundaries"""
        pass

# Tier 3: Economic Domain (new concrete)
class EconLLMValidator(LLMValidator):
    """Economic domain validator"""
    def _construct_validation_prompt(self, action: Action) -> str:
        domain_desc = self._get_domain_description()
        return f"""Validate if this action is economic policy:
        Action: {action.action_string}
        Economic domain: {domain_desc}
        Return: is_valid, reasoning"""

    def _get_domain_description(self) -> str:
        return "interest rates, fiscal policy, trade policy, taxation, monetary policy"
```

**Key Benefits**:
- `LLMValidator` handles LLM validation workflow (reusable)
- `EconLLMValidator` only defines economic boundaries (focused)
- Future domains define their own boundaries (military: "troop deployment, defense...")

---

## Engine Hierarchy

```python
# Tier 1: Base (existing, no changes)
class Engine(ABC):
    """Base simulation engine interface"""
    @abstractmethod
    def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        pass

# Tier 2: LLM Infrastructure (new abstract)
class LLMEngine(Engine):
    """Adds LLM state reasoning infrastructure"""
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.current_state = None

    async def run_turn(self, validated_actions: List[Action]) -> SimulationState:
        # Generic LLM state update workflow
        reasoning_chains = []
        for action in validated_actions:
            if not action.validated:
                self._log_skip(action)
                continue

            prompt = self._construct_state_update_prompt(action, self.current_state.global_state)  # abstract
            decision = await self.llm_client.call_with_retry(prompt, StateUpdateDecision)
            reasoning_chains.append(decision)
            self._log_reasoning(decision)

        new_state = self._apply_state_update(decision, self.current_state)  # abstract, domain-specific
        new_state.reasoning_chains = reasoning_chains
        return new_state

    @abstractmethod
    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        """Subclass provides domain-specific state update prompt"""
        pass

    @abstractmethod
    def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
        """Subclass applies domain-specific state changes"""
        pass

# Tier 3: Economic Domain (new concrete)
class EconLLMEngine(LLMEngine):
    """Economic simulation engine"""
    def _construct_state_update_prompt(self, action: Action, state: GlobalState) -> str:
        return f"""You are an economic engine.
        Current interest rate: {state.interest_rate}%
        Action: {action.action_string}
        Calculate new interest rate."""

    def _apply_state_update(self, decision: StateUpdateDecision, state: SimulationState) -> SimulationState:
        # Update interest rate only (economic domain)
        new_global = GlobalState(
            interest_rate=decision.new_interest_rate,
            total_economic_value=state.global_state.total_economic_value
        )
        return SimulationState(
            turn=state.turn + 1,
            agents=state.agents,
            global_state=new_global
        )
```

**Key Benefits**:
- `LLMEngine` handles LLM reasoning workflow and skip logic (reusable)
- `EconLLMEngine` only defines interest rate updates (focused)
- Future domains update their own state fields (military: troop positions, social: happiness index)

---

## Configuration in Orchestrator

```python
class SimulationOrchestrator:
    def _create_agents(self, agent_strategies: Optional[Dict[str, str]] = None) -> List[Agent]:
        agents = []
        llm_client = LLMClient(config=self.config.llm)

        for agent_config in self.config.agents:
            if agent_config.type == "nation":
                # Legacy agent (no LLM)
                agent = NationAgent(name=agent_config.name, strategy="grow")
            elif agent_config.type == "econ_llm_agent":
                # New LLM-based economic agent
                agent = EconLLMAgent(name=agent_config.name, llm_client=llm_client)
            # Future: elif agent_config.type == "military_llm_agent": ...
            agents.append(agent)

        return agents

    def _create_validator(self) -> Validator:
        if self.config.validator.type == "always_valid":
            # Legacy validator
            return AlwaysValidValidator()
        elif self.config.validator.type == "econ_llm_validator":
            # New LLM-based economic validator
            llm_client = LLMClient(config=self.config.llm)
            return EconLLMValidator(
                llm_client=llm_client,
                domain="economic",
                permissive=self.config.validator.permissive
            )
        # Future: elif self.config.validator.type == "military_llm_validator": ...

    def _create_engine(self) -> Engine:
        if self.config.engine.type == "economic":
            # Legacy engine
            return EconomicEngine(self.config)
        elif self.config.engine.type == "econ_llm_engine":
            # New LLM-based economic engine
            llm_client = LLMClient(config=self.config.llm)
            return EconLLMEngine(config=self.config, llm_client=llm_client)
        # Future: elif self.config.engine.type == "military_llm_engine": ...
```

---

## Example Config YAML

```yaml
simulation:
  name: "Economic LLM Simulation"
  max_turns: 10

llm:
  model: "gemma:3"
  host: "http://localhost:11434"
  timeout: 60.0
  max_retries: 1
  temperature: 0.7
  stream: true

agents:
  - name: "USA"
    type: econ_llm_agent  # NEW: LLM-based economic agent
  - name: "EU"
    type: econ_llm_agent  # NEW: LLM-based economic agent

validator:
  type: econ_llm_validator  # NEW: LLM-based economic validator
  domain: economic
  permissive: true

engine:
  type: econ_llm_engine  # NEW: LLM-based economic engine

logging:
  level: DEBUG  # See reasoning chains
  format: json
```

---

## Future Domain Extensions

To add a new domain (e.g., military), you would:

1. **Create abstract layer concrete implementations**:
   - `MilitaryLLMAgent(LLMAgent)` - defines military prompts
   - `MilitaryLLMValidator(LLMValidator)` - defines military domain boundaries
   - `MilitaryLLMEngine(LLMEngine)` - updates troop positions, defense levels

2. **No changes to LLM infrastructure**:
   - `LLMAgent`, `LLMValidator`, `LLMEngine` remain unchanged
   - `LLMClient` remains unchanged

3. **Update Orchestrator config**:
   - Add `"military_llm_agent"`, `"military_llm_validator"`, `"military_llm_engine"` to type mappings

**Benefit**: Each domain is ~100-200 lines of prompt engineering, not full reimplementation.

---

## Class Diagram

```
                    ┌─────────────┐
                    │   Agent     │ (existing ABC)
                    │  (base.py)  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  LLMAgent   │ (new ABC)
                    │(llm_agent.py)│
                    │             │
                    │ + llm_client│
                    │ + decide()  │ (concrete, uses LLM)
                    │ - _prompt() │ (abstract)
                    │ - _validate()│ (abstract)
                    └──────┬──────┘
                           │
              ┌────────────┴────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────────┐
       │EconLLMAgent │          │MilitaryLLMAgent │ (future)
       │(econ_llm_   │          │(military_llm_   │
       │ agent.py)   │          │  agent.py)      │
       │             │          │                 │
       │+ _prompt()  │          │+ _prompt()      │ (military prompts)
       │+ _validate()│          │+ _validate()    │
       └─────────────┘          └─────────────────┘
      (economic prompts)
```

Same pattern for Validator and Engine hierarchies.

---

## Summary

**Three-Tier Pattern Benefits**:
1. **Separation of concerns**: Base interface, LLM infrastructure, domain logic
2. **Reusability**: LLM layer reused across all domains
3. **Extensibility**: New domains = ~100-200 lines of prompts, not full class
4. **Testability**: Can test abstract layer independently of domains
5. **Backward compatibility**: Legacy classes (NationAgent, AlwaysValidValidator, EconomicEngine) unchanged

**Implementation Order**:
1. Create abstract LLM classes first (LLMAgent, LLMValidator, LLMEngine)
2. Implement one concrete domain (Economic) to validate pattern
3. Future domains follow same pattern

---

**Version**: 1.0.0
**Last Updated**: 2025-09-30