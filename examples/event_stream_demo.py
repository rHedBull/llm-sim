#!/usr/bin/env python3
"""Demonstration of the event streaming feature.

This script shows how to:
1. Run a simulation with event streaming enabled
2. Query events via the EventService
3. Filter events by various criteria
4. Analyze causality chains
"""

import asyncio
import json
from pathlib import Path

from llm_sim.infrastructure.events import (
    EventWriter,
    VerbosityLevel,
    create_milestone_event,
    create_decision_event,
    create_action_event,
    create_state_event,
)
from llm_sim.api.services.event_service import EventService
from llm_sim.models.event_filter import EventFilter


async def demo_event_writer():
    """Demonstrate EventWriter functionality."""
    print("=" * 60)
    print("DEMO 1: Event Writer")
    print("=" * 60)

    # Create event writer
    output_dir = Path("output/demo-simulation")
    output_dir.mkdir(parents=True, exist_ok=True)

    writer = EventWriter(
        output_dir=output_dir,
        simulation_id="demo-simulation",
        verbosity=VerbosityLevel.ACTION
    )

    # Start writer
    await writer.start()

    # Emit various events
    events = [
        create_milestone_event(
            simulation_id="demo-simulation",
            turn_number=0,
            milestone_type="simulation_start",
            description="Demo simulation started"
        ),
        create_milestone_event(
            simulation_id="demo-simulation",
            turn_number=1,
            milestone_type="turn_start",
            description="Turn 1 started"
        ),
        create_decision_event(
            simulation_id="demo-simulation",
            turn_number=1,
            agent_id="agent_alpha",
            decision_type="investment",
            old_value=0,
            new_value=100,
            description="Agent alpha decided to invest 100 units"
        ),
        create_action_event(
            simulation_id="demo-simulation",
            turn_number=1,
            agent_id="agent_alpha",
            action_type="trade",
            action_payload={"partner": "agent_beta", "amount": 50},
            description="Agent alpha traded with beta"
        ),
        create_state_event(
            simulation_id="demo-simulation",
            turn_number=1,
            variable_name="wealth",
            old_value=1000,
            new_value=1050,
            agent_id="agent_alpha",
            scope="agent",
            description="Agent alpha wealth increased"
        ),
        create_milestone_event(
            simulation_id="demo-simulation",
            turn_number=1,
            milestone_type="turn_end",
            description="Turn 1 completed"
        ),
        create_milestone_event(
            simulation_id="demo-simulation",
            turn_number=1,
            milestone_type="simulation_end",
            description="Demo simulation completed"
        ),
    ]

    for event in events:
        writer.emit(event)
        print(f"✅ Emitted: {event.event_type:10} - {event.description}")

    # Give writer time to process events
    await asyncio.sleep(0.5)

    # Stop writer and flush
    await writer.stop(timeout=5.0)

    # Show file contents
    event_file = output_dir / "events.jsonl"
    if event_file.exists():
        with open(event_file) as f:
            count = sum(1 for _ in f)
        print(f"\n✅ Written {count} events to {event_file}")
    else:
        print(f"\n❌ No events file created")

    print()


def demo_event_service():
    """Demonstrate EventService functionality."""
    print("=" * 60)
    print("DEMO 2: Event Service & Filtering")
    print("=" * 60)

    service = EventService(Path("output"))

    # List all simulations
    simulations = service.list_simulations()
    print(f"\n📊 Found {len(simulations)} simulations:")
    for sim in simulations:
        print(f"   - {sim['id']}: {sim['event_count']} events")

    # Get all events
    filter_all = EventFilter(limit=100, offset=0)
    result = service.get_filtered_events("demo-simulation", filter_all)
    print(f"\n📋 All events: {result['total']} total")
    for event in result['events']:
        print(f"   - Turn {event['turn_number']}: {event['event_type']:10} - {event['description']}")

    # Filter by event type (MILESTONE only)
    filter_milestone = EventFilter(event_types=["MILESTONE"], limit=100)
    result_milestone = service.get_filtered_events("demo-simulation", filter_milestone)
    print(f"\n🎯 MILESTONE events only: {len(result_milestone['events'])} events")
    for event in result_milestone['events']:
        milestone_type = event.get('details', {}).get('milestone_type', 'unknown')
        print(f"   - {milestone_type}: {event['description']}")

    # Filter by agent
    filter_agent = EventFilter(agent_ids=["agent_alpha"], limit=100)
    result_agent = service.get_filtered_events("demo-simulation", filter_agent)
    print(f"\n👤 Agent alpha events: {len(result_agent['events'])} events")
    for event in result_agent['events']:
        print(f"   - {event['event_type']}: {event['description']}")

    # Filter by turn
    filter_turn = EventFilter(turn_start=1, turn_end=1, limit=100)
    result_turn = service.get_filtered_events("demo-simulation", filter_turn)
    print(f"\n🔢 Turn 1 events: {len(result_turn['events'])} events")

    print()


def demo_causality():
    """Demonstrate causality chain analysis."""
    print("=" * 60)
    print("DEMO 3: Causality Chain Analysis")
    print("=" * 60)

    service = EventService(Path("output"))

    # Get all events to find a DECISION event
    filter_all = EventFilter(event_types=["DECISION"], limit=10)
    result = service.get_filtered_events("demo-simulation", filter_all)

    if result['events']:
        decision_event = result['events'][0]
        event_id = decision_event['event_id']

        print(f"\n🔍 Analyzing causality for event: {decision_event['description']}")

        # Get causality chain
        chain = service.get_causality_chain("demo-simulation", event_id, depth=5)

        if chain:
            print(f"\n⬆️  Upstream events (causes): {len(chain['upstream'])}")
            for event in chain['upstream']:
                print(f"   - {event['event_type']}: {event['description']}")

            print(f"\n⬇️  Downstream events (effects): {len(chain['downstream'])}")
            if chain['downstream']:
                for event in chain['downstream']:
                    print(f"   - {event['event_type']}: {event['description']}")
            else:
                print("   (none)")
    else:
        print("\n⚠️  No DECISION events found")

    print()


def demo_verbosity_levels():
    """Demonstrate different verbosity levels."""
    print("=" * 60)
    print("DEMO 4: Verbosity Level Filtering")
    print("=" * 60)

    from llm_sim.infrastructure.events.config import should_log_event

    event_types = ["MILESTONE", "DECISION", "ACTION", "STATE", "DETAIL", "SYSTEM"]
    verbosity_levels = [
        VerbosityLevel.MILESTONE,
        VerbosityLevel.DECISION,
        VerbosityLevel.ACTION,
        VerbosityLevel.STATE,
        VerbosityLevel.DETAIL,
    ]

    print("\n📊 Event capture by verbosity level:\n")
    print(f"{'Event Type':<12} | " + " | ".join(f"{v.value:<10}" for v in verbosity_levels))
    print("-" * 70)

    for event_type in event_types:
        captured = []
        for verbosity in verbosity_levels:
            captured.append("✅" if should_log_event(event_type, verbosity) else "❌")
        print(f"{event_type:<12} | " + " | ".join(f"{c:<10}" for c in captured))

    print("\n💡 Explanation:")
    print("   - MILESTONE: Only major simulation events")
    print("   - DECISION:  MILESTONE + agent decisions")
    print("   - ACTION:    DECISION + agent actions (default)")
    print("   - STATE:     ACTION + state variable changes")
    print("   - DETAIL:    STATE + calculations + system events")

    print()


async def main():
    """Run all demonstrations."""
    print("\n" + "=" * 60)
    print("  EVENT STREAMING FEATURE DEMONSTRATION")
    print("=" * 60 + "\n")

    # Demo 1: Event Writer
    await demo_event_writer()

    # Demo 2: Event Service
    demo_event_service()

    # Demo 3: Causality
    demo_causality()

    # Demo 4: Verbosity levels
    demo_verbosity_levels()

    print("=" * 60)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\n✅ All event streaming features demonstrated successfully!")
    print("\n📚 Next steps:")
    print("   - Run API server: python -m llm_sim.api.server")
    print("   - View OpenAPI docs: http://localhost:8000/docs")
    print("   - Query events: curl http://localhost:8000/simulations")
    print()


if __name__ == "__main__":
    asyncio.run(main())
