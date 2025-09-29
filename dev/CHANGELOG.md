# Changelog

All notable changes to the LLM Geopolitical Simulation project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Three-Layer State Architecture** - Complete implementation of sophisticated state management system
  - Global State Layer for world-wide conditions (read-only for agents)
  - Agent Game Values Layer for nation statistics (read-only for agents)
  - Agent Memory Layer for learning and strategy (read/write for owning agent)
- **Access Control System** - Enforced permission matrix preventing unauthorized state modifications
- **Audit Logging System** - Comprehensive tracking of all state access with violation detection
- **State Migration Tools** - Utilities for migrating legacy state formats to three-layer architecture
- **Performance Benchmarks** - Comprehensive performance testing suite
- **E2E Test Suite** - Full end-to-end testing of three-layer simulation
- **CLI Commands** for state management:
  - `audit` - Generate audit reports and view violations
  - `migrate` - Migrate legacy states to new format
- **Configuration Templates** - YAML templates for three-layer state configuration
- **Enhanced Documentation**:
  - Complete three-layer state architecture guide
  - System architecture documentation
  - Migration guide from legacy formats

### Changed
- **BasicDiplomaticAgent** - Updated to support three-layer state architecture with backward compatibility
- **State Management** - Refactored to use immutable state objects with copy-on-write semantics
- **Test Suite** - Expanded from 122 to 314+ tests with full coverage of new features

### Fixed
- State persistence now uses efficient in-memory snapshots
- Memory management with automatic garbage collection
- Access control violations properly tracked and reported

## [0.2.0] - Previous Release

### Added
- Basic diplomatic agent implementation
- Simple state management system
- Action validation framework
- CLI interface for running simulations

### Changed
- Improved LLM integration with Ollama
- Enhanced output formatting options

### Fixed
- Various bug fixes in state transitions
- Memory leaks in long-running simulations

## [0.1.0] - Initial Release

### Added
- Core simulation engine
- Basic agent framework
- State representation models
- Configuration system
- Test infrastructure

---

## Migration Guide

### Migrating from v0.2.0 to Three-Layer Architecture

1. **Update Configuration Files**
   - Use new configuration templates in `config/templates/`
   - Add three-layer state configuration

2. **Migrate State Files**
   ```bash
   # Analyze existing states
   uv run llm-sim migrate analyze --path old_states/

   # Perform migration
   uv run llm-sim migrate run --input old_states/ --output new_states/
   ```

3. **Update Custom Agents**
   - Implement `process_turn()` method for three-layer support
   - Use filtered state views instead of direct state access
   - Update memory operations to use AgentMemory API

4. **Enable Audit Logging**
   - Configure audit settings in state configuration
   - Use `audit` command to monitor access patterns

For detailed migration instructions, see [Migration Guide](../docs/three_layer_state.md#migration-from-legacy-state).