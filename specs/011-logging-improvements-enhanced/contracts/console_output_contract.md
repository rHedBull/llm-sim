# Contract: Console Output Format

**Feature**: 011-logging-improvements-enhanced
**Contract ID**: LC-003
**Date**: 2025-10-06

## Purpose

Define the contract for console output formatting including colors, alignment, and readability.

## Output Format Specification

### General Format

```
[timestamp] [level     ] [event_name padded to 35 chars] [key1=value1] [key2=value2] ...
```

### Example Output

```
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-20251006 simulation=economic agents=5
2025-10-06 09:08:33 [info     ] turn_started                     run_id=demo-20251006 turn=1 active=5 paused=0
2025-10-06 09:08:34 [warning  ] slow_operation                   run_id=demo-20251006 duration_ms=1234.5
2025-10-06 09:08:35 [error    ] validation_failed                run_id=demo-20251006 agent_id=alpha reason=invalid
```

## Behavioral Contract

### Timestamp Format

**MUST display timestamp in readable format**:
```
Format: YYYY-MM-DD HH:MM:SS
Example: 2025-10-06 09:08:33
```

**MUST use local timezone** (not UTC):
```python
# Console output shows local time
# JSON output can use ISO 8601 UTC
```

### Log Level Display

**MUST display level in brackets with padding**:
```
[info     ]  # 'info' padded to 9 chars
[warning  ]  # 'warning' padded to 9 chars
[error    ]  # 'error' padded to 9 chars
[debug    ]  # 'debug' padded to 9 chars
```

**MUST align level column**:
```
All level brackets start at same column position
```

### Event Name Alignment

**MUST pad event names to 35 characters**:
```
simulation_starting              # Padded with spaces to 35 chars
turn_started                     # Padded with spaces to 35 chars
agent_decision_completed         # Padded with spaces to 35 chars
```

**MUST truncate event names longer than 35 characters**:
```
very_long_event_name_that_exceeds_limit  # Truncated to 35 chars
```

### Key-Value Pair Display

**MUST display context and event data as key=value**:
```
run_id=demo-123 simulation=economic turn=5
```

**MUST NOT quote string values** (for readability):
```
# Good
agent_id=alice simulation=economic

# Bad (too verbose)
agent_id="alice" simulation="economic"
```

**MUST handle special characters in values**:
```
# Spaces in values - use quotes if needed
reason="invalid action type"

# Numbers - no quotes
turn=5 duration_ms=123.45

# Booleans - lowercase
enabled=true paused=false
```

### Color Coding

**MUST use colors for log levels**:
```
ERROR   → Red
WARNING → Yellow
INFO    → Cyan
DEBUG   → Gray
```

**MUST disable colors when not TTY**:
```python
# If sys.stdout.isatty() == False:
#   Disable colors (e.g., when piped to file)
```

**MUST handle ANSI color codes**:
```
Red:    \033[91m...\033[0m
Yellow: \033[93m...\033[0m
Cyan:   \033[96m...\033[0m
Gray:   \033[90m...\033[0m
```

### Component/Module Display

**MUST include logger name in output**:
```
[llm_sim.orchestrator] simulation_starting
[llm_sim.infrastructure.events] event_written
[llm_sim.infrastructure.patterns] agent_decision_started
```

**OR** include as context field:
```
logger=llm_sim.orchestrator simulation_starting run_id=demo-123
```

## Format Examples

### Basic Event

```
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-20251006-090833 simulation=economic
```

**Assertions**:
- Timestamp present and formatted ✅
- Level padded and aligned ✅
- Event name padded to 35 chars ✅
- Context displayed as key=value ✅

### Event with Agent Context

```
2025-10-06 09:08:34 [info     ] agent_decision_started           run_id=demo-20251006 agent_id=alice turn=5
```

**Assertions**:
- Agent context (agent_id) included ✅
- Turn context included ✅
- Formatting consistent ✅

### Warning Event

```
2025-10-06 09:08:35 [warning  ] slow_operation                   run_id=demo-20251006 duration_ms=1543.2
```

**Assertions**:
- Warning level displayed ✅
- Color: Yellow (if TTY) ✅
- Numeric value formatted correctly ✅

### Error Event

```
2025-10-06 09:08:36 [error    ] validation_failed                run_id=demo-20251006 agent_id=alice reason=invalid_action
```

**Assertions**:
- Error level displayed ✅
- Color: Red (if TTY) ✅
- Error details in context ✅

### Multi-Line Exception

```
2025-10-06 09:08:37 [error    ] simulation_crashed               run_id=demo-20251006 simulation=economic
Traceback (most recent call last):
  File "orchestrator.py", line 123, in run
    state = self.engine.run_turn(actions)
ValueError: Invalid state transition
```

**Assertions**:
- Exception info follows log line ✅
- Traceback preserved ✅
- Readable formatting ✅

## Non-TTY Behavior

### When Output is Redirected

```bash
python simulate.py > output.log
```

**MUST disable colors**:
```
# No ANSI escape codes in file
2025-10-06 09:08:33 [info     ] simulation_starting              run_id=demo-123
```

**MUST maintain formatting**:
```
# Padding and alignment still work
# Just no color codes
```

### Detection Method

```python
import sys

if sys.stdout.isatty():
    # Enable colors
    use_colors = True
else:
    # Disable colors (piped or redirected)
    use_colors = False
```

## Configuration

**MUST respect format parameter**:
```python
configure_logging(format="console")  # Use console formatting
configure_logging(format="json")     # Use JSON formatting (no console)
```

**MUST allow customizing event padding**:
```python
# Default: 35 characters
ConsoleRenderer(pad_event=35)

# Custom: 50 characters
ConsoleRenderer(pad_event=50)
```

## Test Scenarios

### Scenario 1: Basic Console Format

```python
def test_basic_console_format():
    """Test basic console output format."""
    configure_logging(format="console")
    logger = get_logger(__name__)

    with capture_stdout() as output:
        logger.info("test_event", key="value")

    # Parse output line
    line = output.getvalue().strip()

    # Must contain timestamp
    assert re.match(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", line)

    # Must contain level in brackets
    assert "[info     ]" in line

    # Must contain event name
    assert "test_event" in line

    # Must contain key=value
    assert "key=value" in line
```

### Scenario 2: Event Name Padding

```python
def test_event_name_padding():
    """Test that event names are padded to 35 characters."""
    configure_logging(format="console")
    logger = get_logger(__name__)

    with capture_stdout() as output:
        logger.info("short")

    line = output.getvalue()

    # Extract event name portion
    # Should be padded to 35 chars before first key=value or end of line
    event_section = line.split("]")[2]  # After [info     ]
    event_name = event_section.split()[0]

    # Verify padding (event + spaces = 35)
    # Or verify consistent column alignment across multiple events
```

### Scenario 3: Color Coding (TTY)

```python
def test_color_coding_tty(monkeypatch):
    """Test color coding when output is TTY."""
    # Mock sys.stdout.isatty() to return True
    monkeypatch.setattr("sys.stdout.isatty", lambda: True)

    configure_logging(format="console")
    logger = get_logger(__name__)

    with capture_stdout() as output:
        logger.error("error_event")
        logger.warning("warning_event")
        logger.info("info_event")

    lines = output.getvalue().split("\n")

    # Error should have red color code
    assert "\033[91m" in lines[0] or "error" in lines[0].lower()

    # Warning should have yellow color code
    assert "\033[93m" in lines[1] or "warning" in lines[1].lower()

    # Info should have cyan color code
    assert "\033[96m" in lines[2] or "info" in lines[2].lower()
```

### Scenario 4: No Colors (Non-TTY)

```python
def test_no_colors_non_tty(monkeypatch):
    """Test that colors are disabled when not TTY."""
    # Mock sys.stdout.isatty() to return False
    monkeypatch.setattr("sys.stdout.isatty", lambda: False)

    configure_logging(format="console")
    logger = get_logger(__name__)

    with capture_stdout() as output:
        logger.error("error_event")

    line = output.getvalue()

    # Should NOT contain ANSI color codes
    assert "\033[" not in line
```

### Scenario 5: Context Display

```python
def test_context_display():
    """Test that bound context and event data are displayed."""
    configure_logging(format="console")
    logger = get_logger(__name__).bind(run_id="test-123", simulation="demo")

    with capture_stdout() as output:
        logger.info("event", turn=5, agent="alice")

    line = output.getvalue()

    # Must contain bound context
    assert "run_id=test-123" in line
    assert "simulation=demo" in line

    # Must contain event data
    assert "turn=5" in line
    assert "agent=alice" in line
```

### Scenario 6: Exception Formatting

```python
def test_exception_formatting():
    """Test that exceptions are formatted readably."""
    configure_logging(format="console")
    logger = get_logger(__name__)

    try:
        raise ValueError("Test error")
    except ValueError:
        with capture_stdout() as output:
            logger.error("error_occurred", exc_info=True)

    output_str = output.getvalue()

    # Must contain traceback
    assert "Traceback" in output_str
    assert "ValueError: Test error" in output_str
```

## Contract Tests Location

**File**: `tests/contract/test_console_output_format.py`

**Test Function Names**:
- `test_basic_console_format()`
- `test_event_name_padding()`
- `test_color_coding_tty()`
- `test_no_colors_non_tty()`
- `test_context_display()`
- `test_exception_formatting()`
- `test_log_level_alignment()`
- `test_timestamp_format()`

## Success Criteria

✅ Console output is readable and well-formatted
✅ Event names are aligned consistently
✅ Colors work in TTY, disabled in non-TTY
✅ Context and event data are clearly displayed
✅ Log levels are color-coded and aligned
✅ Timestamps are human-readable

---

*Contract LC-003 - Ready for contract test implementation*
