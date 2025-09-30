"""Simulation orchestrator that coordinates all components."""

from typing import Any, Dict, List, Optional

import yaml

from llm_sim.agents.nation import NationAgent
from llm_sim.engines.economic import EconomicEngine
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState
from llm_sim.utils.logging import configure_logging, get_logger
from llm_sim.validators.always_valid import AlwaysValidValidator

logger = get_logger(__name__)


class SimulationOrchestrator:
    """Main orchestrator for running simulations."""

    def __init__(
        self, config: SimulationConfig, agent_strategies: Optional[Dict[str, str]] = None
    ) -> None:
        """Initialize orchestrator with configuration.

        Args:
            config: Simulation configuration
            agent_strategies: Optional mapping of agent names to strategies
        """
        self.config = config
        self._configure_logging()

        # Initialize components
        self.engine = self._create_engine()
        self.agents = self._create_agents(agent_strategies)
        self.validator = self._create_validator()

        # State tracking
        self.history: List[SimulationState] = []

    @classmethod
    def from_yaml(cls, path: str) -> "SimulationOrchestrator":
        """Load configuration from YAML file and create orchestrator.

        Args:
            path: Path to YAML configuration file

        Returns:
            Configured SimulationOrchestrator instance
        """
        with open(path, "r") as f:
            config_data = yaml.safe_load(f)

        config = SimulationConfig(**config_data)
        return cls(config)

    def _configure_logging(self) -> None:
        """Configure logging based on config."""
        configure_logging(level=self.config.logging.level, format=self.config.logging.format)

    def _create_engine(self) -> EconomicEngine:
        """Create engine based on configuration.

        Returns:
            Configured engine instance
        """
        if self.config.engine.type == "economic":
            return EconomicEngine(self.config)
        else:
            raise ValueError(f"Unknown engine type: {self.config.engine.type}")

    def _create_agents(
        self, agent_strategies: Optional[Dict[str, str]] = None
    ) -> List[NationAgent]:
        """Create agents based on configuration.

        Args:
            agent_strategies: Optional mapping of agent names to strategies

        Returns:
            List of configured agent instances
        """
        agents = []

        for agent_config in self.config.agents:
            if agent_config.type == "nation":
                strategy = "grow"  # Default
                if agent_strategies and agent_config.name in agent_strategies:
                    strategy = agent_strategies[agent_config.name]

                agent = NationAgent(name=agent_config.name, strategy=strategy)
                agents.append(agent)
            else:
                raise ValueError(f"Unknown agent type: {agent_config.type}")

        return agents

    def _create_validator(self) -> AlwaysValidValidator:
        """Create validator based on configuration.

        Returns:
            Configured validator instance
        """
        if self.config.validator.type == "always_valid":
            return AlwaysValidValidator()
        else:
            raise ValueError(f"Unknown validator type: {self.config.validator.type}")

    def run(self) -> Dict[str, Any]:
        """Run the simulation.

        Returns:
            Dictionary containing:
                - final_state: Final simulation state
                - history: List of all states
                - stats: Simulation statistics
        """
        logger.info(
            "simulation_starting",
            name=self.config.simulation.name,
            max_turns=self.config.simulation.max_turns,
            num_agents=len(self.agents),
        )

        # Initialize state
        state = self.engine.initialize_state()
        self.history.append(state)

        # Run simulation turns
        while not self.engine.check_termination(state):
            state = self._run_turn(state)
            self.history.append(state)

            logger.info(
                "turn_completed",
                turn=state.turn,
                total_value=state.global_state.total_economic_value,
            )

        # Collect final statistics
        stats = self._collect_stats()

        logger.info(
            "simulation_completed",
            final_turn=state.turn,
            final_value=state.global_state.total_economic_value,
            total_turns=len(self.history) - 1,  # Exclude initial state
        )

        return {"final_state": state, "history": self.history, "stats": stats}

    def _run_turn(self, state: SimulationState) -> SimulationState:
        """Run a single simulation turn.

        Args:
            state: Current simulation state

        Returns:
            New state after turn
        """
        # Distribute state to agents
        for agent in self.agents:
            agent.receive_state(state)

        # Collect actions from agents
        actions: List[Action] = []
        for agent in self.agents:
            action = agent.decide_action(state)
            actions.append(action)

        # Validate actions
        validated_actions = self.validator.validate_actions(actions, state)

        # Execute turn
        new_state = self.engine.run_turn(validated_actions)

        return new_state

    def _collect_stats(self) -> Dict[str, Any]:
        """Collect simulation statistics.

        Returns:
            Dictionary of statistics
        """
        return {
            "validation": self.validator.get_stats(),
            "total_turns": len(self.history) - 1,
            "final_turn": self.history[-1].turn if self.history else 0,
            "initial_value": (
                self.history[0].global_state.total_economic_value if self.history else 0
            ),
            "final_value": (
                self.history[-1].global_state.total_economic_value if self.history else 0
            ),
        }
