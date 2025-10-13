# Phase 0 Research: Complex Data Type Support for State Variables

**Feature**: `014-data-variable-type` | **Date**: 2025-10-13 | **Research Phase Output**

## Purpose

This document provides comprehensive research findings for implementing complex data type support (dict, list, tuple, str, object) in the VariableDefinition system. All decisions are based on Pydantic 2.x capabilities and best practices.

---

## 1. Pydantic 2.x Complex Type Support

### 1.1 Dict Types with Dynamic Keys and Fixed Schemas

#### Decision
Use `RootModel[Dict[str, ValueType]]` for dynamic keys with constrained value types. For nested models with dict fields, use standard field annotations like `my_dict: dict[str, SomeModel]`.

#### Rationale
- Pydantic 2.x deprecated `__root__` in favor of `RootModel` for cleaner type handling
- `RootModel` provides attribute access methods while maintaining validation
- Dict annotations with type parameters (e.g., `dict[str, int]`) automatically validate both keys and values
- More efficient than custom validators for simple key-value constraints

#### Implementation Pattern
```python
from pydantic import BaseModel, RootModel, Field
from typing import Dict

# For dynamic keys at the root level
class PersonModel(BaseModel):
    age: int = Field(ge=0)
    postcode: int = Field(ge=1000, le=9999)

class PeopleRegistry(RootModel):
    root: Dict[str, PersonModel]

    def __getattr__(self, item: str):
        return self.root.__getitem__(item)

# For dict fields in a model
class AgentState(BaseModel):
    inventory: dict[str, int] = Field(default_factory=dict)  # item_name -> quantity
    metadata: dict[str, str] = Field(default_factory=dict)
```

#### Alternatives Considered
1. **TypedDict**: Limited to fixed keys; doesn't support truly dynamic key sets
2. **Custom validators with `__root__`**: Deprecated in Pydantic 2.x
3. **Mapping type**: Less efficient than dict; triggers additional isinstance checks

#### Performance Notes
- Using concrete `dict` type is faster than abstract `Mapping` type
- TypedDict with TypeAdapter is ~2.5x faster than nested BaseModel for read-only scenarios
- For our use case (write-heavy validation), BaseModel provides better ergonomics

#### References
- [Pydantic 2.x Dicts and Mapping](https://docs.pydantic.dev/latest/concepts/types/)
- [Stack Overflow: Dynamic keys in Pydantic v2](https://stackoverflow.com/questions/77413598/dynamic-keys-in-pydantic-v2)

---

### 1.2 List Types with Item Type Constraints

#### Decision
Use `Annotated[list[ItemType], Field(...)]` for list validation with constraints. Push constraints down to the item type using `list[Annotated[ItemType, Field(...)]]` when item-level validation is needed.

#### Rationale
- Pydantic 2.x changed constraint semantics: constraints on `list` apply to the list itself, not items
- `Annotated` provides explicit, reusable type definitions
- Supports min/max length, uniqueness, and custom validation at both container and item levels
- Maintains strict mode compatibility (only list instances accepted, not tuples/sets)

#### Implementation Pattern
```python
from pydantic import BaseModel, Field
from typing import Annotated

# List-level constraints (length)
class HistoryModel(BaseModel):
    events: Annotated[list[str], Field(min_length=1, max_length=1000)]

# Item-level constraints (pattern validation on each string)
class TaggedModel(BaseModel):
    tags: list[Annotated[str, Field(pattern=r'^[a-z_]+$')]]

# Combined constraints
class CoordinateModel(BaseModel):
    position: Annotated[
        list[Annotated[float, Field(ge=-180.0, le=180.0)]],
        Field(min_length=2, max_length=3)
    ]  # 2D or 3D coordinates within bounds
```

#### Alternatives Considered
1. **Field constraints on generic parameter (Pydantic v1 style)**: No longer works in v2
2. **Custom validator for each list**: More verbose, less reusable
3. **Sequence type**: Less efficient than list; triggers additional type checks

#### Best Practices
- Use `default_factory=list` instead of `default=[]` to avoid mutable default issues
- For strict validation, set `strict=True` in Field to reject non-list types
- Consider `FailFast` annotation if validation should stop at first error (performance)

#### References
- [Pydantic 2.x Lists and Tuples](https://docs.pydantic.dev/2.0/usage/types/list_types/)
- [Pydantic Migration Guide - Field Constraints](https://docs.pydantic.dev/latest/migration/)

---

### 1.3 Tuple Types with Per-Element Type Constraints

#### Decision
Use typed tuple annotations like `tuple[int, str, float]` for fixed-length tuples with per-position type constraints. Use `tuple[ItemType, ...]` for variable-length tuples with homogeneous items.

#### Rationale
- Pydantic 2.x natively supports per-position tuple validation
- Type annotations directly express the schema (no additional configuration needed)
- Validation automatically coerces from lists/sequences when parsing JSON
- Clear error messages include position index in validation errors

#### Implementation Pattern
```python
from pydantic import BaseModel, Field
from typing import Annotated

# Fixed-length tuple with heterogeneous types
class LocationModel(BaseModel):
    # (x: int, y: int, label: str)
    position: tuple[int, int, str]

# Variable-length tuple with homogeneous types
class PathModel(BaseModel):
    coordinates: tuple[float, ...]  # Any number of floats

# Constrained tuple items
class BoundedRangeModel(BaseModel):
    range: tuple[
        Annotated[float, Field(ge=0.0)],
        Annotated[float, Field(le=100.0)]
    ]  # (min >= 0, max <= 100)
```

#### JSON Serialization Behavior
**IMPORTANT**: Tuples are serialized as arrays in JSON and lose immutability:
- Python: `(1, 2, 3)` → JSON: `[1, 2, 3]` → Python: `(1, 2, 3)`
- Immutability is preserved on round-trip validation but not in JSON representation
- Consider documenting this behavior for users who care about immutability

#### Alternatives Considered
1. **Using lists**: Loses semantic meaning of "fixed structure"
2. **Custom validators**: Unnecessary complexity; native support is sufficient
3. **Dataclasses with frozen=True**: Doesn't integrate well with Pydantic validation

#### Validation Error Format
- Error location for tuple: `('field_name', 1)` where `1` is the tuple index
- Clear messages like "Input should be a valid integer" at specific positions

#### References
- [Pydantic 2.x Standard Library Types](https://docs.pydantic.dev/latest/api/standard_library_types/)
- [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/)

---

### 1.4 Nested Object Schemas (Recursive)

#### Decision
Use self-referencing models with forward annotations (`'ModelName'` as string) and rely on Pydantic's built-in cyclic reference detection. Call `model_rebuild()` after model definition if needed.

#### Rationale
- Pydantic 2.x natively detects cyclic references during validation (raises `ValidationError` instead of `RecursionError`)
- Forward annotations resolve automatically during model creation
- No manual recursion limit tracking needed - Pydantic handles it
- Serialization also detects cycles and raises `ValueError` with clear message

#### Implementation Pattern
```python
from pydantic import BaseModel, Field
from typing import Optional

# Self-referencing model
class TreeNode(BaseModel):
    value: int
    children: list['TreeNode'] = Field(default_factory=list)
    parent: Optional['TreeNode'] = None

# Rebuild if references are complex or circular
TreeNode.model_rebuild()

# Mutual recursion
class Category(BaseModel):
    name: str
    products: list['Product'] = Field(default_factory=list)

class Product(BaseModel):
    name: str
    category: Optional[Category] = None

# Rebuild both models
Category.model_rebuild()
Product.model_rebuild()
```

#### Cyclic Reference Behavior
```python
# Validation error for cyclic data
node = TreeNode(value=1)
node.children = [node]  # Self-reference
# Raises: ValidationError("Recursion error - cyclic reference detected")

# Serialization error for cyclic data
valid_tree = TreeNode(value=1, children=[TreeNode(value=2)])
valid_tree.children[0].parent = valid_tree  # Create cycle
# valid_tree.model_dump() raises: ValueError("Circular reference detected")
```

#### Alternatives Considered
1. **Manual depth tracking**: Unnecessary; Pydantic handles it automatically
2. **Flattening nested structures**: Loses semantic meaning and requires complex bookkeeping
3. **Disallowing recursion entirely**: Too restrictive for real-world use cases

#### Limitations
- Max nesting depth is Python's recursion limit (~1000 levels on most systems)
- For very deep structures (>100 levels), consider flattening or using references
- Serialization with cycles requires custom serializers (see Pydantic docs)

#### References
- [Pydantic Forward Annotations](https://docs.pydantic.dev/latest/concepts/forward_annotations/)
- [Pydantic Recursive Models Tutorial](https://www.kevsrobots.com/learn/pydantic/06_recursive_models.html)

---

### 1.5 Validation Error Messages with Field Paths

#### Decision
Use Pydantic's default error structure with `loc` tuples and provide a helper function to convert to dot notation for user-facing error messages.

#### Rationale
- Pydantic's `loc` field provides complete path to error in nested structures
- Tuple format `('field', 0, 'subfield')` is machine-readable
- Converting to dot notation `'field[0].subfield'` is more user-friendly
- Consistent with industry standards (JSON Path, JSONPath)

#### Implementation Pattern
```python
from pydantic import ValidationError, BaseModel

def loc_to_dot_sep(loc: tuple[str | int, ...]) -> str:
    """Convert Pydantic error location tuple to dot notation.

    Examples:
        ('inventory', 'food') -> 'inventory.food'
        ('agents', 0, 'position') -> 'agents[0].position'
        ('nested', 'deeply', 1, 'field') -> 'nested.deeply[1].field'
    """
    path = ''
    for i, x in enumerate(loc):
        if isinstance(x, str):
            path += '.' if i > 0 else ''
            path += x
        elif isinstance(x, int):
            path += f'[{x}]'
    return path

# Usage in error handling
try:
    model.model_validate(data)
except ValidationError as e:
    for error in e.errors():
        field_path = loc_to_dot_sep(error['loc'])
        print(f"Error at {field_path}: {error['msg']}")
        # Output: "Error at inventory.food: Input should be a valid integer"
```

#### Error Structure
Each error in `ValidationError.errors()` contains:
- `loc`: Tuple path to the field (e.g., `('agents', 0, 'state', 'health')`)
- `msg`: Human-readable message (e.g., "Input should be a valid integer")
- `type`: Machine-readable error type (e.g., "int_type", "missing", "greater_than")
- `input`: The actual invalid value received
- `ctx`: Optional context dict with additional info (e.g., `{'ge': 0}` for minimum value)
- `url`: Link to Pydantic error documentation

#### Best Practices
1. **Preserve original loc**: Keep tuple format in logs for debugging
2. **User-facing messages**: Convert to dot notation for CLI output
3. **Context inclusion**: Include `ctx` values in messages (e.g., "must be >= 0")
4. **Multiple errors**: Report all errors at once (don't use `FailFast` in config load)

#### Alternatives Considered
1. **Custom error classes**: Unnecessary; Pydantic's structure is comprehensive
2. **JSONPath format**: More complex than needed for our use case
3. **Flat error structure**: Loses nesting information

#### References
- [Pydantic Error Handling](https://docs.pydantic.dev/latest/errors/errors/)
- [Pydantic Validation Errors](https://docs.pydantic.dev/latest/errors/validation_errors/)

---

### 1.6 Performance Characteristics of Nested Validation

#### Decision
Use `model_validate_json()` for JSON input, reuse validators, prefer concrete types, and use TypedDict for read-only nested data. Set `cache_strings='keys'` for repeated string keys.

#### Rationale
- `model_validate_json()` is faster than `model_validate(json.loads(...))` (single-pass parsing)
- TypedDict is ~2.5x faster than nested BaseModel (but less flexible for mutation)
- Concrete types (`dict`, `list`) are faster than abstract types (`Mapping`, `Sequence`)
- String caching reduces memory allocation for repeated keys (common in dictionaries)
- Wrap validators have ~20% overhead; avoid in hot paths

#### Optimization Patterns
```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Annotated

# 1. Use model_validate_json for JSON input
class FastModel(BaseModel):
    data: dict[str, int]

# Slow: two-pass (parse JSON, then validate)
import json
slow_instance = FastModel.model_validate(json.loads(json_string))

# Fast: single-pass
fast_instance = FastModel.model_validate_json(json_string)

# 2. Configure string caching
class CachedModel(BaseModel):
    model_config = ConfigDict(cache_strings='keys')  # Cache dict keys only

    metadata: dict[str, str]  # Repeated keys benefit from caching

# 3. Prefer concrete types
class EfficientModel(BaseModel):
    # Fast: concrete types
    items: list[int]
    mapping: dict[str, float]

    # Slow: abstract types (more isinstance checks)
    # items: Sequence[int]
    # mapping: Mapping[str, float]

# 4. Avoid wrap validators in hot paths
class ValidatedModel(BaseModel):
    # Fast: field validator (after mode)
    @field_validator('value', mode='after')
    @classmethod
    def check_value(cls, v: int) -> int:
        if v < 0:
            raise ValueError("must be non-negative")
        return v

    # Slow: wrap validator (materializes data in Python)
    # @field_validator('value', mode='wrap')
    # @classmethod
    # def check_value_wrap(cls, v, handler):
    #     result = handler(v)
    #     if result < 0:
    #         raise ValueError("must be non-negative")
    #     return result
```

#### Performance Benchmarks (from Pydantic docs)
- BaseModel validation: Baseline
- TypedDict with TypeAdapter: ~2.5x faster (read-only scenarios)
- `model_validate_json()`: ~30% faster than two-pass validation
- String caching: ~15% faster for dict-heavy models with repeated keys
- Wrap validators: ~20% slower than after validators

#### Our Target Performance
- Validation goal: <10ms for typical state (100 agents × 50 variables with 3 dicts, 2 lists, 1 tuple each)
- Estimated per-agent validation: <0.1ms (100µs)
- Estimated per-variable validation: <2µs

**Strategy to meet target**:
1. Use `model_validate_json()` for checkpoint loading
2. Enable string caching for dict-heavy state
3. Avoid wrap validators entirely
4. Use concrete types (`dict`, `list`, `tuple`) throughout
5. Profile with `pytest-benchmark` to identify bottlenecks

#### Alternatives Considered
1. **Manual validation**: Much slower and error-prone
2. **Marshmallow/Cerberus**: Slower than Pydantic 2.x's Rust core
3. **No validation**: Unsafe; silent failures in production

#### Memory Usage
- Pydantic models: ~200-500 bytes overhead per instance
- String caching: +~10% memory for cached strings (worthwhile tradeoff)
- Nested models: Memory grows linearly with nesting depth (predictable)

#### References
- [Pydantic Performance Guide](https://docs.pydantic.dev/latest/concepts/performance/)
- [Pydantic at Scale: 7 Tricks for 2x Faster Validation](https://medium.com/@connect.hashblock/pydantic-v2-at-scale-7-tricks-for-2-faster-validation-9bd95bf27232)

---

## 2. Circular Reference Detection

### 2.1 Algorithms for Detecting Cycles

#### Decision
Use Depth-First Search (DFS) with recursion stack tracking for schema definition cycle detection. Rely on Pydantic's runtime cyclic reference detection for data validation.

#### Rationale
- DFS is the standard algorithm for cycle detection in directed graphs (O(V+E) time complexity)
- Recursion stack tracks "currently visiting" nodes, distinguishing back edges (cycles) from cross/forward edges
- Pydantic handles runtime data cycles automatically; we only need schema-level detection
- Schema graphs are small (typically <100 nodes), so algorithm choice matters less than clarity

#### Implementation Pattern
```python
from typing import Set, List, Optional

def detect_schema_cycle(
    schema_name: str,
    schema_graph: dict[str, list[str]],
    visited: Set[str],
    rec_stack: Set[str],
    path: List[str]
) -> Optional[List[str]]:
    """Detect cycles in schema dependency graph using DFS.

    Args:
        schema_name: Current schema being explored
        schema_graph: Dict mapping schema names to their dependencies
        visited: Set of all visited schemas
        rec_stack: Set of schemas in current recursion stack
        path: Current path for cycle reporting

    Returns:
        List of schema names forming the cycle, or None if no cycle
    """
    visited.add(schema_name)
    rec_stack.add(schema_name)
    path.append(schema_name)

    # Explore dependencies
    for dependency in schema_graph.get(schema_name, []):
        if dependency not in visited:
            cycle = detect_schema_cycle(dependency, schema_graph, visited, rec_stack, path)
            if cycle:
                return cycle
        elif dependency in rec_stack:
            # Back edge found - cycle detected
            cycle_start = path.index(dependency)
            return path[cycle_start:] + [dependency]

    # Backtrack
    rec_stack.remove(schema_name)
    path.pop()
    return None

# Usage example
schema_deps = {
    'AgentState': ['Inventory', 'Position'],
    'Inventory': ['Item'],
    'Item': ['ItemCategory'],
    'ItemCategory': ['Item'],  # CYCLE!
}

visited = set()
rec_stack = set()
path = []
cycle = detect_schema_cycle('AgentState', schema_deps, visited, rec_stack, path)
if cycle:
    print(f"Cycle detected: {' -> '.join(cycle)}")
    # Output: "Cycle detected: Item -> ItemCategory -> Item"
```

#### Algorithm Complexity
- **Time**: O(V + E) where V = number of schemas, E = number of dependencies
- **Space**: O(V) for visited/rec_stack sets, O(D) for recursion depth D
- **Typical case**: V < 20 schemas, E < 50 dependencies → <1ms execution time

#### Alternatives Considered
1. **Tarjan's Algorithm**: More complex; overkill for simple cycle detection
2. **Kahn's Algorithm (Topological Sort)**: Detects cycles but doesn't provide cycle path
3. **Floyd's Cycle Detection**: Designed for linked lists; doesn't apply to general graphs
4. **Union-Find**: Doesn't detect cycles in directed graphs (only undirected)

#### Why DFS Over Alternatives
- Simplest to implement and understand
- Provides actual cycle path for error reporting
- Standard algorithm taught in CS courses (well-known)
- Sufficient performance for our scale

#### References
- [GeeksforGeeks: Detect Cycle in Directed Graph](https://www.geeksforgeeks.org/dsa/detect-cycle-in-a-graph/)
- [Baeldung: Detecting Cycles in Directed Graphs](https://www.baeldung.com/cs/detecting-cycles-in-directed-graph)

---

### 2.2 Reporting Cycle Paths to Users

#### Decision
Format cycle paths as `A -> B -> C -> A` with schema names and field names. Include remediation suggestions (use references, flatten structure, or rethink design).

#### Rationale
- Visual arrow notation clearly shows cycle direction
- Including field names (e.g., `Agent.inventory -> Inventory.owner -> Agent`) helps users locate exact problem
- Remediation suggestions educate users on proper schema design patterns
- Consistent with other validation error formats in the system

#### Error Message Format
```python
from llm_sim.models.exceptions import CircularSchemaError

class CircularSchemaError(Exception):
    """Raised when a circular reference is detected in schema definitions."""

    def __init__(self, cycle_path: List[str], field_path: List[str]):
        self.cycle_path = cycle_path
        self.field_path = field_path

        # Format cycle path
        cycle_str = ' -> '.join(cycle_path)

        # Format field path (if available)
        if field_path:
            field_str = ' -> '.join(f"{schema}.{field}" for schema, field in zip(cycle_path, field_path))
            message = (
                f"Circular reference detected in schema definitions:\n"
                f"  Cycle: {cycle_str}\n"
                f"  Fields: {field_str}\n\n"
                f"Suggested fixes:\n"
                f"  1. Use Optional[ForwardRef] for back-references\n"
                f"  2. Use string IDs instead of nested objects\n"
                f"  3. Flatten the schema structure"
            )
        else:
            message = (
                f"Circular reference detected in schema definitions:\n"
                f"  Cycle: {cycle_str}\n\n"
                f"Suggested fixes:\n"
                f"  1. Use Optional[ForwardRef] for back-references\n"
                f"  2. Use string IDs instead of nested objects\n"
                f"  3. Flatten the schema structure"
            )

        super().__init__(message)

# Usage
try:
    validate_schemas(definitions)
except CircularSchemaError as e:
    logger.error("Schema validation failed", cycle=e.cycle_path, fields=e.field_path)
    raise
```

#### Example Error Output
```
Circular reference detected in schema definitions:
  Cycle: Agent -> Inventory -> Item -> Agent
  Fields: Agent.inventory -> Inventory.items -> Item.owner -> Agent

Suggested fixes:
  1. Use Optional[ForwardRef] for back-references
  2. Use string IDs instead of nested objects
  3. Flatten the schema structure
```

#### User-Facing Documentation
Include a section in the user guide explaining:
1. **What cycles are**: "A cycle occurs when schema A references B, which references C, which references back to A"
2. **Why they're problematic**: "Cycles can cause infinite recursion during validation or serialization"
3. **How to fix them**: Examples of each remediation strategy
4. **When they're okay**: "Pydantic can handle cycles in data at runtime; this error is about schema definitions"

#### Alternatives Considered
1. **Just listing schema names**: Doesn't help users locate the problem fields
2. **JSON pointer format**: Less readable than arrow notation
3. **No remediation suggestions**: Users left guessing how to fix the issue

#### References
- [Pydantic Forward Annotations](https://docs.pydantic.dev/latest/concepts/forward_annotations/)

---

## 3. Nesting Depth Validation

### 3.1 Strategies for Enforcing Max Depth Limits

#### Decision
Implement a recursive schema traversal function that tracks current depth and raises an error when max depth is exceeded. Run this during config load (fail-fast) rather than during runtime validation.

#### Rationale
- Config load is the right place to enforce architectural constraints (depth limits are design rules, not data validation)
- Fail-fast prevents users from running simulations with problematic configs
- Recursive traversal is simple and matches the structure being validated
- Separating depth validation from Pydantic validation keeps concerns separated

#### Implementation Pattern
```python
from pydantic import BaseModel
from typing import Any, get_args, get_origin

MAX_DICT_DEPTH = 4  # Per spec requirements
MAX_LIST_DEPTH = 3  # Per spec requirements

class DepthLimitError(Exception):
    """Raised when nesting depth exceeds configured limits."""
    pass

def check_nesting_depth(
    field_type: type,
    current_depth: int,
    max_depth: int,
    field_path: str,
    container_type: str  # 'dict' or 'list'
) -> None:
    """Recursively check nesting depth of complex types.

    Args:
        field_type: Type to check (may be generic like dict[str, dict[str, int]])
        current_depth: Current depth level (starts at 0)
        max_depth: Maximum allowed depth
        field_path: Dot-notation path for error reporting
        container_type: 'dict' or 'list' to track separately

    Raises:
        DepthLimitError: If nesting exceeds max_depth
    """
    if current_depth > max_depth:
        raise DepthLimitError(
            f"Nesting depth exceeds limit for {container_type} at '{field_path}': "
            f"{current_depth} > {max_depth}"
        )

    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is dict:
        # Check dict nesting depth
        if container_type == 'dict' or current_depth == 0:
            # dict[str, T] - recurse into value type
            if len(args) >= 2:
                check_nesting_depth(
                    args[1],
                    current_depth + 1,
                    max_depth,
                    f"{field_path}.<value>",
                    'dict'
                )

    elif origin is list or origin is tuple:
        # Check list/tuple nesting depth
        if container_type == 'list' or current_depth == 0:
            # list[T] - recurse into item type
            if args:
                item_type = args[0] if origin is list else args[0] if len(args) == 2 and args[1] is ... else None
                if item_type:
                    check_nesting_depth(
                        item_type,
                        current_depth + 1,
                        max_depth,
                        f"{field_path}[*]",
                        'list'
                    )

    elif isinstance(field_type, type) and issubclass(field_type, BaseModel):
        # Nested model - check its fields
        for field_name, field_info in field_type.model_fields.items():
            check_nesting_depth(
                field_info.annotation,
                current_depth,  # Don't increment for object nesting, only for collections
                max_depth,
                f"{field_path}.{field_name}",
                container_type
            )

# Usage in config loading
def validate_variable_definition_depth(var_def: VariableDefinition) -> None:
    """Validate that variable definition doesn't exceed depth limits."""
    type_annotation = var_def.get_type_annotation()

    try:
        # Check dict depth
        check_nesting_depth(type_annotation, 0, MAX_DICT_DEPTH, var_def.name, 'dict')
        # Check list depth
        check_nesting_depth(type_annotation, 0, MAX_LIST_DEPTH, var_def.name, 'list')
    except DepthLimitError as e:
        logger.error("Depth limit exceeded", variable=var_def.name, error=str(e))
        raise
```

#### When to Run Depth Validation
1. **Config load time** (preferred): During `SimulationConfig.model_validate()`
2. **Variable definition registration**: When `VariableDefinition` is created
3. **NOT during runtime**: Depth is a static property of schemas, not data

#### Alternatives Considered
1. **Pydantic validator**: Would run on every data validation (performance cost)
2. **Manual depth counting in user code**: Error-prone and not enforced
3. **No depth limits**: Risk of excessive nesting causing performance issues

#### Edge Cases
- **Mixed nesting**: `dict[str, list[dict[str, int]]]` - track depths separately
- **Object nesting**: Objects don't count toward depth (only collections do)
- **Union types**: Check depth of all union members
- **Optional types**: Unwrap Optional and check inner type

#### References
- [Python typing module: get_origin and get_args](https://docs.python.org/3/library/typing.html)

---

### 3.2 Traversing Schema Definitions to Calculate Depth

#### Decision
Use `typing.get_origin()` and `typing.get_args()` to introspect generic types recursively. Track dict and list depths separately since they have different limits.

#### Rationale
- `get_origin()` returns the base generic type (e.g., `dict` from `dict[str, int]`)
- `get_args()` returns type parameters (e.g., `(str, int)` from `dict[str, int]`)
- Standard library solution; no external dependencies
- Works with all Pydantic-compatible type annotations

#### Type Introspection Patterns
```python
from typing import get_origin, get_args, Union, Optional
import inspect

def introspect_type(annotation: type) -> dict[str, Any]:
    """Extract structure information from a type annotation.

    Returns:
        Dict with keys: 'origin', 'args', 'is_model', 'is_union', 'is_optional'
    """
    origin = get_origin(annotation)
    args = get_args(annotation)

    info = {
        'origin': origin,
        'args': args,
        'is_model': isinstance(annotation, type) and issubclass(annotation, BaseModel),
        'is_union': origin is Union,
        'is_optional': origin is Union and type(None) in args,
    }

    return info

# Example usage
from typing import Optional

def analyze_field(field_type: type) -> None:
    info = introspect_type(field_type)
    print(f"Origin: {info['origin']}")
    print(f"Args: {info['args']}")
    print(f"Is BaseModel: {info['is_model']}")
    print(f"Is Optional: {info['is_optional']}")

# Test with various types
analyze_field(dict[str, int])
# Output:
#   Origin: <class 'dict'>
#   Args: (<class 'str'>, <class 'int'>)
#   Is BaseModel: False
#   Is Optional: False

analyze_field(Optional[list[str]])
# Output:
#   Origin: typing.Union
#   Args: (<class 'list'>[<class 'str'>], <class 'NoneType'>)
#   Is BaseModel: False
#   Is Optional: True
```

#### Handling Special Cases
```python
def get_collection_item_type(field_type: type) -> Optional[type]:
    """Extract item type from list/tuple/set annotations.

    Examples:
        list[int] -> int
        tuple[str, ...] -> str
        set[float] -> float
        dict[str, int] -> int (value type)
    """
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin in (list, set):
        return args[0] if args else None
    elif origin is tuple:
        # tuple[int, ...] -> int (homogeneous)
        # tuple[int, str, float] -> None (heterogeneous, no single item type)
        if len(args) == 2 and args[1] is ...:
            return args[0]
        return None
    elif origin is dict:
        return args[1] if len(args) >= 2 else None

    return None

def unwrap_optional(field_type: type) -> type:
    """Remove Optional wrapper from a type annotation.

    Examples:
        Optional[int] -> int
        Union[int, None] -> int
        int -> int (unchanged)
    """
    origin = get_origin(field_type)
    args = get_args(field_type)

    if origin is Union:
        # Filter out NoneType
        non_none_args = [arg for arg in args if arg is not type(None)]
        if len(non_none_args) == 1:
            return non_none_args[0]

    return field_type
```

#### Integration with Depth Checking
The introspection functions above integrate with the depth checking algorithm in §3.1 to handle complex nested types correctly.

#### Alternatives Considered
1. **String parsing of type repr**: Fragile; breaks with complex types
2. **Custom type registry**: Unnecessary complexity
3. **Pydantic's schema generation**: Overkill; we only need structure info

#### Performance Notes
- Type introspection is fast: ~1µs per field
- Results can be cached for repeated use
- Only runs once during config load

#### References
- [Python typing module documentation](https://docs.python.org/3/library/typing.html)
- [PEP 585: Type Hinting Generics In Standard Collections](https://peps.python.org/pep-0585/)

---

## 4. JSON Serialization Patterns

### 4.1 Tuple Serialization (List vs Tuple in JSON)

#### Decision
Accept that tuples serialize to JSON arrays and document this behavior. Use `model_validate_json()` for round-trip consistency (JSON array → tuple per annotation).

#### Rationale
- JSON has no tuple type; arrays are the only sequence type
- Pydantic 2.x behavior: tuple → JSON array → tuple (consistent round-trip)
- Immutability is a Python runtime concept, not serializable to JSON
- Users should rely on type annotations, not JSON representation, for immutability

#### Serialization Behavior
```python
from pydantic import BaseModel

class LocationModel(BaseModel):
    position: tuple[int, int]  # (x, y)
    tags: list[str]

# Python -> JSON
loc = LocationModel(position=(10, 20), tags=["indoor", "safe"])
json_output = loc.model_dump_json()
# Output: {"position": [10, 20], "tags": ["indoor", "safe"]}
# Note: position is an array, indistinguishable from tags

# JSON -> Python
loc_restored = LocationModel.model_validate_json(json_output)
# loc_restored.position is tuple[int, int] again (not list)
# loc_restored.tags is list[str]

# Type correctness preserved despite JSON representation
assert isinstance(loc_restored.position, tuple)  # ✓
assert isinstance(loc_restored.tags, list)       # ✓
```

#### Documentation for Users
Include in user guide:
```markdown
### Tuple Serialization in JSON

**Important**: JSON does not have a tuple type. Tuples are serialized as arrays:
- Python: `(1, 2, 3)` → JSON: `[1, 2, 3]`
- When loading from JSON, Pydantic restores the correct Python type based on your annotations
- Immutability is preserved in Python code, not in the JSON file

**Example**:
```python
# Define a model with a tuple
class Position(BaseModel):
    coords: tuple[float, float]

# Save to JSON
pos = Position(coords=(1.5, 2.5))
json_str = pos.model_dump_json()  # {"coords": [1.5, 2.5]}

# Load from JSON
pos_loaded = Position.model_validate_json(json_str)
pos_loaded.coords  # tuple[float, float] again!
```

**When to use tuples vs lists**:
- Use `tuple` for fixed-length, semantically immutable sequences (coordinates, RGB colors)
- Use `list` for variable-length, mutable collections (history, inventory)
```

#### Alternatives Considered
1. **Custom serializer for tuples**: Would break JSON compatibility
2. **Metadata field to distinguish tuples**: Added complexity for little benefit
3. **Disallow tuples in variable definitions**: Too restrictive; tuples are useful

#### Impact on Checkpoints
- Checkpoint files (JSON) will have arrays for both lists and tuples
- Loading checkpoints respects type annotations in `VariableDefinition`
- No migration needed for existing scalar-only checkpoints

#### References
- [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/)
- [JSON Specification (RFC 8259)](https://tools.ietf.org/html/rfc8259)

---

### 4.2 Handling None/Null in Optional Complex Fields

#### Decision
Use `Optional[ComplexType]` for nullable fields and `Field(default=None)` for optional fields. Serialize None as JSON null. Distinguish between "field absent" and "field is null" in validation.

#### Rationale
- JSON null is well-supported and semantically clear
- Pydantic handles `Optional[T]` correctly (allows None or T)
- `Field(default=None)` makes None the default when field is absent
- Explicit is better than implicit (no magic fallback values)

#### Patterns for Optional Fields
```python
from pydantic import BaseModel, Field
from typing import Optional

class AgentState(BaseModel):
    # Required complex field (must be present and non-null)
    inventory: dict[str, int]

    # Optional complex field with None default (can be absent or null)
    metadata: Optional[dict[str, str]] = None

    # Optional complex field with empty default (can be absent, but if present, must be non-null)
    tags: list[str] = Field(default_factory=list)

    # Optional complex field with explicit None (distinguishes null from absent)
    coordinates: Optional[tuple[float, float]] = Field(default=None)

# Validation behavior
AgentState(inventory={"food": 10})  # ✓ metadata=None, tags=[], coordinates=None
AgentState(inventory={"food": 10}, metadata=None)  # ✓ explicit None
AgentState(inventory={"food": 10}, metadata={"key": "value"})  # ✓
AgentState(inventory={})  # ✓ empty dict is valid
AgentState()  # ✗ ValidationError: inventory is required
```

#### JSON Serialization
```python
state = AgentState(
    inventory={"food": 10},
    metadata=None,
    tags=["active"],
    coordinates=(1.0, 2.0)
)

json_output = state.model_dump_json()
# {
#   "inventory": {"food": 10},
#   "metadata": null,
#   "tags": ["active"],
#   "coordinates": [1.0, 2.0]
# }

# Loading with missing optional fields
json_input = '{"inventory": {"food": 10}}'
loaded = AgentState.model_validate_json(json_input)
# loaded.metadata is None (default applied)
# loaded.tags is [] (default_factory applied)
# loaded.coordinates is None (default applied)
```

#### Mode Differences
```python
# mode='python' - includes None values
state.model_dump(mode='python')
# {'inventory': {...}, 'metadata': None, 'tags': [...], 'coordinates': None}

# exclude_none=True - omits None values
state.model_dump(mode='python', exclude_none=True)
# {'inventory': {...}, 'tags': [...]}  # metadata and coordinates omitted

# mode='json' - includes None as null
state.model_dump(mode='json')
# {'inventory': {...}, 'metadata': None, 'tags': [...], 'coordinates': [1.0, 2.0]}
```

#### Best Practices
1. **Use Optional[T] for nullable fields**: Clear intent that None is valid
2. **Use Field(default_factory=...) for mutable defaults**: Avoid mutable default bug
3. **Document None semantics**: Explain what None means for each field
4. **Consider exclude_none for serialization**: Reduces checkpoint file size

#### Alternatives Considered
1. **Empty collections instead of None**: Less clear; empty dict might be meaningful
2. **Sentinel values**: More complex; None is idiomatic Python
3. **Required all fields**: Too restrictive; many fields naturally optional

#### References
- [Pydantic Required Fields](https://docs.pydantic.dev/latest/concepts/models/#required-fields)
- [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/)

---

### 4.3 Preserving Immutability Constraints During Deserialization

#### Decision
Do not attempt to preserve Python-level immutability in JSON. Rely on Pydantic's type validation to restore correct types (tuple, frozenset) from JSON arrays. Document that JSON is an intermediate format, not a storage format for immutability.

#### Rationale
- JSON fundamentally does not support immutable types
- Pydantic's validation restores correct Python types based on annotations
- Attempting to encode immutability in JSON adds complexity for no real benefit
- Users who need immutability should rely on Python's type system, not JSON

#### Round-Trip Behavior
```python
from pydantic import BaseModel

class ImmutableData(BaseModel):
    # Immutable sequence (tuple)
    coords: tuple[int, int, int]

    # Mutable sequence (list)
    history: list[str]

    # Immutable set (frozenset) - NOT RECOMMENDED, see note
    # tags: frozenset[str]  # Pydantic serializes to list, not set

# Python object with immutable data
data = ImmutableData(coords=(1, 2, 3), history=["event1", "event2"])

# Serialize to JSON
json_str = data.model_dump_json()
# {"coords": [1, 2, 3], "history": ["event1", "event2"]}
# coords looks like a list in JSON

# Deserialize from JSON
data_restored = ImmutableData.model_validate_json(json_str)

# Immutability restored by Pydantic
assert isinstance(data_restored.coords, tuple)  # ✓ Immutable again
assert isinstance(data_restored.history, list)  # ✓ Mutable

# Runtime immutability enforced by Python
try:
    data_restored.coords[0] = 99  # ✗ TypeError: 'tuple' object does not support item assignment
except TypeError:
    pass  # Expected

data_restored.history[0] = "modified"  # ✓ List is mutable
```

#### Frozenset Caveat
```python
# Frozenset is NOT recommended for JSON serialization
from frozenset import frozenset

class BadExample(BaseModel):
    tags: frozenset[str]

bad = BadExample(tags=frozenset({"a", "b", "c"}))
json_str = bad.model_dump_json()
# {"tags": ["a", "b", "c"]}  # Serialized as array, loses set semantics (unique, unordered)

restored = BadExample.model_validate_json(json_str)
# restored.tags is frozenset again, but order may differ

# Recommendation: Use list with custom validator for uniqueness
from pydantic import field_validator

class BetterExample(BaseModel):
    tags: list[str]

    @field_validator('tags', mode='after')
    @classmethod
    def ensure_unique(cls, v: list[str]) -> list[str]:
        if len(v) != len(set(v)):
            raise ValueError("Tags must be unique")
        return v
```

#### Documentation for Users
```markdown
### Immutability and JSON Serialization

**Key Concept**: JSON is a data format, not a type system.

- **Tuples** serialize as arrays and deserialize as tuples (immutability restored)
- **Frozensets** serialize as arrays and deserialize as frozensets (but avoid them for JSON)
- **Nested immutable objects** work correctly if annotated properly

**Example**:
```python
class Config(BaseModel):
    # Immutable coordinate pair
    origin: tuple[int, int] = (0, 0)

    # Mutable list of moves
    moves: list[str] = Field(default_factory=list)

# JSON: {"origin": [0, 0], "moves": []}
# Python types restored correctly on load
```

**Recommendation**: Design your state variables assuming JSON serialization. If you need immutability:
1. Use `tuple` for fixed-length sequences
2. Use `list` with validators for uniqueness instead of `set`/`frozenset`
3. Document immutability in your schema, don't rely on JSON to enforce it
```

#### Alternatives Considered
1. **Custom JSON encoding for tuples**: Breaks standard JSON parsers
2. **Metadata to mark immutable fields**: Added complexity, no real benefit
3. **Forbid tuples entirely**: Too restrictive; tuples are semantically useful

#### References
- [Pydantic Serialization Docs](https://docs.pydantic.dev/latest/concepts/serialization/)

---

## 5. Performance Optimization

### 5.1 Pydantic Validation Performance with Deeply Nested Structures

#### Decision
Optimize for validation speed by using `model_validate_json()`, enabling string caching for dict-heavy models, and avoiding wrap validators. Profile validation with `pytest-benchmark` to ensure <10ms for typical state.

#### Rationale
- Pydantic 2.x's Rust core (pydantic-core) is already highly optimized
- Biggest gains come from using the right APIs, not micro-optimizations
- String caching helps with repeated dict keys (common in simulation state)
- Profiling ensures we meet performance targets objectively

#### Optimization Checklist
```python
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Annotated

class OptimizedAgentState(BaseModel):
    """Performance-optimized state model."""

    # 1. Enable string caching for dict-heavy models
    model_config = ConfigDict(
        cache_strings='keys',  # Cache dict keys to reduce allocations
    )

    # 2. Use concrete types (dict, list) instead of abstract (Mapping, Sequence)
    inventory: dict[str, int] = Field(default_factory=dict)
    history: list[str] = Field(default_factory=list)

    # 3. Use Annotated for reusable constraints
    health: Annotated[float, Field(ge=0.0, le=100.0)] = 100.0

    # 4. Prefer 'after' validators over 'wrap' (faster)
    @field_validator('health', mode='after')
    @classmethod
    def validate_health(cls, v: float) -> float:
        if v < 0:
            raise ValueError("Health cannot be negative")
        return v

    # 5. Avoid 'wrap' validators in hot paths (they materialize data in Python)
    # @field_validator('health', mode='wrap')  # DON'T DO THIS

# Usage: Always use model_validate_json for JSON input
json_data = '{"inventory": {"food": 10}, "health": 50.0}'
state = OptimizedAgentState.model_validate_json(json_data)  # Fast

# Avoid two-pass validation
import json
# slow_state = OptimizedAgentState.model_validate(json.loads(json_data))  # Slow
```

#### Performance Target Breakdown
Per spec requirements:
- **Target**: <10ms for 100 agents × 50 variables with 3 dicts, 2 lists, 1 tuple each
- **Per agent**: <100µs (10ms / 100 agents)
- **Per variable**: <2µs (100µs / 50 variables)

Estimation:
- Pydantic 2.x can validate ~10,000 simple fields/ms
- Complex types (dict, list) add ~2-5× overhead
- Nested validation adds ~1.5× overhead per level
- String caching reduces dict overhead by ~15%

Expected performance:
- Scalar field: ~0.1µs
- Dict field (10 items): ~1µs
- List field (10 items): ~0.8µs
- Nested dict (2 levels, 10 items each): ~3µs
- Full agent state (50 fields): ~50µs
- 100 agents: ~5ms

**Conclusion**: We should comfortably meet the <10ms target.

#### Profiling Setup
```python
# tests/performance/test_validation_perf.py
import pytest
from llm_sim.models.state import create_agent_state_model
from llm_sim.models.config import VariableDefinition

def test_validation_performance_typical_state(benchmark):
    """Benchmark validation of typical agent state."""
    # Define typical state schema
    var_defs = [
        VariableDefinition(name="health", var_type="float", min_value=0, max_value=100),
        VariableDefinition(name="inventory", var_type="dict", value_schema={"item": "str", "count": "int"}),
        VariableDefinition(name="history", var_type="list", item_schema={"event": "str"}),
        # ... 47 more fields
    ]

    StateModel = create_agent_state_model(var_defs)

    # Typical JSON payload
    json_data = '''
    {
        "health": 75.0,
        "inventory": {"sword": 1, "potion": 3, "gold": 150},
        "history": ["spawned", "moved", "traded"],
        ...
    }
    '''

    # Benchmark validation
    result = benchmark(StateModel.model_validate_json, json_data)

    # Assert performance target
    assert result is not None
    # pytest-benchmark will report timing; manually check < 100µs per agent

# Run with: uv run pytest tests/performance/ --benchmark-only
```

#### Alternatives Considered
1. **Custom validation logic**: Slower and more error-prone than Pydantic
2. **No validation**: Unsafe; silent corruption in production
3. **Lazy validation**: Complex; adds state tracking overhead
4. **Async validation**: Overkill; validation is CPU-bound, not I/O-bound

#### References
- [Pydantic Performance Guide](https://docs.pydantic.dev/latest/concepts/performance/)
- [pytest-benchmark Documentation](https://pytest-benchmark.readthedocs.io/)

---

### 5.2 Strategies for Caching Compiled Validators

#### Decision
Rely on Pydantic's built-in validator caching (automatic) and reuse model classes across simulation runs. Create model factories that cache generated models by schema hash.

#### Rationale
- Pydantic 2.x automatically caches compiled validators in pydantic-core
- Model class creation is expensive (~1-10ms); reuse is critical
- Schema hash ensures cache hits for identical configs across runs
- No manual cache management needed (Pydantic handles it)

#### Model Factory with Caching
```python
import hashlib
import json
from typing import Type
from functools import lru_cache
from pydantic import BaseModel, create_model

# Cache model classes by schema hash
_model_cache: dict[str, Type[BaseModel]] = {}

def schema_hash(var_defs: list[VariableDefinition]) -> str:
    """Compute stable hash of variable definitions for caching."""
    # Serialize to JSON for stable hashing
    schema_dict = [vd.model_dump(mode='json') for vd in var_defs]
    schema_json = json.dumps(schema_dict, sort_keys=True)
    return hashlib.sha256(schema_json.encode()).hexdigest()[:16]

def create_agent_state_model(var_defs: list[VariableDefinition]) -> Type[BaseModel]:
    """Create (or retrieve cached) agent state model from variable definitions.

    This function caches generated models to avoid redundant compilation.
    """
    cache_key = schema_hash(var_defs)

    # Check cache
    if cache_key in _model_cache:
        logger.debug("Using cached agent state model", cache_key=cache_key)
        return _model_cache[cache_key]

    # Generate model
    logger.debug("Generating new agent state model", cache_key=cache_key)
    fields = {}
    for vd in var_defs:
        field_type = vd.get_type_annotation()
        default = vd.get_default_value()
        fields[vd.name] = (field_type, default)

    model = create_model('AgentState', **fields)

    # Cache for future use
    _model_cache[cache_key] = model

    return model

# Usage: Model class is reused across all agents in a simulation
StateModel = create_agent_state_model(var_defs)  # Compiled once

# Create many agents with same model (fast)
agent1_state = StateModel(health=100, inventory={"food": 10})
agent2_state = StateModel(health=80, inventory={"food": 5})
# ... 1000 more agents, all using the same compiled validator
```

#### Validator Reuse Across Runs
```python
# Simulation runner
class Simulation:
    def __init__(self, config: SimulationConfig):
        self.config = config

        # Create models once during initialization
        self.agent_state_model = create_agent_state_model(config.agent_variables)
        self.global_state_model = create_global_state_model(config.global_variables)

        # Pydantic's validator cache is reused automatically

    def step(self):
        # Validation uses cached validators (fast)
        for agent in self.agents:
            # This is fast because validator is compiled and cached
            validated = self.agent_state_model.model_validate(agent.state)
```

#### Cache Statistics (Optional)
```python
def get_cache_stats() -> dict[str, int]:
    """Get statistics about model cache usage."""
    return {
        'cached_models': len(_model_cache),
        'memory_mb': sum(sys.getsizeof(m) for m in _model_cache.values()) / 1024 / 1024,
    }

# Log cache stats periodically
logger.info("Model cache stats", **get_cache_stats())
```

#### Alternatives Considered
1. **No caching**: 10-100× slower for repeated validation
2. **Manual validator compilation**: Pydantic already does this optimally
3. **Serializing compiled validators**: Complex and fragile
4. **Global model registry**: Less flexible than hash-based cache

#### Memory Considerations
- Each cached model: ~10-50KB depending on complexity
- 100 unique schemas: ~5MB memory (acceptable)
- Consider clearing cache if memory pressure is high (rare)

#### References
- [Pydantic create_model](https://docs.pydantic.dev/latest/api/main/)
- [Python functools.lru_cache](https://docs.python.org/3/library/functools.html#functools.lru_cache)

---

### 5.3 Memory Usage Patterns for Large Collections

#### Decision
Monitor memory usage with `sys.getsizeof()` and `tracemalloc`. Set hard limits on collection sizes (1000 items per spec) and log warnings when approaching limits. Use memory-efficient data structures (dict/list, not custom classes) for state storage.

#### Rationale
- Pydantic models have ~200-500 bytes overhead per instance
- Large collections (1000+ items) can consume significant memory
- Hard limits prevent runaway memory usage
- Standard Python collections are more memory-efficient than custom objects

#### Memory Estimation
```python
import sys
from pydantic import BaseModel

# Memory overhead per model instance
class SimpleAgent(BaseModel):
    health: float
    inventory: dict[str, int]

agent = SimpleAgent(health=100.0, inventory={"food": 10, "water": 5})
model_size = sys.getsizeof(agent)  # ~400-600 bytes

# Large collection estimation
num_agents = 1000
num_items_per_inventory = 100

# Memory breakdown:
# - Agent models: 1000 × 500 bytes = 500 KB
# - Inventory dicts: 1000 × (100 items × 80 bytes/item) = 8 MB
# - List overhead: ~8 KB
# Total: ~8.5 MB for 1000 agents

# This is acceptable for typical simulations
```

#### Collection Size Validation
```python
from pydantic import BaseModel, Field, field_validator
from typing import Annotated

MAX_COLLECTION_SIZE = 1000  # Per spec

class AgentState(BaseModel):
    # Enforce max collection size at validation time
    inventory: Annotated[
        dict[str, int],
        Field(max_length=MAX_COLLECTION_SIZE)
    ]

    history: Annotated[
        list[str],
        Field(max_length=MAX_COLLECTION_SIZE)
    ]

    @field_validator('inventory', mode='after')
    @classmethod
    def warn_large_inventory(cls, v: dict[str, int]) -> dict[str, int]:
        if len(v) > MAX_COLLECTION_SIZE * 0.8:  # 80% threshold
            import structlog
            logger = structlog.get_logger()
            logger.warning(
                "Inventory approaching size limit",
                current_size=len(v),
                max_size=MAX_COLLECTION_SIZE
            )
        return v

# Validation will raise error if size exceeds limit
try:
    huge_inventory = {f"item_{i}": 1 for i in range(2000)}
    state = AgentState(inventory=huge_inventory, history=[])
except ValidationError as e:
    # Error: "List should have at most 1000 items after validation"
    pass
```

#### Memory Monitoring
```python
import tracemalloc
import structlog

logger = structlog.get_logger()

def monitor_memory_usage(func):
    """Decorator to monitor memory usage of a function."""
    def wrapper(*args, **kwargs):
        tracemalloc.start()

        result = func(*args, **kwargs)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        logger.info(
            "Memory usage",
            function=func.__name__,
            current_mb=current / 1024 / 1024,
            peak_mb=peak / 1024 / 1024
        )

        return result
    return wrapper

# Usage
@monitor_memory_usage
def load_checkpoint(path: str) -> SimulationState:
    with open(path) as f:
        data = json.load(f)
    return SimulationState.model_validate_json(data)

# Logs: "Memory usage" function="load_checkpoint" current_mb=12.5 peak_mb=15.3
```

#### Memory Optimization Patterns
```python
# 1. Use generators for large iterations (avoid loading all at once)
def iter_agents(checkpoint_path: str):
    """Stream agents from checkpoint without loading all into memory."""
    with open(checkpoint_path) as f:
        data = json.load(f)
        for agent_data in data['agents']:
            yield AgentState.model_validate(agent_data)

# 2. Use __slots__ for frequently instantiated classes (reduces per-instance overhead)
class AgentState(BaseModel):
    model_config = ConfigDict(
        # Note: Pydantic doesn't use __slots__ by default for flexibility
        # Consider for performance-critical scenarios
    )

# 3. Clear unused references explicitly
def process_simulation_step(state: SimulationState):
    # Process agents
    for agent in state.agents:
        # ... do work ...
        pass

    # Clear old state to free memory
    old_state = state
    state = new_state
    del old_state  # Explicitly delete large object
```

#### Alternatives Considered
1. **No memory limits**: Risk of out-of-memory crashes
2. **Database for large collections**: Overkill for in-memory simulation
3. **Memory-mapped files**: Complex; not needed for typical scale
4. **Compressed state**: Adds CPU overhead; memory not the bottleneck

#### Performance vs Memory Tradeoff
- String caching: +15% speed, +10% memory (worthwhile)
- Model caching: +1000% speed, +1% memory (essential)
- Large collections: Linear memory growth (mitigate with hard limits)

#### References
- [Python tracemalloc Documentation](https://docs.python.org/3/library/tracemalloc.html)
- [sys.getsizeof Documentation](https://docs.python.org/3/library/sys.html#sys.getsizeof)

---

## Summary of Decisions

### Quick Reference Table

| Topic | Decision | Key References |
|-------|----------|----------------|
| Dict with dynamic keys | Use `RootModel[Dict[str, ValueType]]` or `dict[str, ValueType]` fields | [Pydantic Dicts](https://docs.pydantic.dev/latest/concepts/types/) |
| List with constraints | Use `Annotated[list[ItemType], Field(...)]` and `list[Annotated[ItemType, Field(...)]]` | [Pydantic Lists](https://docs.pydantic.dev/2.0/usage/types/list_types/) |
| Tuple with per-element types | Use `tuple[Type1, Type2, ...]` native Python syntax | [Pydantic Standard Types](https://docs.pydantic.dev/latest/api/standard_library_types/) |
| Nested/recursive objects | Use forward annotations (`'ModelName'`) and `model_rebuild()` | [Pydantic Forward Annotations](https://docs.pydantic.dev/latest/concepts/forward_annotations/) |
| Validation error paths | Use `loc` tuple, convert to dot notation with helper function | [Pydantic Error Handling](https://docs.pydantic.dev/latest/errors/errors/) |
| Circular reference detection | DFS with recursion stack for schemas; Pydantic handles data cycles | [GeeksforGeeks: Cycle Detection](https://www.geeksforgeeks.org/dsa/detect-cycle-in-a-graph/) |
| Nesting depth limits | Recursive type introspection with `get_origin()`/`get_args()` | [Python typing module](https://docs.python.org/3/library/typing.html) |
| Tuple JSON serialization | Accept tuple → array conversion; document behavior | [Pydantic Serialization](https://docs.pydantic.dev/latest/concepts/serialization/) |
| None/null handling | Use `Optional[T]` with `Field(default=None)` | [Pydantic Required Fields](https://docs.pydantic.dev/latest/concepts/models/) |
| Immutability preservation | Don't preserve in JSON; rely on type annotations for Python immutability | [Pydantic Serialization](https://docs.pydantic.dev/latest/concepts/serialization/) |
| Validation performance | Use `model_validate_json()`, enable string caching, avoid wrap validators | [Pydantic Performance](https://docs.pydantic.dev/latest/concepts/performance/) |
| Validator caching | Rely on Pydantic's automatic caching; cache model classes by schema hash | [Pydantic create_model](https://docs.pydantic.dev/latest/api/main/) |
| Memory usage | Set hard limits (1000 items), monitor with `tracemalloc`, use efficient structures | [Python tracemalloc](https://docs.python.org/3/library/tracemalloc.html) |

---

## Next Steps

With this research complete, proceed to **Phase 1: Design** to create:
1. `data-model.md` - Detailed data model definitions
2. `quickstart.md` - User-facing quickstart guide
3. `contracts/variable_definition.json` - Extended VariableDefinition JSON schema

All implementation decisions should reference this research document for rationale and best practices.

---

**Research completed**: 2025-10-13
**Reviewed by**: /speckit.plan command
**Status**: Ready for Phase 1
