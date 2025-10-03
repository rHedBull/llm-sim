"""Contract test for PauseTracker.tick_auto_resume() method.

Contract: contracts/pause_tracker_contract.md - tick_auto_resume() method
"""

import pytest
from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker


class TestPauseTrackerTickAutoResumeContract:
    """Test contract for PauseTracker.tick_auto_resume() method."""

    def test_tick_decrements_counters(self):
        """Should decrement all auto_resume counters by 1."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=3)
        tracker.pause("agent2", auto_resume_turns=2)

        tracker.tick_auto_resume()

        assert tracker.auto_resume == {"agent1": 2, "agent2": 1}

    def test_tick_resumes_at_zero(self):
        """Should auto-resume agents when counter reaches 0."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=1)

        resumed = tracker.tick_auto_resume()

        assert "agent1" in resumed
        assert "agent1" not in tracker.paused_agents
        assert "agent1" not in tracker.auto_resume

    def test_tick_returns_resumed_list(self):
        """Should return list of agent names that were auto-resumed."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=1)
        tracker.pause("agent2", auto_resume_turns=1)
        tracker.pause("agent3", auto_resume_turns=2)

        resumed = tracker.tick_auto_resume()

        assert set(resumed) == {"agent1", "agent2"}
        assert "agent3" in tracker.paused_agents
        assert tracker.auto_resume == {"agent3": 1}

    def test_tick_with_no_auto_resume(self):
        """Should return empty list when no auto_resume configured."""
        tracker = PauseTracker()
        tracker.pause("agent1")  # No auto_resume

        resumed = tracker.tick_auto_resume()

        assert resumed == []
        assert "agent1" in tracker.paused_agents

    def test_tick_multiple_times(self):
        """Should handle multiple ticks correctly."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=3)

        # Tick 1: 3 -> 2
        resumed = tracker.tick_auto_resume()
        assert resumed == []
        assert tracker.auto_resume["agent1"] == 2

        # Tick 2: 2 -> 1
        resumed = tracker.tick_auto_resume()
        assert resumed == []
        assert tracker.auto_resume["agent1"] == 1

        # Tick 3: 1 -> 0 (resume)
        resumed = tracker.tick_auto_resume()
        assert resumed == ["agent1"]
        assert "agent1" not in tracker.paused_agents
        assert "agent1" not in tracker.auto_resume

    def test_tick_empty_tracker(self):
        """Should handle empty tracker without errors."""
        tracker = PauseTracker()

        resumed = tracker.tick_auto_resume()

        assert resumed == []

    def test_tick_only_affects_auto_resume_agents(self):
        """Should only affect agents with auto_resume, not indefinite pauses."""
        tracker = PauseTracker()
        tracker.pause("agent1")  # Indefinite
        tracker.pause("agent2", auto_resume_turns=1)

        resumed = tracker.tick_auto_resume()

        assert resumed == ["agent2"]
        assert "agent1" in tracker.paused_agents  # Still paused
        assert "agent2" not in tracker.paused_agents
