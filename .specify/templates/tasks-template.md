# Tasks Template

## Pre-Implementation Checklist
- [ ] Review all constitution principles
- [ ] Write tests first (TDD)
- [ ] Get test approval before implementation
- [ ] Identify reusable components in existing codebase
- [ ] Plan simplest possible implementation
- [ ] Design explicit, type-annotated interfaces
- [ ] Plan observability and error handling
- [ ] Ensure clean transitions without compatibility layers

## Task Categories

### Simplification Tasks (KISS)
- [ ] Identify and remove unnecessary complexity
- [ ] Refactor complex functions into simple ones
- [ ] Replace clever code with clear code
- [ ] Simplify configuration structures

### Consolidation Tasks (DRY)
- [ ] Extract duplicated logic into shared functions
- [ ] Centralize scattered configuration
- [ ] Create reusable components from patterns
- [ ] Consolidate similar implementations

### Migration Tasks (No Legacy Support)
- [ ] Identify and remove legacy compatibility code
- [ ] Update all components to latest version
- [ ] Remove deprecated methods and classes
- [ ] Ensure breaking changes fail explicitly

### Test-First Tasks (TDD)
- [ ] Write test specifications
- [ ] Get test approval
- [ ] Verify tests fail initially (red phase)
- [ ] Implement minimal code to pass tests (green phase)
- [ ] Refactor while maintaining green tests

### Interface Design Tasks
- [ ] Add type annotations to all public methods
- [ ] Break down monolithic functions
- [ ] Document interface contracts
- [ ] Ensure single responsibility per method

### Observability Tasks
- [ ] Add structured logging
- [ ] Implement meaningful error messages
- [ ] Add debug mode traces
- [ ] Include performance metrics

### Core Implementation Tasks
1. **Task Name**: [Clear, simple description]
   - Complexity: [Low/Medium/High - justify if not Low]
   - Reuses: [Existing component being reused]
   - Creates: [New reusable component if any]
   - Dependencies: [Other tasks that must complete first]

### Testing Tasks
- [ ] Write simple, focused unit tests
- [ ] Create minimal integration tests
- [ ] Ensure tests don't duplicate logic

### Documentation Tasks
- [ ] Update README if user-facing changes
- [ ] Document only non-obvious behavior
- [ ] Add examples rather than long explanations

## Task Prioritization

### Priority 1: Simplification
Tasks that reduce complexity come first

### Priority 2: Consolidation
Tasks that eliminate duplication come second

### Priority 3: New Features
New functionality only after simplification and consolidation

## Validation Steps
- [ ] Each task maintains or improves simplicity
- [ ] No task introduces duplication
- [ ] All tasks follow established patterns
- [ ] Complex tasks have been broken into simple ones

## Post-Implementation Review
- [ ] Code is simpler than before
- [ ] No duplication was introduced
- [ ] Existing components were reused
- [ ] New components are reusable