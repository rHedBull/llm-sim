# Feature Specification: LLM-Based Reasoning in Simulation Components

**Feature Branch**: `003-next-we-make`
**Created**: 2025-09-30
**Status**: Draft
**Input**: User description: "Next we make the simulation more complex. The agent, Engine and Validator use LLM form ollama gemma:3 to reason. The agent still get's the state, but uses the llm to reason and come up with an economic policy. the validator now uses the llm to validate. in this case simply if the selected policy is a econ policy and no military for example. the engine then takes that, and reasons, what the new applied intereste rate is based on the selected action, for the agent. The fundamental architecture should stay the same maybe just some adaptations in the classes."

## Clarifications

### Session 2025-09-30
- Q: What are the specific economic policy types to support? → A: No policy types - actions are flexible strings for maximum extensibility across different simulation types
- Q: How should the Validator determine policy type boundaries? → A: LLM reasoning determines domain validity (not predefined type checking)
- Q: What is the expected format for Agent-Engine-Validator communication? → A: Existing Action structure (Agent → Validator → Engine flow), where action contains a string field
- Q: When the LLM fails (unreachable, timeout, or invalid output), what should each component do? → A: Retry LLM call once, then abort if still failing; MUST log prominent error message
- Q: When the Validator rejects an action, what happens next? → A: Engine receives rejection and skips that agent; log info message "SKIPPED Agent [name] due to unvalidated Action"
- Q: Should the system log successful LLM reasoning chains for auditability? → A: Yes - log at DEBUG level (can be enabled when needed)
- Q: For ambiguous boundary cases (e.g., "Implement trade sanctions" - economic or foreign policy?), how should the Validator LLM handle them? → A: Permissive approach - accept if LLM determines any relevant domain impact
- Q: Should simulation results (state + reasoning chains) be persisted to disk/storage after each step, or only kept in memory? → A: Keep in memory only, output final results at simulation end

## Execution Flow (main)
```
1. Parse user description from Input
   → Description extracted successfully
2. Extract key concepts from description
   → Actors: Agent, Validator, Engine
   → Actions: LLM reasoning for policy generation, validation, state updates
   → Data: Economic state, policy decisions, interest rates
   → Constraints: Use Ollama gemma:3, maintain existing architecture
3. For each unclear aspect:
   → Resolved: All ambiguities clarified (8 questions answered)
   → Resolved: Actions use flexible string format (no typed enums)
   → Resolved: Validator uses LLM reasoning for domain validation
   → Resolved: Uses existing Action → Validator → Engine communication structure
   → Resolved: LLM error handling (retry once, abort with prominent log)
   → Resolved: Validator rejection handling (Engine skips agent)
   → Resolved: Logging approach (DEBUG level for reasoning chains)
   → Resolved: Permissive boundary validation
   → Resolved: In-memory results, output at end
4. Fill User Scenarios & Testing section
   → User flow identified: state observation → policy reasoning → validation → state update
5. Generate Functional Requirements
   → Requirements generated with testability criteria
6. Identify Key Entities
   → Entities: Economic State, Policy Decision, Validation Result, Interest Rate Update
7. Run Review Checklist
   → All items passed - spec complete and unambiguous
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## User Scenarios & Testing

### Primary User Story
The simulation system runs scenarios where an autonomous agent observes state indicators, uses LLM reasoning to propose actions (expressed as flexible string descriptions), validates those actions against domain constraints via LLM reasoning, and applies validated actions to update the simulation state. The system must produce explainable, valid decisions with full reasoning chains from all components.

### Acceptance Scenarios
1. **Given** an economic state with current indicators (GDP, inflation, unemployment), **When** the agent processes this state, **Then** the agent must produce an action string with supporting LLM-generated rationale
2. **Given** an agent action (e.g., "Lower interest rates by 0.5%"), **When** the validator evaluates it using LLM reasoning, **Then** the validator must confirm the action is within economic domain boundaries (not military, not social, etc.) and mark it as validated
3. **Given** a validated action, **When** the engine processes it, **Then** the engine must use LLM reasoning to determine and apply the appropriate interest rate adjustment
4. **Given** an invalid action (e.g., "Deploy military forces"), **When** the validator evaluates it, **Then** the validator must reject it with LLM-generated reasoning explaining the domain violation
5. **Given** a simulation step completion, **When** reviewing the results, **Then** all three components (Agent, Validator, Engine) must provide their LLM reasoning chains for auditability

### Edge Cases
- What happens when the LLM reasoning produces ambiguous or unparseable output? → Retry once, then abort with prominent error log
- How does the system handle validator rejection? → Engine skips that agent, logs info "SKIPPED Agent [name] due to unvalidated Action"
- What happens if the Engine cannot determine an appropriate state update from the action string? → Retry LLM once, then abort
- What happens when the LLM service is unreachable or times out? → Retry once, then abort with prominent error log
- How does Validator handle ambiguous boundary cases? → Permissive approach - accept if LLM finds any relevant domain impact

## Requirements

### Functional Requirements
- **FR-001**: Agent MUST accept simulation state as input and produce an action string with supporting rationale
- **FR-002**: Agent MUST utilize LLM reasoning to generate action strings based on observed state
- **FR-003**: Agent MUST provide explainable LLM-generated rationale for each action
- **FR-004**: Validator MUST evaluate action strings against domain constraints using LLM reasoning
- **FR-005**: Validator MUST use LLM reasoning (not predefined type checking) to determine if an action is valid for the current simulation domain
- **FR-005a**: Validator MUST use permissive validation approach - accept actions if LLM determines any relevant domain impact (not strict primary-purpose requirement)
- **FR-006**: Validator MUST reject actions that fall outside the simulation domain with LLM-generated reasoning
- **FR-007**: Validator MUST mark actions as validated or rejected and forward decisions to Engine
- **FR-008**: Engine MUST skip agents with rejected actions and log info message "SKIPPED Agent [name] due to unvalidated Action"
- **FR-008a**: Engine MUST accept validated actions and determine appropriate state updates
- **FR-009**: Engine MUST use LLM reasoning to interpret action strings and determine specific state changes (e.g., interest rate adjustments for economic simulations)
- **FR-010**: Engine MUST provide LLM-generated reasoning for state update decisions
- **FR-011**: Engine MUST apply the determined state changes to update the simulation
- **FR-012**: System MUST preserve the existing Action → Validator → Engine communication flow (minimal class adaptations)
- **FR-013**: System MUST support flexible action strings (not typed enums) to enable different simulation types
- **FR-014**: System MUST retry failed LLM calls exactly once before aborting
- **FR-015**: System MUST log prominent, highly visible error messages when LLM failures cause simulation abort
- **FR-016**: System MUST abort the simulation step when LLM fails after retry
- **FR-017**: System MUST log all successful LLM reasoning chains at DEBUG level for auditability
- **FR-018**: System MUST keep simulation results (state + reasoning chains) in memory during execution
- **FR-019**: System MUST output final simulation results only at simulation end (no intermediate persistence)

### Key Entities

- **Simulation State**: Current state containing domain-specific indicators (e.g., GDP, inflation, unemployment, interest rate for economic simulations) that the Agent observes and the Engine updates
- **Action**: Agent's output containing a flexible action string and LLM-generated reasoning; communicated through existing Action structure
- **Validation Result**: Validator's LLM-based determination of whether an action is valid for the simulation domain, including validated/rejected status and reasoning
- **State Update Decision**: Engine's output containing specific state changes (e.g., new interest rate) and LLM-generated reasoning for the update based on validated action
- **Reasoning Chain**: Explanatory LLM output from Agent, Validator, or Engine that justifies decisions for transparency and debugging

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
- [x] Ambiguities resolved (8 clarifications provided)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---