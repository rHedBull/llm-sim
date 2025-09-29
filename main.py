"""CLI entry point for the simulation."""

import argparse
import json
import sys
from pathlib import Path

from src.llm_sim.orchestrator import SimulationOrchestrator


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="Run a turn-based economic simulation")
    parser.add_argument("config", type=str, help="Path to YAML configuration file")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--output", type=str, help="Output file for results (JSON format)")
    parser.add_argument("--print-history", action="store_true", help="Print full state history")

    args = parser.parse_args()

    # Check config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file '{config_path}' not found", file=sys.stderr)
        sys.exit(1)

    try:
        # Create and run simulation
        orchestrator = SimulationOrchestrator.from_yaml(str(config_path))

        if args.debug:
            print(f"Loading configuration from: {config_path}")
            print(f"Simulation name: {orchestrator.config.simulation.name}")
            print(f"Max turns: {orchestrator.config.simulation.max_turns}")
            print(f"Number of agents: {len(orchestrator.agents)}")

        result = orchestrator.run()

        # Display results
        final_state = result["final_state"]
        stats = result["stats"]

        print("\n=== Simulation Complete ===")
        print(f"Final Turn: {final_state.turn}")
        print(f"Total Economic Value: {final_state.global_state.total_economic_value:.2f}")
        print("\nAgent Final States:")
        for name, agent in final_state.agents.items():
            print(f"  {name}: {agent.economic_strength:.2f}")

        print("\nValidation Statistics:")
        print(f"  Total Validated: {stats['validation']['total_validated']:.0f}")
        print(f"  Total Rejected: {stats['validation']['total_rejected']:.0f}")
        print(f"  Acceptance Rate: {stats['validation']['acceptance_rate']:.2%}")

        if args.print_history:
            print("\n=== State History ===")
            for state in result["history"]:
                print(
                    f"Turn {state.turn}: Total Value = {state.global_state.total_economic_value:.2f}"
                )

        # Save results if requested
        if args.output:
            output_data = {
                "final_state": final_state.model_dump(),
                "stats": stats,
                "history": (
                    [s.model_dump() for s in result["history"]] if args.print_history else None
                ),
            }
            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\nResults saved to: {args.output}")

    except Exception as e:
        print(f"Error running simulation: {e}", file=sys.stderr)
        if args.debug:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
