"""Simulation orchestrator that coordinates all components."""

from typing import Any, Dict, List, Optional

import yaml

from llm_sim.agents.nation import NationAgent
from llm_sim.agents.econ_llm_agent import EconLLMAgent
from llm_sim.engines.economic import EconomicEngine
from llm_sim.engines.econ_llm_engine import EconLLMEngine
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient
from llm_sim.utils.logging import configure_logging, get_logger
from llm_sim.validators.always_valid import AlwaysValidValidator
from llm_sim.validators.econ_llm_validator import EconLLMValidator

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

    def _create_engine(self):
        """Create engine based on configuration.

        Returns:
            Configured engine instance
        """
        if self.config.engine.type == "economic":
            return EconomicEngine(self.config)
        elif self.config.engine.type == "econ_llm_engine":
            # NEW: LLM-based economic engine
            if not self.config.llm:
                raise ValueError("LLM config required for econ_llm_engine")
            llm_client = LLMClient(config=self.config.llm)
            return EconLLMEngine(config=self.config, llm_client=llm_client)
        else:
            raise ValueError(f"Unknown engine type: {self.config.engine.type}")

    def _create_agents(
        self, agent_strategies: Optional[Dict[str, str]] = None
    ) -> List:
        """Create agents based on configuration.

        Args:
            agent_strategies: Optional mapping of agent names to strategies

        Returns:
            List of configured agent instances
        """
        agents = []

        # Initialize shared LLM client if LLM config present
        llm_client = None
        if self.config.llm:
            llm_client = LLMClient(config=self.config.llm)

        for agent_config in self.config.agents:
            if agent_config.type == "nation":
                strategy = "grow"  # Default
                if agent_strategies and agent_config.name in agent_strategies:
                    strategy = agent_strategies[agent_config.name]

                agent = NationAgent(name=agent_config.name, strategy=strategy)
                agents.append(agent)
            elif agent_config.type == "econ_llm_agent":
                # NEW: LLM-based economic agent
                if not llm_client:
                    raise ValueError("LLM config required for econ_llm_agent")
                agent = EconLLMAgent(name=agent_config.name, llm_client=llm_client)
                agents.append(agent)
            else:
                raise ValueError(f"Unknown agent type: {agent_config.type}")

        return agents

    def _create_validator(self):
        """Create validator based on configuration.

        Returns:
            Configured validator instance
        """
        if self.config.validator.type == "always_valid":
            return AlwaysValidValidator()
        elif self.config.validator.type == "econ_llm_validator":
            # NEW: LLM-based economic validator
            if not self.config.llm:
                raise ValueError("LLM config required for econ_llm_validator")
            llm_client = LLMClient(config=self.config.llm)
            return EconLLMValidator(
                llm_client=llm_client,
                domain=self.config.validator.domain or "economic",
                permissive=self.config.validator.permissive
            )
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

    async def _run_turn_async(self, state: SimulationState) -> SimulationState:
        """Run a single simulation turn asynchronously (for LLM-based components).

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
            action = await agent.decide_action(state)
            actions.append(action)

        # Validate actions
        validated_actions = await self.validator.validate_actions(actions, state)

        # Execute turn
        new_state = await self.engine.run_turn(validated_actions)

        return new_state

    def _run_turn(self, state: SimulationState) -> SimulationState:
        """Run a single simulation turn.

        Args:
            state: Current simulation state

        Returns:
            New state after turn
        """
        # Check if we need async execution (for LLM-based components)
        import asyncio
        import inspect

        # Check if any component has async methods
        has_async = (
            inspect.iscoroutinefunction(self.agents[0].decide_action) if self.agents else False
        ) or inspect.iscoroutinefunction(self.validator.validate_actions) or inspect.iscoroutinefunction(self.engine.run_turn)

        if has_async:
            # Run async version
            return asyncio.run(self._run_turn_async(state))
        else:
            # Run sync version (legacy)
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
