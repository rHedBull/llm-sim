# Feature Specification: Event Stream Activity Logging

**Feature Branch**: `010-event-stream-the`
**Created**: 2025-10-04
**Status**: Draft
**Input**: User description: "event-stream       The event stream enhancement adds fine-grained activity logging to simulations, capturing every significant action between checkpoint snapshots.

  What Gets Captured:
  - Agent decisions and actions (investments, policy changes, strategic moves)
  - State variable transitions (economic indicators changing, resource levels updating)
  - Inter-agent interactions (trades, communications, conflicts)
  - System events (validation failures, LLM API calls, retry attempts)
  - Causality links showing what triggered each change

  Data Storage:
  The llm-sim framework writes a single events.jsonl file in each simulation's output directory, appending events as they occur during the simulation run.

  Server Capabilities:
  The API server discovers these event files, exposes an endpoint to retrieve events, and supports filtering by time range, event type, specific agents, or turn numbers.

  Visualization Benefits:
  The UI can display detailed timelines, filter event streams by criteria, show causality chains explaining state changes, animate simulation playback, and provide audit trails for debugging or analysis.

  Architecture Philosophy:
  This is a simple file-based approach suitable for small-to-medium simulations, avoiding infrastructure complexity while enabling rich observability. If scale demands it later, the same data could migrate to a
  proper time-series database.
  this must be integrated at import parts of the existing code. there should be information levels. like TURN,   - MILESTONE - Turn boundaries, phase transitions, major outcomes
  - DECISION - Agent strategic choices, policy changes
  - ACTION - Individual agent actions, transactions
  - STATE - Variable changes, resource updates
  - DETAIL - Granular calculations, intermediate values  and the deepest level of wanted event streaming configurable"

## Execution Flow (main)
```
1. Parse user description from Input
   → SUCCESS: Feature description provided
2. Extract key concepts from description
   → Identified: event logging, activity tracking, filtering, observability levels
3. For each unclear aspect:
   → [NEEDS CLARIFICATION: Default verbosity level for simulations]
   → [NEEDS CLARIFICATION: Maximum event stream size limits or rotation policy]
   → [NEEDS CLARIFICATION: Event retention policy after simulation completes]
4. Fill User Scenarios & Testing section
   → SUCCESS: User flows identified
5. Generate Functional Requirements
   → Each requirement testable and linked to scenarios
6. Identify Key Entities
   → SUCCESS: Event entities identified
7. Run Review Checklist
   → WARN "Spec has uncertainties - marked with [NEEDS CLARIFICATION]"
8. Return: SUCCESS (spec ready for planning after clarifications)
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

---

## Clarifications

### Session 2025-10-04
- Q: What should be the default verbosity level when no level is explicitly configured for a simulation? → A: ACTION - Captures turn milestones, decisions, and individual actions (balanced observability)
- Q: How should the system handle event file size limits during long-running simulations? → A: Rotation at 500MB - Create timestamped files (events_2025-10-04_14-30.jsonl)
- Q: What should happen to event files when a simulation output directory is deleted or archived? → A: Delete with output directory - Events tied to simulation lifecycle, no separate retention
- Q: How should the system handle event write failures when the logging system cannot keep up with event generation rate? → A: Drop events - Continue simulation, log warning (maintains simulation speed, loses data)
- Q: How should causality links be represented when a single event triggers multiple simultaneous consequences? → A: One-to-many array - Source event ID stored in array field on each consequence
- Q: What metadata fields should be REQUIRED in every JSONL event entry (beyond timestamp and turn_number)? → A: event_id, timestamp, turn_number, event_type, simulation_id, agent_id (optional), caused_by (optional array)
- Q: Should the event-specific payload (beyond required metadata) follow a standardized schema or be flexible per event type? → A: Hybrid - Common fields defined (e.g., "description", "details"), plus type-specific optional fields

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
As a simulation researcher or analyst, I need to understand what happened during a simulation run at varying levels of detail. Between checkpoint snapshots, many significant events occur that are currently invisible. The event stream gives me a complete activity log showing every agent decision, state change, interaction, and system event, allowing me to debug issues, analyze causality chains, and replay simulations step-by-step.

### Acceptance Scenarios

1. **Given** a simulation is running, **When** an agent makes a strategic decision (e.g., changes investment policy), **Then** the event stream captures the decision with timestamp, agent identifier, decision type, and causal context.

2. **Given** a simulation has completed, **When** I request events filtered by a specific agent, **Then** the API returns only events involving that agent in chronological order.

3. **Given** a simulation is running with MILESTONE verbosity, **When** a turn boundary is crossed, **Then** only turn transitions and major outcomes are logged, not individual agent actions.

4. **Given** a simulation is running with DETAIL verbosity, **When** a state variable changes, **Then** the event stream captures the old value, new value, triggering action, and intermediate calculations.

5. **Given** multiple simulations have completed, **When** I query the API for a specific simulation's events, **Then** the server discovers and returns events from the correct events.jsonl file.

6. **Given** event filtering by turn number range, **When** I request events from turns 5-10, **Then** only events occurring within that turn range are returned.

7. **Given** event filtering by event type, **When** I request only DECISION events, **Then** the response excludes all ACTION, STATE, and DETAIL events.

8. **Given** an LLM API call fails and retries, **When** the system event occurs, **Then** the event stream captures the failure, retry attempt count, and eventual outcome.

9. **Given** two agents interact (e.g., trade or conflict), **When** the interaction occurs, **Then** the event stream links both agents and captures the bidirectional relationship.

10. **Given** a UI timeline visualization, **When** displaying events, **Then** users can filter by criteria, follow causality chains, and animate playback through the simulation.

### Edge Cases

- What happens when the event file reaches 500MB during simulation execution?
- How does the system handle write failures to the event file during simulation execution?
- What happens if events are generated faster than the logging system can write them?
- How is the user notified when events are being dropped due to write backlog?
- How are causality arrays structured when a single event has multiple triggering sources?
- What happens if the API server encounters a corrupted events.jsonl file?
- How does filtering perform on very large event streams (millions of events)?
- What happens when events from parallel agent actions need timestamps with sub-millisecond precision?

---

## Requirements *(mandatory)*

### Functional Requirements

**Event Capture**
- **FR-001**: Every event MUST include required metadata: event_id, timestamp (ISO 8601), turn_number, event_type, simulation_id
- **FR-002**: Agent-related events MUST include agent_id field; system events MUST NOT include agent_id
- **FR-003**: Events with causal triggers MUST include caused_by array containing source event_id values
- **FR-004**: Every event SHOULD include common payload fields: description (human-readable summary), details (structured data object)
- **FR-005**: System MUST capture agent strategic decisions with type-specific fields: decision_type, old_value, new_value
- **FR-006**: System MUST capture state variable transitions with type-specific fields: variable_name, old_value, new_value
- **FR-007**: System MUST capture inter-agent interactions with type-specific fields: interaction_type, participating_agent_ids
- **FR-008**: System MUST capture system events with type-specific fields: error_type, status, retry_count (if applicable)
- **FR-009**: System MUST support multiple causality sources per event (one-to-many causality relationships)

**Verbosity Levels**
- **FR-010**: System MUST support configurable verbosity levels: MILESTONE, DECISION, ACTION, STATE, DETAIL
- **FR-011**: System MUST filter logged events based on the configured verbosity level
- **FR-012**: MILESTONE level MUST capture only turn boundaries, phase transitions, and major outcomes
- **FR-013**: DECISION level MUST capture MILESTONE events plus agent strategic choices and policy changes
- **FR-014**: ACTION level MUST capture DECISION events plus individual agent actions and transactions
- **FR-015**: STATE level MUST capture ACTION events plus variable changes and resource updates
- **FR-016**: DETAIL level MUST capture STATE events plus granular calculations and intermediate values
- **FR-017**: System MUST allow verbosity level configuration per simulation run (defaults to ACTION level if not specified)

**Data Storage**
- **FR-018**: System MUST write events to events.jsonl file(s) in the simulation's output directory
- **FR-019**: System MUST append events to the file as they occur during simulation execution
- **FR-020**: System MUST rotate event files when size reaches 500MB, creating timestamped files (events_YYYY-MM-DD_HH-MM.jsonl)
- **FR-021**: System MUST ensure each event is written as a complete JSON line
- **FR-022**: System MUST generate unique event_id values for each event

**API Server Capabilities**
- **FR-023**: API server MUST discover all event files (including rotated timestamped files) from completed simulations
- **FR-024**: API server MUST expose an endpoint to retrieve events for a specific simulation
- **FR-025**: API server MUST aggregate events from multiple rotated files when serving a single simulation
- **FR-026**: API server MUST support filtering events by time range (start timestamp to end timestamp)
- **FR-027**: API server MUST support filtering events by event type (MILESTONE, DECISION, ACTION, STATE, DETAIL)
- **FR-028**: API server MUST support filtering events by specific agent identifiers
- **FR-029**: API server MUST support filtering events by turn number or turn range
- **FR-030**: API server MUST return events in chronological order across all rotated files
- **FR-031**: API server MUST handle pagination for large event streams

**Observability & Visualization**
- **FR-032**: System MUST provide event data suitable for timeline visualization
- **FR-033**: System MUST preserve causality links in event data for chain analysis
- **FR-034**: Event data MUST be structured to support playback animation
- **FR-035**: Event data MUST include sufficient context for debugging and audit trails

**Data Management**
- **FR-036**: System MUST handle event file write failures gracefully without crashing simulations
- **FR-037**: When event writes cannot keep up with generation rate, system MUST drop events and continue simulation execution
- **FR-038**: System MUST log a warning event when dropping events due to write backlog
- **FR-039**: System MUST validate events.jsonl file integrity before serving via API
- **FR-040**: Event files MUST be deleted when the simulation output directory is deleted (no separate retention policy)

### Key Entities *(include if feature involves data)*

- **Event**: Represents a single significant occurrence during simulation execution. Required fields: event_id (unique identifier), timestamp (ISO 8601 format), turn_number (integer), event_type (MILESTONE/DECISION/ACTION/STATE/DETAIL), simulation_id (simulation identifier). Optional standard fields: agent_id (present for agent-specific events, absent for system events), caused_by (array of event_id values indicating causality sources). Common payload fields: description (human-readable summary), details (structured data object). Type-specific optional fields vary by event type (e.g., state changes include old_value/new_value, decisions include decision_type).

- **Causality Link**: Represents the relationship between triggering events and resulting events. Implemented as an array field on each event containing one or more source event identifiers that caused this event to occur.

- **Event Stream**: The complete chronological sequence of events for a simulation run. Stored as a single JSONL file with one event per line.

- **Event Filter**: Criteria used to retrieve a subset of events. Contains optional time range (start/end timestamps), event type list, agent identifier list, and turn number range.

---

## Review & Acceptance Checklist
*GATE: Automated checks run during main() execution*

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
*Updated by main() during processing*

- [x] User description parsed
- [x] Key concepts extracted
- [x] Ambiguities resolved (5 clarifications answered)
- [x] User scenarios defined
- [x] Requirements generated
- [x] Entities identified
- [x] Review checklist passed

---
