"""Simulation orchestrator that coordinates all components."""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from llm_sim.discovery import ComponentDiscovery
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig
from llm_sim.models.state import SimulationState
from llm_sim.utils.llm_client import LLMClient
from llm_sim.utils.logging import configure_logging, get_logger

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

        # Initialize discovery mechanism
        self.discovery = ComponentDiscovery(Path(__file__).parent)

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
        if self.config.logging:
            configure_logging(level=self.config.logging.level, format=self.config.logging.format)
        else:
            configure_logging(level="INFO", format="json")

    def _create_engine(self):
        """Create engine based on configuration using discovery mechanism.

        Returns:
            Configured engine instance
        """
        # Use discovery to load engine class
        EngineClass = self.discovery.load_engine(self.config.engine.type)

        # Check if engine requires LLM client (for LLM-based engines)
        try:
            # Try with LLM client first
            if self.config.llm:
                llm_client = LLMClient(config=self.config.llm)
                return EngineClass(config=self.config, llm_client=llm_client)
        except TypeError:
            # If TypeError, engine doesn't take llm_client parameter
            pass

        # Fall back to basic initialization
        return EngineClass(config=self.config)

    def _create_agents(
        self, agent_strategies: Optional[Dict[str, str]] = None
    ) -> List:
        """Create agents based on configuration using discovery mechanism.

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
            # Use discovery to load agent class
            AgentClass = self.discovery.load_agent(agent_config.type)

            # Build initialization parameters
            init_params = {"name": agent_config.name}

            # Add strategy if available (for agents that support it)
            if agent_strategies and agent_config.name in agent_strategies:
                init_params["strategy"] = agent_strategies[agent_config.name]
            elif hasattr(agent_config, "strategy"):
                init_params["strategy"] = agent_config.strategy

            # Try with LLM client first (for LLM-based agents)
            if llm_client:
                try:
                    agent = AgentClass(**init_params, llm_client=llm_client)
                    agents.append(agent)
                    continue
                except TypeError:
                    # Agent doesn't take llm_client parameter
                    pass

            # Try without LLM client
            try:
                agent = AgentClass(**init_params)
                agents.append(agent)
            except TypeError:
                # Agent requires llm_client but we don't have one - create default
                from llm_sim.models.config import LLMConfig
                if not llm_client:
                    llm_client = LLMClient(config=LLMConfig())
                agent = AgentClass(**init_params, llm_client=llm_client)
                agents.append(agent)

        return agents

    def _create_validator(self):
        """Create validator based on configuration using discovery mechanism.

        Returns:
            Configured validator instance
        """
        # Use discovery to load validator class
        ValidatorClass = self.discovery.load_validator(self.config.validator.type)

        # Check if validator requires LLM client (for LLM-based validators)
        if self.config.llm:
            try:
                llm_client = LLMClient(config=self.config.llm)
                return ValidatorClass(
                    llm_client=llm_client,
                    domain=self.config.validator.domain or "economic",
                    permissive=self.config.validator.permissive
                )
            except TypeError:
                # Validator doesn't take llm_client parameter
                pass

        # Fall back to basic initialization
        return ValidatorClass()

    def run(self) -> Dict[str, Any]:
        """Run the simulation.

        Returns:
            Dictionary containing:
                - final_state: Final simulation state
                - history: List of all states
                - stats: Simulation statistics
        """
        import asyncio
        import inspect

        # Check if any component has async methods
        has_async = (
            inspect.iscoroutinefunction(self.agents[0].decide_action) if self.agents else False
        ) or inspect.iscoroutinefunction(self.validator.validate_actions) or inspect.iscoroutinefunction(self.engine.run_turn)

        if has_async:
            # Run entire simulation asynchronously
            return asyncio.run(self._run_async())
        else:
            # Run sync version
            return self._run_sync()

    def _run_sync(self) -> Dict[str, Any]:
        """Run simulation synchronously (for non-LLM components)."""
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
            state = self._run_turn_sync(state)
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

    async def _run_async(self) -> Dict[str, Any]:
        """Run simulation asynchronously (for LLM components)."""
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
            state = await self._run_turn_async(state)
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

    def _run_turn_sync(self, state: SimulationState) -> SimulationState:
        """Run a single simulation turn synchronously (for non-LLM components).

        Args:
            state: Current simulation state

        Returns:
            New state after turn execution
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
