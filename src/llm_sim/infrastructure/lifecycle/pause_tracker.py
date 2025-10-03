"""Pause tracking for agent lifecycle management."""

from typing import Any, Dict, List, Optional, Set


class PauseTracker:
    """Track paused agent state and auto-resume metadata."""

    def __init__(self) -> None:
        """Initialize pause tracker."""
        self.paused_agents: Set[str] = set()
        self.auto_resume: Dict[str, int] = {}

    def pause(self, agent_name: str, auto_resume_turns: Optional[int] = None) -> None:
        """Pause an agent with optional auto-resume.

        Args:
            agent_name: Name of agent to pause
            auto_resume_turns: Optional number of turns until auto-resume

        Note:
            No validation performed - assumes pre-validated by caller.
            If agent already paused, overwrites auto_resume value if provided.
        """
        self.paused_agents.add(agent_name)

        if auto_resume_turns is not None:
            self.auto_resume[agent_name] = auto_resume_turns
        elif agent_name in self.auto_resume:
            # If no auto_resume provided but agent has one, keep existing
            pass

    def resume(self, agent_name: str) -> bool:
        """Resume an agent if paused.

        Args:
            agent_name: Name of agent to resume

        Returns:
            True if agent was paused and resumed, False if not paused
        """
        if agent_name not in self.paused_agents:
            return False

        self.paused_agents.discard(agent_name)
        self.auto_resume.pop(agent_name, None)
        return True

    def is_paused(self, agent_name: str) -> bool:
        """Check if agent is paused.

        Args:
            agent_name: Name of agent to check

        Returns:
            True if agent is paused, False otherwise
        """
        return agent_name in self.paused_agents

    def tick_auto_resume(self) -> List[str]:
        """Process auto-resume for one turn.

        Decrements all auto_resume counters by 1 and resumes agents
        when counter reaches 0.

        Returns:
            List of agent names that were auto-resumed this tick
        """
        resumed: List[str] = []

        # Need to iterate over a copy since we're modifying the dict
        for agent_name, turns_remaining in list(self.auto_resume.items()):
            turns_remaining -= 1

            if turns_remaining <= 0:
                # Auto-resume
                self.paused_agents.discard(agent_name)
                del self.auto_resume[agent_name]
                resumed.append(agent_name)
            else:
                # Update counter
                self.auto_resume[agent_name] = turns_remaining

        return resumed

    def get_paused_count(self) -> int:
        """Get count of paused agents.

        Returns:
            Number of currently paused agents
        """
        return len(self.paused_agents)

    def clear(self) -> None:
        """Clear all pause tracking state.

        Use case: Reset tracker for new simulation run
        """
        self.paused_agents.clear()
        self.auto_resume.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize pause tracker state.

        Returns:
            Dict containing paused_agents and auto_resume state
        """
        return {
            "paused_agents": sorted(list(self.paused_agents)),  # Sorted for determinism
            "auto_resume": self.auto_resume.copy(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PauseTracker":
        """Deserialize pause tracker state.

        Args:
            data: Dict containing paused_agents and auto_resume state

        Returns:
            PauseTracker instance with restored state

        Raises:
            ValueError: If auto_resume keys not in paused_agents
        """
        tracker = cls()
        tracker.paused_agents = set(data.get("paused_agents", []))
        tracker.auto_resume = data.get("auto_resume", {}).copy()

        # Validate invariants
        auto_resume_keys = set(tracker.auto_resume.keys())
        if not auto_resume_keys.issubset(tracker.paused_agents):
            invalid = auto_resume_keys - tracker.paused_agents
            raise ValueError(f"auto_resume keys not in paused_agents: {invalid}")

        return tracker
