# Feature Specification: Partial Observability for Agents

**Feature Branch**: `008-partial-observability-agents`
**Created**: 2025-10-02
**Status**: Draft
**Input**: User description: "partial-observability    Agents don't see the complete simulation state - only a limited, personalized view based on their position, capabilities, and relationships. This mirrors real-world information constraints.

  Key Features

  Information Filtering: Each agent receives a custom "local state" containing only what they can perceive - not the full global state. A company sees its own detailed finances but only aggregate market statistics.

  Spatial/Network Limits: Agents observe only nearby entities or those connected through networks. Military units see within visual range; social network members only hear from connected friends.

  Information Asymmetry: Different agents have systematically different access - insiders have privileged info, governments have surveillance, predators have better senses than prey.

  Temporal Delays: Information arrives late or stale. Economic data reports quarterly, intelligence ages, discoveries take time to spread.

  Noise and Uncertainty: Observations contain errors, estimates are imprecise, measurements are noisy. Agents must reason under uncertainty.

  Hidden Variables: Some state is completely private - true intentions, secret resources, hidden alliances. Agents must infer through observable signals.

  Active Exploration: Agents can expand observability by spending resources - scouting, forming relationships, investing in sensors.

  Observable Actions: Agents might see others' actions without seeing the full state that motivated them - learning through behavioral observation.

  Why It Matters

  Creates realistic strategic behaviors: deception, signaling, exploration, learning, coordination failures, information markets, intelligence gathering. Makes LLM agents shine since they can reason about uncertainty and
  make inferences from incomplete data.  Agents receive filtered, personalized views of the simulation state instead of seeing everything. The engine maintains the true global state, but constructs limited observations for each agent based on an
  observability matrix.

  Three-Level Observability Model

  Unaware (Level 0): Agent doesn't know the target exists - completely invisible, not included in observations.

  External (Level 1): Agent sees the target exists and can observe "public/external" state variables with configurable noise. Like watching a competitor from outside.

  Insider (Level 2): Agent has privileged access to all state variables (both external and internal) with low/zero noise. Like being inside the organization.

  Configuration Structure

  observability:
    enabled: true

    # Define which variables are public vs private
    variable_visibility:
      external: [economic_strength, position]
      internal: [resources, strategy, hidden_reserves]

    # Observability matrix: who sees whom and how
    # [observer, target, level, noise]
    matrix:
      - [Agent1, Agent1, insider,  0.0]      # Self - always perfect
      - [Agent1, Agent2, external, 0.2]      # Sees public vars with noise
      - [Agent1, Agent3, unaware,  null]     # Invisible

      - [Agent2, Agent2, insider,  0.0]
      - [Agent2, Agent1, unaware,  null]
      - [Agent2, Agent3, insider,  0.05]     # Privileged access

      - [Agent3, Agent3, insider,  0.0]
      - [Agent3, Agent1, external, 0.3]
      - [Agent3, Agent2, external, 0.1]

  Key Design Principles

  Asymmetric: Agent A can see Agent B while B cannot see A.

  Ground truth preserved: Engine maintains exact state, noise only applied to observations.

  Configurable per-pair: Each observer-target pair has independent visibility level and noise.

  Backward compatible: enabled: false or absent = current full-visibility behavior.

  Variable-level control: External vs internal variables defined once, applied everywhere.  the default, if nothing is configured should be complete full observability."

## Execution Flow (main)
```
1. Parse user description from Input
   → If empty: ERROR "No feature description provided"
2. Extract key concepts from description
   → Identify: actors, actions, data, constraints
3. For each unclear aspect:
   → Mark with [NEEDS CLARIFICATION: specific question]
4. Fill User Scenarios & Testing section
   → If no clear user flow: ERROR "Cannot determine user scenarios"
5. Generate Functional Requirements
   → Each requirement must be testable
   → Mark ambiguous requirements
6. Identify Key Entities (if data involved)
7. Run Review Checklist
   → If any [NEEDS CLARIFICATION]: WARN "Spec has uncertainties"
   → If implementation details found: ERROR "Remove tech details"
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

### Section Requirements
- **Mandatory sections**: Must be completed for every feature
- **Optional sections**: Include only when relevant to the feature
- When a section doesn't apply, remove it entirely (don't leave as "N/A")

### For AI Generation
When creating this spec from a user prompt:
1. **Mark all ambiguities**: Use [NEEDS CLARIFICATION: specific question] for any assumption you'd need to make
2. **Don't guess**: If the prompt doesn't specify something (e.g., "login system" without auth method), mark it
3. **Think like a tester**: Every vague requirement should fail the "testable and unambiguous" checklist item
4. **Common underspecified areas**:
   - User types and permissions
   - Data retention/deletion policies
   - Performance targets and scale
   - Error handling behaviors
   - Integration requirements
   - Security/compliance needs

---

## Clarifications

### Session 2025-10-02
- Q: Which features are in scope for initial implementation? → A: Core only: Three-level observability model with noise (unaware/external/insider)
- Q: What noise model should be used for observation uncertainty? → A: Most testable option
- Q: How should the system handle invalid observability configuration? → A: Fail fast: Reject invalid config at simulation startup with clear error messages
- Q: What format should agent observations use? → A: Structurally similar to state model, separate observation representation
- Q: How should the system handle agent pairs not defined in the observability matrix? → A: Configurable default observability level
- Note: Observability applies to global state variables as well - the global state can be treated as an observable entity like agents

---

## User Scenarios & Testing

### Primary User Story
A simulation designer configures varying levels of information visibility between agents in a multi-agent simulation. Each agent receives personalized observations based on their relationships, capabilities, and position relative to other agents and the global state. Agents must make decisions based on incomplete, noisy, or delayed information, creating realistic strategic behaviors like information gathering, deception, and inference.

### Acceptance Scenarios
1. **Given** a simulation with three agents configured with different observability levels, **When** Agent1 requests the current state, **Then** Agent1 receives only information about agents it can observe (excluding "unaware" targets) with appropriate noise levels applied to external observations.

2. **Given** an agent with "external" level access to another agent's state, **When** the agent observes the target, **Then** the agent sees only variables marked as "external" (public) with configured noise applied, while "internal" (private) variables remain hidden.

3. **Given** an agent with "insider" level access to another agent's state, **When** the agent observes the target, **Then** the agent sees all state variables (both external and internal) with minimal or zero noise.

4. **Given** an agent marked as "unaware" of a target agent, **When** the agent requests observations, **Then** the target agent does not appear in the observation at all (complete invisibility).

5. **Given** observability is disabled in the configuration, **When** any agent requests the current state, **Then** the agent receives the complete global state with full visibility (backward compatibility).

6. **Given** no observability configuration is provided, **When** agents request observations, **Then** they receive complete full observability by default.

7. **Given** asymmetric observability where Agent A can see Agent B but B cannot see A, **When** each agent requests observations, **Then** A receives information about B while B receives no information about A.

8. **Given** an observability configuration with a default level set to "external" with 0.1 noise, **When** an agent observes another agent not explicitly defined in the matrix, **Then** the observer receives external variables with 0.1 noise applied.

9. **Given** an agent has "external" level access to global state variables, **When** the agent requests observations, **Then** the agent sees only external global state variables with configured noise, while internal global variables remain hidden.

### Edge Cases
- What happens when noise level is set to 1.0 (100% noise)? Should observations become completely randomized or still preserve some signal?
- How does the system handle circular observability relationships (A observes B, B observes C, C observes A with different levels)?
- **Given** variable_visibility lists contain variables that don't exist in agent state, **When** simulation starts, **Then** system rejects configuration with error identifying undefined variables.
- **Given** observability matrix contains invalid agent IDs, **When** simulation starts, **Then** system rejects configuration with error identifying invalid agent references.
- What happens when an agent's state variables change their visibility classification during runtime?

## Requirements

### Functional Requirements
- **FR-001**: System MUST maintain a complete, accurate global state that represents ground truth for all agents and their state variables.

- **FR-002**: System MUST support an observability configuration that can be enabled or disabled via a boolean flag.

- **FR-003**: System MUST provide complete full observability to all agents when observability is disabled or when no observability configuration is present (default/backward compatible behavior).

- **FR-004**: System MUST support classification of state variables into "external" (public/visible) and "internal" (private/hidden) categories via configuration.

- **FR-005**: System MUST support a three-level observability model: "unaware" (Level 0 - target invisible), "external" (Level 1 - public variables visible with noise), and "insider" (Level 2 - all variables visible with low/zero noise).

- **FR-006**: System MUST construct personalized observation views for each agent based on an observability matrix that defines observer-target relationships for both other agents and global state.

- **FR-007**: System MUST support asymmetric observability where Agent A's view of Agent B can differ from Agent B's view of Agent A.

- **FR-008**: System MUST ensure agents always have "insider" level observability of their own state (perfect self-awareness).

- **FR-009**: System MUST apply configurable noise to observations based on the observability level, where noise is a numeric value representing observation error/uncertainty.

- **FR-010**: System MUST exclude agents marked as "unaware" from an observer's view entirely (no mention of existence).

- **FR-011**: System MUST filter state variables based on observability level: "external" observers see only external variables, "insider" observers see all variables. This applies to both agent state and global state variables.

- **FR-012**: System MUST preserve ground truth state while applying noise only to observations delivered to agents.

- **FR-013**: System MUST support per-pair configuration of observability level and noise in the observability matrix.

- **FR-014**: Observability configuration MUST accept a matrix format where each entry specifies [observer_id, target_id, level, noise_value]. Target IDs can reference agents or global state.

- **FR-014a**: Observability configuration MUST support a configurable default observability level and noise value applied to any observer-target pairs (including global state) not explicitly defined in the matrix.

- **FR-015**: System MUST validate observability matrix entries at simulation startup and reject configuration with clear error messages if any observer or target IDs do not reference valid agents or global state.

- **FR-016**: System MUST validate that variable names in variable_visibility lists correspond to actual state variables at simulation startup and reject configuration with clear error messages if any variables are undefined.

- **FR-017**: System MUST apply noise using a deterministic, testable model with predictable, reproducible results for given noise factors and seed values.

- **FR-018**: Agents MUST receive observations as a separate representation that mirrors the structure of the ground truth state but contains only observable data (filtered and/or noisy values).

- **FR-019**: Observation representation MUST be structurally compatible with the state model to minimize agent logic changes between full and partial observability modes.


### Key Entities

- **Observability Configuration**: Defines the complete observability behavior for a simulation, including whether observability is enabled, how variables are classified, and the observability matrix defining relationships between all agents.

- **Variable Visibility Classification**: Specifies which state variables are "external" (publicly observable) versus "internal" (private/hidden), applicable across all agents in the simulation.

- **Observability Matrix Entry**: A relationship definition specifying how one agent (observer) perceives another entity (target agent or global state), including the observability level (unaware/external/insider) and noise factor applied to observations.

- **Agent Observation**: The personalized, filtered view of simulation state delivered to a specific agent, containing only visible agents, observable global state variables, and their values with noise applied according to the observability matrix.

- **Noise Factor**: A numeric parameter (0.0 to 1.0+) representing the degree of uncertainty or error applied to observations, where 0.0 means perfect information and higher values introduce increasing observation error.

- **Ground Truth State**: The complete, accurate global simulation state maintained by the engine, representing reality before any observability filtering or noise is applied.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain (7 clarifications needed)
- [x] Requirements are testable and unambiguous (where specified)
- [x] Success criteria are measurable
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

---

## Execution Status
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities marked (7 items requiring clarification)
- [x] User scenarios defined
- [x] Requirements generated (21 functional requirements)
- [x] Entities identified (6 key entities)
- [ ] Review checklist passed (blocked by clarifications)

---
