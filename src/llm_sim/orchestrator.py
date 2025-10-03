"""Simulation orchestrator that coordinates all components."""

from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

import yaml

from llm_sim.discovery import ComponentDiscovery
from llm_sim.models.action import Action
from llm_sim.models.config import SimulationConfig, get_variable_definitions
from llm_sim.models.state import SimulationState
from llm_sim.models.checkpoint import RunMetadata, SimulationResults
from llm_sim.models.observation import construct_observation
from llm_sim.persistence.checkpoint_manager import CheckpointManager
from llm_sim.persistence.run_id_generator import RunIDGenerator
from llm_sim.utils.llm_client import LLMClient
from llm_sim.utils.logging import configure_logging, get_logger

logger = get_logger(__name__)


class SimulationOrchestrator:
    """Main orchestrator for running simulations."""

    def __init__(
        self, config: SimulationConfig, agent_strategies: Optional[Dict[str, str]] = None,
        output_root: Path = Path("output"),
        implementations_root: Optional[Path] = None
    ) -> None:
        """Initialize orchestrator with configuration.

        Args:
            config: Simulation configuration
            agent_strategies: Optional mapping of agent names to strategies
            output_root: Root directory for output files
            implementations_root: Optional root directory for implementations/ discovery.
                                If None, defaults to framework's directory (backward compat).
        """
        self.config = config
        self.output_root = output_root
        self._configure_logging()

        # Initialize discovery mechanism
        discovery_root = implementations_root if implementations_root else Path(__file__).parent
        self.discovery = ComponentDiscovery(discovery_root)

        # Initialize components
        self.engine = self._create_engine()
        self.agents = self._create_agents(agent_strategies)
        self.validator = self._create_validator()

        # Generate unique run ID
        self.start_time = datetime.now()
        self.run_id = RunIDGenerator.generate(
            simulation_name=self.config.simulation.name,
            num_agents=len(self.agents),
            start_time=self.start_time,
            output_root=self.output_root
        )

        # Get variable definitions for schema hash
        agent_var_defs, global_var_defs = get_variable_definitions(self.config)

        # Initialize checkpoint manager with variable definitions
        self.checkpoint_manager = CheckpointManager(
            run_id=self.run_id,
            agent_var_defs=agent_var_defs,
            global_var_defs=global_var_defs,
            checkpoint_interval=self.config.simulation.checkpoint_interval,
            output_root=self.output_root
        )

        # Create run metadata
        self.run_metadata = RunMetadata(
            run_id=self.run_id,
            simulation_name=self.config.simulation.name,
            num_agents=len(self.agents),
            start_time=self.start_time,
            end_time=None,
            checkpoint_interval=self.config.simulation.checkpoint_interval,
            config_snapshot=self.config.model_dump()
        )

        # State tracking
        self.history: List[SimulationState] = []

    @classmethod
    def from_yaml(
        cls,
        path: str,
        output_root: Path = Path("output"),
        implementations_root: Optional[Path] = None
    ) -> "SimulationOrchestrator":
        """Load configuration from YAML file and create orchestrator.

        Args:
            path: Path to YAML configuration file
            output_root: Root directory for output files
            implementations_root: Optional root directory for implementations/ discovery

        Returns:
            Configured SimulationOrchestrator instance
        """
        with open(path, "r") as f:
            config_data = yaml.safe_load(f)

        config = SimulationConfig(**config_data)
        return cls(config, output_root=output_root, implementations_root=implementations_root)

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

    def initialize(self) -> SimulationState:
        """Initialize simulation state.

        Returns:
            Initial simulation state

        Note: This is a convenience method for testing. The run() method
        initializes state automatically.
        """
        return self.engine.initialize_state()

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
            run_id=self.run_id,
        )

        # Initialize state
        state = self.engine.initialize_state()
        self.history.append(state)

        # Run simulation turns
        while not self.engine.check_termination(state):
            state = self._run_turn_sync(state)
            self.history.append(state)

            # Check if we should save checkpoint
            is_final = self.engine.check_termination(state)
            if self.checkpoint_manager.should_save_checkpoint(state.turn, is_final):
                checkpoint_type = "final" if is_final else "interval"
                self.checkpoint_manager.save_checkpoint(state, checkpoint_type)
                logger.info(
                    "checkpoint_saved",
                    turn=state.turn,
                    type=checkpoint_type,
                )

            # Always save last checkpoint (overwrite each turn)
            self.checkpoint_manager.save_checkpoint(state, "last")

            # Log turn completion (safely handle dynamic global state)
            log_data = {"turn": state.turn}
            if hasattr(state.global_state, "total_economic_value"):
                log_data["total_value"] = state.global_state.total_economic_value
            logger.info("turn_completed", **log_data)

        # Update run metadata end time
        self.run_metadata = RunMetadata(
            **{**self.run_metadata.model_dump(), "end_time": datetime.now()}
        )

        # Collect checkpoint list
        checkpoints = self.checkpoint_manager.list_checkpoints(self.run_id)

        # Collect final statistics
        stats = self._collect_stats()

        # Save simulation results
        results = SimulationResults(
            run_metadata=self.run_metadata,
            final_state=state,
            checkpoints=checkpoints,
            summary_stats=stats
        )
        self.checkpoint_manager.save_results(results)

        # Log simulation completion (safely handle dynamic global state)
        log_data = {
            "final_turn": state.turn,
            "total_turns": len(self.history) - 1,  # Exclude initial state
            "run_id": self.run_id,
        }
        if hasattr(state.global_state, "total_economic_value"):
            log_data["final_value"] = state.global_state.total_economic_value
        logger.info("simulation_completed", **log_data)

        return {"final_state": state, "history": self.history, "stats": stats, "run_id": self.run_id}

    async def _run_async(self) -> Dict[str, Any]:
        """Run simulation asynchronously (for LLM components)."""
        logger.info(
            "simulation_starting",
            name=self.config.simulation.name,
            max_turns=self.config.simulation.max_turns,
            num_agents=len(self.agents),
            run_id=self.run_id,
        )

        # Initialize state
        state = self.engine.initialize_state()
        self.history.append(state)

        # Run simulation turns
        while not self.engine.check_termination(state):
            state = await self._run_turn_async(state)
            self.history.append(state)

            # Check if we should save checkpoint
            is_final = self.engine.check_termination(state)
            if self.checkpoint_manager.should_save_checkpoint(state.turn, is_final):
                checkpoint_type = "final" if is_final else "interval"
                self.checkpoint_manager.save_checkpoint(state, checkpoint_type)
                logger.info(
                    "checkpoint_saved",
                    turn=state.turn,
                    type=checkpoint_type,
                )

            # Always save last checkpoint (overwrite each turn)
            self.checkpoint_manager.save_checkpoint(state, "last")

            # Log turn completion (safely handle dynamic global state)
            log_data = {"turn": state.turn}
            if hasattr(state.global_state, "total_economic_value"):
                log_data["total_value"] = state.global_state.total_economic_value
            logger.info("turn_completed", **log_data)

        # Update run metadata end time
        self.run_metadata = RunMetadata(
            **{**self.run_metadata.model_dump(), "end_time": datetime.now()}
        )

        # Collect checkpoint list
        checkpoints = self.checkpoint_manager.list_checkpoints(self.run_id)

        # Collect final statistics
        stats = self._collect_stats()

        # Save simulation results
        results = SimulationResults(
            run_metadata=self.run_metadata,
            final_state=state,
            checkpoints=checkpoints,
            summary_stats=stats
        )
        self.checkpoint_manager.save_results(results)

        # Log simulation completion (safely handle dynamic global state)
        log_data = {
            "final_turn": state.turn,
            "total_turns": len(self.history) - 1,  # Exclude initial state
            "run_id": self.run_id,
        }
        if hasattr(state.global_state, "total_economic_value"):
            log_data["final_value"] = state.global_state.total_economic_value
        logger.info("simulation_completed", **log_data)

        return {"final_state": state, "history": self.history, "stats": stats, "run_id": self.run_id}

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
            agent_name = agent.name
            # Construct observation for this agent based on observability config
            if self.config.observability and self.config.observability.enabled:
                observation = construct_observation(agent_name, state, self.config.observability)
                logger.debug(
                    "constructing_observation",
                    observer=agent_name,
                    turn=state.turn,
                    visible_agents=list(observation.agents.keys())
                )
            else:
                observation = state  # Full observability (backward compatible)

            action = await agent.decide_action(observation)
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
        for agent_name, agent in self.agents.items():
            # Construct observation for this agent based on observability config
            if self.config.observability and self.config.observability.enabled:
                observation = construct_observation(agent_name, state, self.config.observability)
                logger.debug(
                    "constructing_observation",
                    observer=agent_name,
                    turn=state.turn,
                    visible_agents=list(observation.agents.keys())
                )
            else:
                observation = state  # Full observability (backward compatible)

            action = agent.decide_action(observation)
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
        stats = {
            "validation": self.validator.get_stats(),
            "total_turns": len(self.history) - 1,
            "final_turn": self.history[-1].turn if self.history else 0,
        }

        # Add economic values if they exist (backward compatibility)
        if self.history and hasattr(self.history[0].global_state, "total_economic_value"):
            stats["initial_value"] = self.history[0].global_state.total_economic_value

        if self.history and hasattr(self.history[-1].global_state, "total_economic_value"):
            stats["final_value"] = self.history[-1].global_state.total_economic_value

        return stats


# Backward compatibility alias
Orchestrator = SimulationOrchestrator
