<!-- Sync Impact Report
Version Change: 1.2.0 → 1.3.0 (Added Python Package Management principle)
Modified Principles:
  - None
Added Sections:
  - Principle 7: Python Package Management with uv
Removed Sections:
  - None
Templates Requiring Updates:
  ⚠ .specify/templates/plan-template.md (pending - needs uv references)
  ⚠ .specify/templates/spec-template.md (pending - needs package management requirements)
  ⚠ .specify/templates/tasks-template.md (pending - needs uv task categories)
Follow-up TODOs:
  - Update templates to reference uv for all Python dependency management
-->

# Project Constitution: LLM Simulation Framework

**VERSION**: 1.3.0
**RATIFICATION_DATE**: 2025-01-29
**LAST_AMENDED_DATE**: 2025-01-29
**PROJECT_NAME**: LLM Simulation Framework

## Preamble

This constitution establishes the fundamental principles and governance model for the LLM Simulation Framework project. All development, design decisions, and contributions MUST adhere to these principles.

## Core Principles

### Principle 1: KISS (Keep It Simple and Stupid)

**Name**: Simplicity First

**Description**: Every component, interface, and implementation MUST prioritize simplicity over complexity. Choose the straightforward solution that works over the clever solution that might work better. Complexity is only justified when it provides substantial, measurable benefits.

**Rationale**: Simple code is easier to understand, debug, maintain, and extend. It reduces cognitive load, minimizes bugs, and enables faster onboarding of new contributors.

**Implementation Requirements**:
- Functions MUST do one thing well
- Class hierarchies MUST be shallow (max 3 levels deep)
- Configuration MUST use simple formats (JSON/YAML over custom DSLs)
- Dependencies MUST be minimized and justified
- Abstractions MUST be introduced only when patterns repeat 3+ times

### Principle 2: DRY (Don't Repeat Yourself)

**Name**: Single Source of Truth

**Description**: Every piece of knowledge, logic, or configuration MUST have a single, unambiguous representation in the system. Duplication is technical debt that MUST be eliminated through abstraction, modularization, or refactoring.

**Rationale**: Duplication leads to inconsistencies, increases maintenance burden, and multiplies the locations where bugs can hide. A single source of truth ensures consistency and reduces effort for updates.

**Implementation Requirements**:
- Shared logic MUST be extracted into reusable functions/modules
- Configuration MUST be centralized in single locations
- Constants MUST be defined once and referenced everywhere
- State management MUST follow the three-layer model without duplication
- Templates and patterns MUST be reused across similar components

### Principle 3: No Legacy Support

**Name**: Clean Transitions

**Description**: When implementing new architectures, dataclasses, or any structural changes, there shall be no legacy support mechanisms unless explicitly specified. Legacy support leads to silent failures and technical debt. Instead, old code MUST be directly updated to the new version or removed if obsolete. This ensures clean transitions and prevents accumulation of compatibility layers that obscure system behavior.

**Rationale**: Legacy compatibility layers create hidden complexity, make debugging difficult, and often mask failures that should be explicit. Clean breaks force immediate migration, ensuring all code stays current and maintainable.

**Implementation Requirements**:
- Breaking changes MUST be explicit and fail loudly
- Migration MUST be immediate, not gradual
- Old implementations MUST be removed, not deprecated
- No backward compatibility shims unless explicitly required by specification
- Version transitions MUST be atomic - either fully old or fully new
- Silent fallbacks to legacy behavior are strictly forbidden

### Principle 4: Test-First Development

**Name**: Red-Green-Refactor

**Description**: Test-Driven Development (TDD) is mandatory for all new features. The cycle MUST be: (1) Write tests first, (2) Get user approval on test specifications, (3) Tests must fail initially, (4) Implement to make tests pass, (5) Refactor while keeping tests green. This Red-Green-Refactor cycle MUST be strictly enforced for all development work.

**Rationale**: Writing tests first ensures we understand requirements before implementation, prevents over-engineering, guarantees testability, and provides immediate feedback on correctness. The failing test proves our test actually tests something meaningful.

**Implementation Requirements**:
- Tests MUST be written before implementation code
- Test specifications MUST be approved before proceeding
- Initial test run MUST show failures (red phase)
- Implementation MUST be minimal to pass tests (green phase)
- Refactoring MUST maintain passing tests
- No production code without corresponding tests

### Principle 5: Clean Interface Design

**Name**: Explicit and Composable

**Description**: All public interfaces MUST be explicit and type-annotated. No implicit behaviors or hidden state transitions. Every method MUST have a single, clear responsibility. Complex operations MUST be broken down into composable units rather than monolithic functions.

**Rationale**: Explicit interfaces prevent surprises, enable static analysis, improve IDE support, and make the system predictable. Single responsibility ensures testability and reusability. Composability enables flexible solutions from simple building blocks.

**Implementation Requirements**:
- All public methods MUST have type annotations
- Return types MUST be explicit, never implicit
- State changes MUST be obvious from method signatures
- Methods MUST do one thing only
- Complex logic MUST be decomposed into smaller functions
- Interfaces MUST be documented with clear contracts

### Principle 6: Observability and Debugging

**Name**: Transparent Operations

**Description**: All components MUST provide clear observability through structured logging and meaningful error messages. Text I/O ensures debuggability. Error messages MUST include context, expected values, and actionable remediation steps.

**Rationale**: Systems fail in production. Without observability, debugging becomes guesswork. Clear logging enables quick diagnosis. Meaningful errors reduce support burden. Text-based I/O ensures human readability and scriptability.

**Implementation Requirements**:
- Structured logging MUST be used (not print statements)
- Each component MUST log its key operations
- Errors MUST include: what failed, why, expected vs actual, how to fix
- Debug mode MUST provide detailed execution traces
- All I/O MUST be text-based for inspectability
- Performance metrics MUST be logged for analysis

### Principle 7: Python Package Management with uv

**Name**: Unified Package Management

**Description**: All Python dependency management and package operations MUST use `uv` as the exclusive package manager. All Python scripts and commands MUST be executed through `uv run` to ensure consistent environment isolation and dependency resolution. Direct pip usage or other package managers are strictly forbidden.

**Rationale**: `uv` provides fast, reliable, and deterministic dependency resolution with built-in virtual environment management. Using a single package manager eliminates version conflicts, ensures reproducible builds, and simplifies the development workflow. The `uv run` pattern guarantees that code always executes in the correct environment with proper dependencies.

**Implementation Requirements**:
- All dependency installation MUST use `uv add` or `uv pip install`
- Python scripts MUST be executed with `uv run python` or `uv run <script>`
- Tests MUST be run with `uv run pytest` or equivalent
- Development tools MUST be invoked through `uv run` (e.g., `uv run black`, `uv run mypy`)
- Virtual environments are managed automatically by uv (no manual venv creation)
- The `pyproject.toml` file MUST be the single source of truth for dependencies
- CI/CD pipelines MUST use uv for all Python operations
- Documentation MUST reference uv commands exclusively for Python setup

## Technical Standards

### Architecture Compliance

All implementations MUST adhere to the three-layer state architecture as defined:
1. Global State (Environment) - Read-only for agents
2. Agent State - Two-part structure (Decision-Making and Game Values)
3. State Management Rules - Strict access patterns and update cycles

### Code Quality Requirements

**Mandatory Practices**:
- Code MUST be self-documenting through clear naming
- Comments are only allowed for complex algorithms or business logic
- All public APIs MUST have type hints (Python) or equivalent
- Error handling MUST be explicit, never silent
- Magic numbers MUST be named constants

### Testing Discipline

**Test Coverage Requirements**:
- Core engine components: Minimum 90% coverage
- Agent implementations: Minimum 80% coverage
- Utility functions: 100% coverage
- Integration tests for all major workflows

**Test Principles**:
- Tests MUST be simple and focused (one assertion per test when possible)
- Test names MUST clearly describe what is being tested
- Test data MUST be minimal and representative

### Documentation Standards

**Required Documentation**:
- README with clear setup and usage instructions
- Architecture documentation for system design
- API documentation for public interfaces
- Inline documentation only where behavior is non-obvious

**Documentation Principles**:
- Documentation MUST be maintained alongside code
- Examples are preferred over lengthy explanations
- Diagrams MUST be used for complex relationships

## Governance Model

### Amendment Process

1. **Proposal**: Amendments MUST be proposed via pull request
2. **Review Period**: Minimum 3-day review period for stakeholders
3. **Approval**: Requires consensus from project maintainers
4. **Versioning**: Follow semantic versioning for constitution updates

### Versioning Policy

- **MAJOR**: Removal or fundamental change to core principles
- **MINOR**: Addition of new principles or sections
- **PATCH**: Clarifications, examples, or formatting improvements

### Compliance Review

- All pull requests MUST be reviewed for constitutional compliance
- Violations MUST be addressed before merge
- Repeated violations warrant architecture review

### Enforcement

- Pre-commit hooks MUST validate basic compliance
- CI/CD pipeline MUST enforce testing and quality standards
- Code reviews MUST explicitly check for all principle adherence

## Ratification

This constitution is ratified as of 2025-01-29 and supersedes all previous governance documents.

## Appendix: Practical Examples

### KISS Example
```python
# BAD: Over-engineered
class AbstractStrategyFactoryBuilder:
    def create_factory(self):
        return StrategyFactory()

# GOOD: Simple and direct
def create_agent(agent_type: str):
    return AGENT_REGISTRY[agent_type]()
```

### DRY Example
```python
# BAD: Repeated logic
def process_economic_action(action):
    if not action.is_valid():
        return False
    # 20 lines of processing...

def process_military_action(action):
    if not action.is_valid():
        return False
    # Same 20 lines of processing...

# GOOD: Extracted common logic
def process_action(action, processor):
    if not action.is_valid():
        return False
    return processor.process(action)
```

### No Legacy Support Example
```python
# BAD: Legacy compatibility layer
def load_state(data):
    if 'version' not in data:
        # Silent fallback to legacy format
        return _load_legacy_state(data)
    elif data['version'] == 1:
        return _load_v1_state(data)
    else:
        return _load_v2_state(data)

# GOOD: Explicit migration required
def load_state(data):
    if 'version' not in data or data['version'] < 2:
        raise ValueError(
            f"State format v{data.get('version', 0)} is obsolete. "
            "Run migration script: python migrate_state.py"
        )
    return StateV2.from_dict(data)
```

### Test-First Development Example
```python
# GOOD: TDD Cycle
# 1. Write test first
def test_calculate_trade_value():
    """Test that trade value calculation is correct."""
    trade = Trade(resource="oil", quantity=100, price=50)
    assert trade.calculate_value() == 5000

# 2. Run test - it fails (red)
# 3. Write minimal implementation
class Trade:
    def calculate_value(self):
        return self.quantity * self.price

# 4. Run test - it passes (green)
# 5. Refactor if needed while keeping test green
```

### Clean Interface Example
```python
# BAD: Implicit, monolithic, unclear
def process(data, mode=None, **kwargs):
    # 200 lines doing multiple things
    if mode == 'full':
        # process everything
    return result  # what type?

# GOOD: Explicit, composable, clear
def validate_input(data: dict[str, Any]) -> ValidationResult:
    """Validate input data against schema."""
    return ValidationResult(is_valid=True, errors=[])

def transform_data(data: dict[str, Any]) -> ProcessedData:
    """Transform validated data to internal format."""
    return ProcessedData(data)

def save_result(result: ProcessedData) -> None:
    """Persist processed data to storage."""
    storage.save(result)
```

### Observability Example
```python
# BAD: No context, unhelpful
try:
    process_action(action)
except:
    print("Error")

# GOOD: Full context, actionable
import structlog
logger = structlog.get_logger()

try:
    logger.info("processing_action", action_id=action.id, type=action.type)
    result = process_action(action)
    logger.info("action_completed", action_id=action.id, result=result.status)
except ValidationError as e:
    logger.error(
        "action_validation_failed",
        action_id=action.id,
        expected=e.expected,
        actual=e.actual,
        remediation="Check action format against schema at docs/action-schema.json"
    )
    raise
```

### Python Package Management Example
```bash
# BAD: Inconsistent package management
pip install numpy
python script.py
python -m pytest tests/

# Also BAD: Manual virtual environment management
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# GOOD: Unified uv usage
uv add numpy
uv run python script.py
uv run pytest tests/

# GOOD: Development workflow
uv sync  # Install all dependencies from pyproject.toml
uv run mypy src/  # Run type checking
uv run black .  # Format code
uv run python -m llm_sim.main  # Run the application

# GOOD: CI/CD pipeline
- name: Setup Python with uv
  run: |
    curl -LsSf https://astral.sh/uv/install.sh | sh
    uv sync
    uv run pytest --cov
    uv run mypy src/
```

---

*End of Constitution*
