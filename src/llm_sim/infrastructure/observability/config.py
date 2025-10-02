"""Configuration models for partial observability feature."""

from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, field_validator, model_validator


class ObservabilityLevel(str, Enum):
    """Define the three levels of observability."""

    UNAWARE = "unaware"
    EXTERNAL = "external"
    INSIDER = "insider"


class VariableVisibilityConfig(BaseModel):
    """Classify state variables as external (public) or internal (private)."""

    external: List[str]
    internal: List[str]

    @model_validator(mode="after")
    def validate_no_overlap(self) -> "VariableVisibilityConfig":
        """Validate no overlap between external and internal lists."""
        external_set = set(self.external)
        internal_set = set(self.internal)
        overlap = external_set & internal_set

        if overlap:
            overlap_str = ", ".join(sorted(overlap))
            raise ValueError(
                f"Variables cannot be both external and internal: {overlap_str}. "
                f"Remediation: Each variable must be classified as either external (visible to EXTERNAL observers) "
                f"or internal (visible only to INSIDER observers), but not both. "
                f"Remove the overlapping variables from one of the lists."
            )

        return self


class ObservabilityEntry(BaseModel):
    """Define observability relationship between one observer and one target."""

    observer: str
    target: str
    level: ObservabilityLevel
    noise: Optional[float]

    @field_validator("noise")
    @classmethod
    def validate_noise(cls, v: Optional[float]) -> Optional[float]:
        """Validate noise >= 0.0 if not None."""
        if v is not None and v < 0.0:
            raise ValueError(
                f"Noise must be >= 0.0, got {v}. "
                f"Remediation: Noise represents the percentage of random variation (e.g., 0.2 = 20% variation). "
                f"Use None for UNAWARE level, or a non-negative value for EXTERNAL/INSIDER levels."
            )
        return v


class DefaultObservability(BaseModel):
    """Fallback observability for observer-target pairs not in matrix."""

    level: ObservabilityLevel
    noise: float

    @field_validator("noise")
    @classmethod
    def validate_noise(cls, v: float) -> float:
        """Validate noise >= 0.0."""
        if v < 0.0:
            raise ValueError(
                f"Default noise must be >= 0.0, got {v}. "
                f"Remediation: Default noise is applied to all observer-target pairs not explicitly listed in the matrix. "
                f"Use a non-negative value (e.g., 0.0 for no noise, 0.2 for 20% variation)."
            )
        return v


class ObservabilityConfig(BaseModel):
    """Complete observability configuration for simulation."""

    enabled: bool
    variable_visibility: VariableVisibilityConfig
    matrix: List[ObservabilityEntry]
    default: Optional[DefaultObservability] = None

    @field_validator("matrix", mode="before")
    @classmethod
    def parse_matrix_entries(cls, v: Any) -> Any:
        """Parse matrix entries from list format to ObservabilityEntry objects."""
        if not isinstance(v, list):
            return v

        parsed_entries: List[ObservabilityEntry] = []
        for idx, item in enumerate(v):
            if isinstance(item, list):
                # Parse from [observer, target, level, noise] format
                if len(item) != 4:
                    raise ValueError(
                        f"Matrix entry at index {idx} must have exactly 4 elements [observer, target, level, noise], "
                        f"got {len(item)} elements: {item}. "
                        f"Remediation: Each matrix entry should be formatted as "
                        f"['ObserverName', 'TargetName', 'level', noise_value]. "
                        f"Valid levels: 'unaware', 'external', 'insider'. "
                        f"Noise should be None (for unaware) or a number >= 0.0."
                    )
                parsed_entries.append(
                    ObservabilityEntry(
                        observer=item[0],
                        target=item[1],
                        level=item[2],
                        noise=item[3],
                    )
                )
            else:
                # Already an ObservabilityEntry or dict
                parsed_entries.append(item)

        return parsed_entries

    @model_validator(mode="after")
    def validate_observability_config(self) -> "ObservabilityConfig":
        """Cross-validate against agent names and variable names."""
        # ValidationInfo context is not available in model_validator mode="after"
        # Cross-validation will be done at SimulationConfig level
        # This method performs internal consistency checks

        # Check for duplicate (observer, target) pairs in matrix
        seen_pairs = set()
        for entry in self.matrix:
            pair = (entry.observer, entry.target)
            if pair in seen_pairs:
                raise ValueError(
                    f"Duplicate observability entry for observer '{entry.observer}' "
                    f"and target '{entry.target}'. "
                    f"Remediation: Each observer-target pair can only appear once in the matrix. "
                    f"Remove the duplicate entry or consolidate the observability settings."
                )
            seen_pairs.add(pair)

        return self
