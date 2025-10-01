"""Component discovery mechanism for loading implementations dynamically.

This module provides the ComponentDiscovery class which scans the filesystem
to dynamically load concrete implementations of agents, engines, and validators.
"""

import importlib.util
from pathlib import Path
from typing import Type, List, Dict
from types import ModuleType

from llm_sim.infrastructure.base.agent import BaseAgent
from llm_sim.infrastructure.base.engine import BaseEngine
from llm_sim.infrastructure.base.validator import BaseValidator


class ComponentDiscovery:
    """Dynamically discover and load concrete implementations by filename.
    
    This class implements a convention-based discovery system where:
    - Filename: snake_case.py (e.g., "econ_llm_agent.py")
    - Class name: PascalCase (e.g., "EconLlmAgent")
    - File location: implementations/{agents,engines,validators}/
    
    All loaded classes are cached for performance.
    """

    def __init__(self, implementations_root: Path):
        """Initialize discovery service.
        
        Args:
            implementations_root: Root directory containing implementations/ subdirectory
        """
        self.implementations_root = Path(implementations_root)
        self._cache: Dict[str, Type] = {}

    def _filename_to_classname(self, filename: str) -> str:
        """Convert snake_case filename to PascalCase class name.

        Args:
            filename: Snake case filename (without .py extension)

        Returns:
            PascalCase class name

        Examples:
            >>> _filename_to_classname("econ_llm_agent")
            "EconLLMAgent"
            >>> _filename_to_classname("nation")
            "Nation"
        """
        # Special handling for common acronyms
        parts = []
        for word in filename.split('_'):
            if word.upper() == 'LLM':
                parts.append('LLM')
            else:
                parts.append(word.capitalize())
        return ''.join(parts)

    def _load_module(self, component_type: str, filename: str) -> ModuleType:
        """Dynamically import module from filesystem.
        
        Args:
            component_type: One of "agents", "engines", "validators"
            filename: Filename without extension
            
        Returns:
            Loaded Python module
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        module_path = (
            self.implementations_root
            / "implementations"
            / component_type
            / f"{filename}.py"
        )
        
        if not module_path.exists():
            available = self._list_component_type(component_type)
            raise FileNotFoundError(
                f"No implementation found for '{component_type}' with filename '{filename}'\n"
                f"Expected file: {module_path}\n"
                f"Available {component_type}: {', '.join(available)}"
            )
        
        # Load module dynamically
        spec = importlib.util.spec_from_file_location(
            f"llm_sim.implementations.{component_type}.{filename}",
            module_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        return module

    def _validate_inheritance(self, cls: Type, base_class: Type) -> None:
        """Verify class inherits from expected base.
        
        Args:
            cls: Loaded class to validate
            base_class: Expected base class
            
        Raises:
            TypeError: If inheritance check fails
        """
        if not issubclass(cls, base_class):
            actual_bases = ', '.join(b.__name__ for b in cls.__bases__)
            raise TypeError(
                f"Class '{cls.__name__}' does not inherit from {base_class.__name__}\n"
                f"Expected: class {cls.__name__}({base_class.__name__})\n"
                f"Found: class {cls.__name__}({actual_bases})"
            )

    def _list_component_type(self, component_type: str) -> List[str]:
        """List all available implementations for a component type.
        
        Args:
            component_type: One of "agents", "engines", "validators"
            
        Returns:
            List of available filenames (without .py extension)
        """
        component_dir = self.implementations_root / "implementations" / component_type
        
        if not component_dir.exists():
            return []
        
        files = []
        for py_file in component_dir.glob("*.py"):
            # Exclude __init__.py and private files (starting with _)
            if py_file.stem.startswith("_"):
                continue
            files.append(py_file.stem)
        
        return sorted(files)

    def load_agent(self, filename: str) -> Type[BaseAgent]:
        """Load agent implementation by filename.

        Args:
            filename: Python filename without .py extension (e.g., "econ_llm_agent")

        Returns:
            Agent class (not instance) that inherits from BaseAgent

        Raises:
            FileNotFoundError: If filename.py doesn't exist
            TypeError: If loaded class doesn't inherit from BaseAgent
            AttributeError: If expected class name not found in module

        Example:
            >>> discovery = ComponentDiscovery(Path("src/llm_sim"))
            >>> AgentClass = discovery.load_agent("econ_llm_agent")
            >>> agent = AgentClass(name="TestAgent", ...)
        """
        cache_key = f"agent:{filename}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Load module
        module = self._load_module("agents", filename)

        # Get expected class name - add "Agent" suffix if not present
        base_name = self._filename_to_classname(filename)
        expected_class_name = base_name if base_name.endswith("Agent") else f"{base_name}Agent"

        # Extract class from module
        if not hasattr(module, expected_class_name):
            available_classes = [
                name for name in dir(module)
                if not name.startswith('_') and isinstance(getattr(module, name), type)
            ]
            raise AttributeError(
                f"Module '{filename}' does not contain expected class '{expected_class_name}'\n"
                f"Available classes in module: {', '.join(available_classes)}\n"
                f"Hint: Filename 'nation.py' should contain class 'NationAgent'"
            )

        cls = getattr(module, expected_class_name)

        # Validate inheritance
        self._validate_inheritance(cls, BaseAgent)

        # Cache and return
        self._cache[cache_key] = cls
        return cls

    def load_engine(self, filename: str) -> Type[BaseEngine]:
        """Load engine implementation by filename.

        Args:
            filename: Python filename without .py extension

        Returns:
            Engine class that inherits from BaseEngine

        Raises:
            Same as load_agent but validates BaseEngine inheritance
        """
        cache_key = f"engine:{filename}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        module = self._load_module("engines", filename)

        # Get expected class name - add "Engine" suffix if not present
        base_name = self._filename_to_classname(filename)
        expected_class_name = base_name if base_name.endswith("Engine") else f"{base_name}Engine"

        if not hasattr(module, expected_class_name):
            available_classes = [
                name for name in dir(module)
                if not name.startswith('_') and isinstance(getattr(module, name), type)
            ]
            raise AttributeError(
                f"Module '{filename}' does not contain expected class '{expected_class_name}'\n"
                f"Available classes in module: {', '.join(available_classes)}\n"
                f"Hint: Filename 'economic.py' should contain class 'EconomicEngine'"
            )

        cls = getattr(module, expected_class_name)
        self._validate_inheritance(cls, BaseEngine)

        self._cache[cache_key] = cls
        return cls

    def load_validator(self, filename: str) -> Type[BaseValidator]:
        """Load validator implementation by filename.

        Args:
            filename: Python filename without .py extension

        Returns:
            Validator class that inherits from BaseValidator

        Raises:
            Same as load_agent but validates BaseValidator inheritance
        """
        cache_key = f"validator:{filename}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        module = self._load_module("validators", filename)

        # Get expected class name - add "Validator" suffix if not present
        base_name = self._filename_to_classname(filename)
        expected_class_name = base_name if base_name.endswith("Validator") else f"{base_name}Validator"

        if not hasattr(module, expected_class_name):
            available_classes = [
                name for name in dir(module)
                if not name.startswith('_') and isinstance(getattr(module, name), type)
            ]
            raise AttributeError(
                f"Module '{filename}' does not contain expected class '{expected_class_name}'\n"
                f"Available classes in module: {', '.join(available_classes)}\n"
                f"Hint: Filename 'always_valid.py' should contain class 'AlwaysValidValidator'"
            )

        cls = getattr(module, expected_class_name)
        self._validate_inheritance(cls, BaseValidator)

        self._cache[cache_key] = cls
        return cls

    def list_agents(self) -> List[str]:
        """List all available agent implementations.
        
        Returns:
            Sorted list of filenames (without .py extension)
        """
        return self._list_component_type("agents")

    def list_engines(self) -> List[str]:
        """List all available engine implementations.
        
        Returns:
            Sorted list of filenames (without .py extension)
        """
        return self._list_component_type("engines")

    def list_validators(self) -> List[str]:
        """List all available validator implementations.
        
        Returns:
            Sorted list of filenames (without .py extension)
        """
        return self._list_component_type("validators")
