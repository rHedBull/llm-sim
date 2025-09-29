# Implementation Plan: Simulation Loop

## Constitution Check
- ✅ KISS Principle: Simple YAML config, minimal class hierarchy, single-threaded execution
- ✅ DRY Principle: Base classes for Agent/Engine/Validator, centralized state management
- ✅ No Legacy Support: Clean greenfield implementation with no backwards compatibility
- ✅ Test-First Development: Tests will be written before each component implementation
- ✅ Clean Interface Design: Typed pydantic models, ABC interfaces, single responsibility
- ✅ Observability: Structured logging at each simulation step, clear error messages

## Feature Overview
Build a simple turn-based simulation loop with YAML configuration, supporting multiple agents (nations) with economic growth via interest rates. The MVP implements a basic economic simulation with 2 nations, each having an economic_strength value that grows by a configured interest rate each turn.

## Design Approach

### Simplicity Analysis
- Current complexity level: Low
- Justification for any complexity: ABC base classes needed for extensibility
- Simpler alternatives considered:
  - Single monolithic class (rejected: violates separation of concerns)
  - No validation layer (rejected: reduces reliability and observability)

### Reusability Check
- Existing components to reuse:
  - Python's logging module
  - Pydantic for data validation
  - PyYAML for configuration loading
  - ABC for interface definitions
- New components that will be reusable:
  - BaseAgent abstract class
  - BaseEngine abstract class
  - BaseValidator abstract class
  - State and Action pydantic models
- Duplication being eliminated:
  - Single state management in Engine
  - Centralized configuration loading
  - Unified logging approach

## Implementation Steps

### Phase 0: Research & Analysis
1. Analyze existing codebase structure
2. Identify integration points
3. Document technology choices

### Phase 1: Design Artifacts
1. Define data models (State, Action, SimConfig)
2. Create interface contracts (Agent, Engine, Validator ABCs)
3. Write quickstart documentation

### Phase 2: Task Breakdown
1. Create detailed implementation tasks
2. Define dependencies and order
3. Estimate effort for each task

## Validation Criteria
- [x] No code duplication introduced
- [x] Solution is understandable without extensive documentation
- [x] Existing patterns and utilities are reused
- [x] Complexity is justified and documented

## Risk Assessment
- Complexity risks: None identified for MVP
- Duplication risks: None - centralized state management
- Mitigation strategies: Maintain strict separation of concerns

## Progress Tracking
- [x] Phase 0: Research complete
- [x] Phase 1: Design artifacts generated
- [x] Phase 2: Task breakdown created
- [x] Verification: All artifacts validated