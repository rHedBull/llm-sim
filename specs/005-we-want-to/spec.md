# Feature Specification: Separate Simulation Infrastructure from Domain Implementations

**Feature Branch**: `005-we-want-to`
**Created**: 2025-09-30
**Status**: Draft
**Input**: User description: "we want to now seperate the simulation loop abstract component't from the actual simulation implementation, for example, base.py and llm_agent.py are abstract classes, but nation and econ_llm_agen.py are the actual implementation of these and that are used in the simulation definition. we want to seperate these, similar for engine and validator. to make the usage of the simulation loop infrastructure as abstract standardized and flexible as possible and provide some sample more specific abstract classes that can easily be used, like the llm_agent.py"

## Execution Flow (main)
```
1. Parse user description from Input
   → Extract goal: separate abstract infrastructure from concrete domain implementations
2. Extract key concepts from description
   → Identify: abstract classes, concrete implementations, simulation infrastructure, domain-specific code
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → User wants to create new simulations easily using infrastructure
5. Generate Functional Requirements
   → Each requirement must be testable
6. Identify Key Entities (abstractions and implementations)
7. Run Review Checklist
   → Verify no implementation details (tech stack)
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-09-30
- Q: FR-007 - How should architecture organization be made discoverable? → A: File placement in directory makes concrete classes usable in simulations
- Q: FR-010 - How should patterns be documented for abstract classes? → A: Separate documentation files
- Q: How should NationAgent fit into the architecture alongside LLM agents? → A: Both are concrete implementations (NationAgent extends BaseAgent directly; EconLLMAgent extends LLMAgent which extends BaseAgent)
- Q: Architectural clarification → A: Two-tier architecture: Abstract classes (BaseAgent/BaseEngine/BaseValidator and LLMAgent/LLMEngine/LLMValidator) → Concrete implementations (EconLLMAgent/EconLLMEngine/EconLLMValidator/NationAgent)
- Q: How should simulation configs reference concrete implementations after reorganization? → A: By filename only (e.g., agent: econ_llm_agent); if file exists in concrete implementations directory and validly implements abstract class, it's usable

---

## User Scenarios & Testing

### Primary User Story
A developer wants to create a new simulation domain (e.g., military, environmental, social) without reimplementing the core simulation loop infrastructure. They should be able to:
1. Understand what abstract classes are available for the infrastructure
2. Choose appropriate abstract classes that provide patterns they need (like LLM-enabled agents via `LLMAgent`, or simple scripted agents via `BaseAgent`)
3. Implement only domain-specific logic in concrete classes
4. Run simulations using the standard orchestration without modifying core infrastructure

### Acceptance Scenarios
1. **Given** a developer wants to create an economic simulation, **When** they review available abstractions, **Then** they can identify that `LLMAgent`, `LLMEngine`, and `LLMValidator` provide LLM-enabled infrastructure they can extend with economic-specific logic
2. **Given** an existing economic simulation with `EconLLMAgent`, `EconLLMEngine`, and `EconLLMValidator`, **When** a developer wants to create a military simulation, **Then** the concrete economic classes should be clearly separated so they can create parallel military-specific implementations
3. **Given** the simulation infrastructure, **When** a developer wants to understand the architecture, **Then** they can distinguish between abstract classes (BaseAgent, BaseEngine, BaseValidator, LLMAgent, LLMEngine, LLMValidator) and concrete domain implementations (EconLLMAgent, NationAgent, EconLLMEngine, EconLLMValidator)
4. **Given** the separated architecture, **When** a developer creates a new simulation, **Then** the orchestrator should work with any combination of concrete implementations without modification

### Edge Cases
- How should simple scripted agents (like `NationAgent`) that extend `BaseAgent` directly coexist with LLM-enabled agents that extend `LLMAgent` in the same simulation?
- How are dependencies between infrastructure components documented and enforced?
- What happens when a concrete implementation partially implements an abstract interface?

## Requirements

### Functional Requirements
- **FR-001**: System MUST separate abstract simulation infrastructure from concrete domain-specific implementations
- **FR-002**: System MUST provide abstract classes (`BaseAgent`, `BaseEngine`, `BaseValidator`) that define minimal interface contracts for the simulation loop
- **FR-003**: System MUST provide abstract classes for common patterns (`LLMAgent`, `LLMEngine`, `LLMValidator`) that implement LLM-enabled reasoning without domain specifics
- **FR-004**: System MUST organize concrete implementations (e.g., `EconLLMAgent`, `NationAgent`, `EconLLMEngine`, `EconLLMValidator`) separately from abstract infrastructure
- **FR-005**: System MUST allow developers to create new simulation domains by extending abstract classes without modifying infrastructure code
- **FR-006**: System MUST maintain backward compatibility with existing simulations after reorganization (configs reference implementations by filename only)
- **FR-007**: System MUST organize concrete implementations in dedicated directories where file placement makes them automatically discoverable and usable by referencing filename in configuration (e.g., agent: econ_llm_agent)
- **FR-008**: System MUST provide sample concrete implementations that demonstrate how to extend different abstract classes (BaseAgent for simple scripted agents, LLMAgent for LLM-enabled agents)
- **FR-009**: Orchestrator MUST work with any concrete implementation that conforms to abstract interfaces
- **FR-010**: System MUST provide separate documentation files explaining what patterns each abstract class provides (e.g., LLM reasoning, validation, state updates)
- **FR-011**: System MUST validate that referenced concrete implementations exist in the concrete directory and properly implement required abstract interfaces before allowing simulation execution

### Key Entities

- **Abstract Classes**: Interface definitions and pattern implementations for simulation components (agents, engines, validators). Includes both minimal interfaces like `BaseAgent` and pattern-providing abstractions like `LLMAgent` that concrete classes can extend
- **Concrete Domain Implementations**: Specific implementations for particular simulation domains (economic, military, environmental, etc.) that extend abstract classes with domain-specific logic
- **Infrastructure Components**: Core simulation loop orchestration that works with any concrete implementation conforming to abstract interfaces
- **Simulation Definition**: Configuration and setup that selects and instantiates concrete implementations to create a runnable simulation

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
