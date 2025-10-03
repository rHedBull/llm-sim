"""Contract test for PauseTracker.pause() method.

Contract: contracts/pause_tracker_contract.md - pause() method
"""

import pytest
from llm_sim.infrastructure.lifecycle.pause_tracker import PauseTracker


class TestPauseTrackerPauseContract:
    """Test contract for PauseTracker.pause() method."""

    def test_pause_adds_agent_to_paused_set(self):
        """Agent should be added to paused_agents set."""
        tracker = PauseTracker()
        tracker.pause("agent1")

        assert "agent1" in tracker.paused_agents

    def test_pause_with_auto_resume_sets_metadata(self):
        """Auto-resume metadata should be set when provided."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=5)

        assert "agent1" in tracker.paused_agents
        assert tracker.auto_resume.get("agent1") == 5

    def test_pause_without_auto_resume_no_metadata(self):
        """Auto-resume metadata should not be set when None."""
        tracker = PauseTracker()
        tracker.pause("agent1", auto_resume_turns=None)

        assert "agent1" in tracker.paused_agents
        assert "agent1" not in tracker.auto_resume

    def test_pause_performs_no_validation(self):
        """pause() should not validate - assumes pre-validated by caller."""
        tracker = PauseTracker()

        # Pause same agent twice - should not raise (no validation)
        tracker.pause("agent1")
        tracker.pause("agent1", auto_resume_turns=3)  # Overwrites auto_resume

        assert "agent1" in tracker.paused_agents
        assert tracker.auto_resume.get("agent1") == 3

    def test_pause_multiple_agents(self):
        """Multiple agents can be paused independently."""
        tracker = PauseTracker()

        tracker.pause("agent1", auto_resume_turns=2)
        tracker.pause("agent2")
        tracker.pause("agent3", auto_resume_turns=5)

        assert tracker.paused_agents == {"agent1", "agent2", "agent3"}
        assert tracker.auto_resume == {"agent1": 2, "agent3": 5}
