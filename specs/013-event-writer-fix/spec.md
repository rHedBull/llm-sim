# Feature Specification: EventWriter Synchronous Mode Implementation

**Feature Branch**: `013-event-writer-fix`
**Created**: 2025-10-08
**Status**: Draft
**Input**: User description: "event-writer-fix # EventWriter Synchronous Mode Implementation

## Overview

This document provides a detailed implementation plan for adding synchronous write mode to the EventWriter class. This solution addresses the root cause of missing `events.jsonl` files while providing a clean migration path for future microservices architecture.

## Problem Statement

The current EventWriter uses an async background task to write events, but the simulation runs in `_run_turn_sync()` which blocks the event loop, preventing the background task from executing. Events are queued but never written to disk.

## Solution Architecture

### Design Principles

1. **Mode-Based Operation**: Support both async and sync modes in the same class
2. **Zero Breaking Changes**: Existing async code continues to work unchanged
3. **Simple API**: Same `emit()` interface for both modes
4. **Service-Ready**: Easy to migrate to remote event service later
5. **Thread-Safe**: Synchronous mode is safe for future threading models

### Class Architecture

```
EventWriter
├── Mode Selection (async/sync)
├── Async Path (existing)
│   ├── Queue-based buffering
│   ├── Background _write_loop()
│   └── Graceful shutdown with flush
└── Sync Path (new)
    ├── Direct file writes
    ├── Immediate flush
    └── Synchronous rotation
```"

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

---

## User Scenarios & Testing

### Primary User Story
**As a** simulation operator
**I want** events from simulation runs to be reliably persisted to disk
**So that** I can review, analyze, and debug simulation behavior through the event log after the simulation completes

### Acceptance Scenarios

1. **Given** a simulation is configured to record events, **When** the simulation runs to completion, **Then** all generated events MUST be written to an event file on disk

2. **Given** the event writer is operating in synchronous mode, **When** an event is emitted, **Then** the event MUST be immediately written and flushed to disk before control returns to the caller

3. **Given** the event writer is operating in asynchronous mode, **When** an event is emitted, **Then** the event MUST be queued and written by a background task without blocking the caller

4. **Given** an event file reaches its maximum size threshold, **When** a new event is emitted, **Then** the system MUST rotate the current file to a timestamped archive file and start a new current event file

5. **Given** the simulation completes or stops, **When** the event writer is shut down, **Then** all pending events MUST be written to disk before shutdown completes (async mode) or already be written (sync mode)

6. **Given** the simulation uses blocking synchronous execution contexts, **When** the event writer mode is configured, **Then** the system MUST default to or use synchronous mode to ensure events are written despite blocked event loops

### Edge Cases

- What happens when the disk is full and an event cannot be written?
  - System MUST log an error indicating the write failure and the specific event that failed

- What happens when the event file rotation fails (e.g., file permissions issue)?
  - System MUST log a rotation failure error and continue writing to the current file if possible

- What happens when the event queue is full in async mode?
  - System MUST drop the event and increment a dropped event counter, logging a warning periodically

- What happens when multiple events are emitted faster than disk write speed in sync mode?
  - System MUST block on each write, ensuring durability at the cost of performance (documented trade-off)

- What happens when the simulation is interrupted or crashes?
  - In sync mode: all events up to the interruption point MUST be on disk
  - In async mode: queued events may be lost (documented limitation)

## Requirements

### Functional Requirements

- **FR-001**: System MUST support two operational modes for event writing: synchronous and asynchronous
- **FR-002**: System MUST allow configuration of the event writer mode at initialization time
- **FR-003**: In synchronous mode, system MUST write each event immediately to disk and flush all OS buffers before returning control
- **FR-004**: In asynchronous mode, system MUST queue events and write them via a background task without blocking event emission
- **FR-005**: System MUST filter events based on verbosity level before writing
- **FR-006**: System MUST rotate event files when they exceed a configurable maximum file size
- **FR-007**: System MUST create timestamped archive filenames during rotation to prevent collisions
- **FR-008**: System MUST ensure output directory exists before attempting to write events
- **FR-009**: System MUST maintain a running count of the current event file size for rotation decisions
- **FR-010**: System MUST provide graceful shutdown that ensures all events are written before termination
- **FR-011**: System MUST log event writer lifecycle events (initialization, start, stop, rotation, errors)
- **FR-012**: System MUST count and report dropped events in async mode when queue is full
- **FR-013**: System MUST serialize events to JSON format with newline delimiters (JSONL)
- **FR-014**: System MUST handle write errors gracefully by logging the error and identifying the failed event
- **FR-015**: Synchronous mode MUST guarantee event persistence by flushing to disk on every write
- **FR-016**: Asynchronous mode start operation MUST be a no-op when in synchronous mode
- **FR-017**: Asynchronous mode stop operation MUST be a no-op when in synchronous mode (events already written)
- **FR-018**: System MUST expose a consistent `emit()` interface regardless of selected mode
- **FR-019**: System MUST default to a mode appropriate for the execution context [NEEDS CLARIFICATION: should default be sync or async? User spec suggests sync for reliability]

### Key Entities

- **Event**: A simulation occurrence to be recorded, consisting of event type, simulation ID, timestamp, and event-specific data
- **Event File**: The current active file receiving event writes (events.jsonl)
- **Rotated Event File**: An archived event file with a timestamped filename (events_YYYY-MM-DD_HH-MM-SS-ffffff.jsonl)
- **Event Writer Mode**: The operational mode (synchronous or asynchronous) determining write behavior
- **Event Queue**: A buffer for events awaiting asynchronous write (async mode only)
- **Verbosity Level**: A filter determining which event types should be written based on importance
- **Write Metrics**: Statistics tracking total events written, bytes written, errors, rotations, and latency

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain (1 marker: FR-019 default mode)
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
- [ ] Review checklist passed (pending clarification on FR-019)

---
