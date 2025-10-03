"""Contract test for PauseTracker.resume() method.

Contract: contracts/pause_tracker_contract.md - resume() method
"""

import pytest
from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker


class TestPauseTrackerResumeContract:
    """Test contract for PauseTracker.resume() method."""

    def test_resume_returns_true_when_paused(self):
        """Should return True when agent was paused."""
        tracker = PauseTracker()
        tracker.pause("agent1")

        result = tracker.resume("agent1")

        assert result is True

    def test_resume_returns_false_when_not_paused(self):
        """Should return False when agent was not paused."""
        tracker = PauseTracker()

        result = tracker.resume("agent1")

        assert result is False

    def test_resume_removes_from_paused_set(self):
        """Agent should be removed from paused_agents set."""
        tracker = PauseTracker()
        tracker.pause("agent1")

        tracker.resume("agent1")

        assert "agent1" not in tracker.paused_agents

    def test_resume_removes_from_auto_resume_dict(self):
        """Agent should be removed from auto_resume dict if present."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=3)

        tracker.resume("agent1")

        assert "agent1" not in tracker.paused_agents
        assert "agent1" not in tracker.auto_resume

    def test_resume_only_affects_target_agent(self):
        """Resuming one agent should not affect others."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=2)
        tracker.pause("agent2", auto_resume_turns=5)

        tracker.resume("agent1")

        assert "agent1" not in tracker.paused_agents
        assert "agent2" in tracker.paused_agents
        assert tracker.auto_resume == {"agent2": 5}

    def test_resume_without_auto_resume(self):
        """Should work for agents paused without auto_resume."""
        tracker = PauseTracker()
        tracker.pause("agent1")  # No auto_resume

        result = tracker.resume("agent1")

        assert result is True
        assert "agent1" not in tracker.paused_agents
        assert "agent1" not in tracker.auto_resume
