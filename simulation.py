import random
from typing import TYPE_CHECKING, Dict, List, Literal, Set, Tuple
import log_utils

if TYPE_CHECKING:
    from consumer import Consumer
    from store import Store
    from market_agent import MarketAgent


class Simulation:
    """
    High-level orchestrator replicating the NetLogo Hotelling's Law observer.

    Manages a grid of Consumer patches and a collection of MarketAgents (Stores
    or Chains), advancing the simulation one tick at a time via `step`.

    Attributes:
        layout (str): "plane" for 2-D grid, "line" for 1-D column.
        pricing_only (bool): Stores may only change prices, not move.
        moving_only (bool): Stores may only move, not change prices.
        mode (str): "store" for stores only, "chain" for chains mode.
        width (int): Number of patch columns in the world.
        height (int): Number of patch rows in the world.
        consumers (List["Consumer"]): All consumer patches.
        stores (List["Store"]): All stores.
        agents (List["MarketAgent"]): All competing market agents.
    """

    def __init__(
        self,
        layout: Literal["plane", "line"] = "plane",
        rules: Literal["normal", "moving-only", "pricing-only"] = "normal",
        mode: Literal["store", "chain"] = "store",
        number_of_stores: int = 3,
        number_of_chains: int = 0,
        chain_allocations: list[int] = [],
        width: int = 41,
        height: int = 41,
    ):
        self.layout: str = layout
        self.pricing_only: bool = rules == "pricing-only"
        self.moving_only: bool = rules == "moving-only"
        self.width: int = width
        self.height: int = height
        self.step_count: int = 0

        # Coordinate bounds centred at origin, matching NetLogo's -20..20 default.
        self._min_x: int = -(width // 2)
        self._max_x: int = width // 2
        self._min_y: int = -(height // 2)
        self._max_y: int = height // 2

        # Setup our consumers, stores, and market agents.
        self.consumers: List["Consumer"] = self._setup_consumers()
        self.stores: List["Store"] = self._setup_stores(number_of_stores)
        self.agents: List["MarketAgent"] = self._setup_agents(
            mode, number_of_chains, chain_allocations
        )

        self._recalculate_area()

    # SETUP ___________________________________________________________________

    def _setup_consumers(self) -> List["Consumer"]:
        """Setup simulation's consumers by assigning

        Returns:
            List["Consumer"]: Consumers to be used in the simulation.
        """
        from consumer import Consumer

        if self.layout == "line":
            return [Consumer((0, y)) for y in range(self._min_y, self._max_y + 1)]
        return [
            Consumer((x, y))
            for x in range(self._min_x, self._max_x + 1)
            for y in range(self._min_y, self._max_y + 1)
        ]

    def _setup_stores(self, number_of_stores: int) -> List["Store"]:
        """Setup simulation's stores by randomly assigning throughout model.

        Args:
            number_of_stores (int): Number of stores to include in the model.

        Raises:
            RuntimeError: Invalid inputs for number of stores provided.

        Returns:
            List["Store"]: Stores to be used in the simulation.
        """
        from store import Store

        # Validate inputs.
        if number_of_stores == 0:
            raise RuntimeError("Must specify at least 1 store.")

        # Randomly select starting location for Store agents.
        stores = []
        positions = random.sample(
            [c.position for c in self.consumers], number_of_stores
        )
        for i, pos in enumerate(positions):
            stores.append(Store(agent_id=i, position=pos, price=10))

        return stores

    def _setup_agents(
        self, mode: str, number_of_chains: int, chain_allocations: list[int]
    ) -> List["MarketAgent"]:
        """Setup market agents for running the simulation.

        Args:
            mode (str): Mode that the simulation is running in.
            number_of_chains (int): Number of chains to include in simulation.
            chain_allocations (list[int]): A list of integers specifying how many
                stores should be allocated to each chain. The length of this list
                should be equal to number_of_chains, and the sum should be equal to
                the total number of stores.

        Raises:
            RuntimeError: Invalid inputs for mode and number of stores/chains provided.

        Returns:
            List["MarketAgent"]: List of agents that implement the MarketAgent interface.
        """
        from chain import Chain

        agents: List["MarketAgent"] = []

        if mode == "store":
            # Validate inputs for store mode.
            if number_of_chains != 0:
                raise RuntimeError("Cannot specify any chains when mode is 'store'")

            # Stores are the agents.
            agents = self.stores

        elif mode == "chain":
            # Validate inputs for chain mode.
            if number_of_chains == 0:
                raise RuntimeError("Must specify at least 1 chain.")
            if sum(chain_allocations) > len(self.stores):
                raise RuntimeError("Chain allocations exceed total number of stores.")
            if len(chain_allocations) != number_of_chains:
                raise RuntimeError(
                    "Length of chain_allocations must match number_of_chains."
                )

            # Assign stores to chains according to the provided chain_allocations list
            assigned_stores: Set["Store"] = set()
            store_pool = self.stores.copy()

            for i, num_to_allocate in enumerate(chain_allocations):
                # Pull the requested number of stores out of the pool for this chain
                chain_stores = [store_pool.pop(0) for _ in range(num_to_allocate)]

                agents.append(Chain(agent_id=-(i + 1), stores=chain_stores))

                assigned_stores.update(chain_stores)

            # Any remaining stores are independent agents
            for store in self.stores:
                if store not in assigned_stores:
                    agents.append(store)

        else:
            raise RuntimeError("Invalid mode provided.")

        return agents

    # CONSUMER QUERIES _________________________________________________________________

    def is_valid_consumer_position(self, position: Tuple[int, int]) -> bool:
        """Evaluate whether a given position is valid for a consumer.

        Args:
            position (Tuple[int, int]): Position to be considered.

        Returns:
            True if position is valid, False otherwise.
        """
        x, y = position
        if self.layout == "line":
            return x == 0 and self._min_y <= y <= self._max_y
        return self._min_x <= x <= self._max_x and self._min_y <= y <= self._max_y

    # MARKET SHARE LOGIC _______________________________________________________________

    def _recalculate_area(self) -> None:
        """Assigns every consumer to its preferred agent and refreshes area counts.

        Mirrors NetLogo's 'recalculate-area' procedure.
        """

        # Reset area counter.
        for store in self.stores:
            store._area_count = 0

        # Update consumer preferred store, and area count.
        for consumer in self.consumers:
            consumer.choose_store(self.stores)._area_count += 1

    def calculate_hypothetical_market_share(
        self,
        store_id: int,
        hypothetical_changes: List[Tuple[int, Tuple[int, int], int]],
    ) -> int:
        """
        Calculates the hypothetical market share for an agent given a set of
        hypothetical changes to the simulation state (store positions and prices),
        with all other unlisted agents remaining unchanged.

        Able to mirror Netlogo's 'potential-market-share' and 'market-share-if-moveto'
        procedures together (with a single store-hypothetical input).

        Args:
            store_id (int): The ID of the agent.
            hypothetical_changes (List[Tuple[int, Tuple[int, int], int]]): A list of
                tuples containing hypothetical changes to the simulation state in
                the form (store_id, (new_x, new_y), new_price).

        Returns:
            Integer representing the hypothetical market share for the provided agent
            given the hypothetical changes.
        """

        original_states: Dict[Store, Tuple[Tuple[int, int], int]] = {}
        target_store_instance = None

        for hyp_id, hyp_pos, hyp_price in hypothetical_changes:
            target_store = None
            for store in self.stores:
                if store._id == hyp_id:
                    target_store = store
                    break
            assert target_store is not None

            # Store original position and price for later restoration
            if target_store not in original_states:
                original_states[target_store] = (
                    target_store.position,
                    target_store.price,
                )

            # Change the store to have the hypothetical state
            target_store.position = hyp_pos
            target_store.price = hyp_price

        for store in self.stores:
            if store._id == store_id:
                target_store_instance = store
                break
        assert target_store_instance is not None

        hypothetical_market_share: int = 0
        for consumer in self.consumers:
            if consumer.choose_store(self.stores) == target_store_instance:
                hypothetical_market_share += 1

        # Move every store back to current position and price.
        for store, (orig_pos, orig_price) in original_states.items():
            store.position = orig_pos
            store.price = orig_price

        return hypothetical_market_share

    # EXECUTION ________________________________________________________________________

    def step(self):
        """Iterate the simulation by one tick according to the rules of the simulation.

        Mirrors Netlogo's 'go' procedure.

        Assumption:
            For similarity to the Netlogo implementation, and simulate simultaneous
            decision making, we have followed Netlogo's go procedure:
                1. All agents simultaneously evaluate their optimal move.
                2. All agents simultaneously evaluate their optimal price.
                3. All changes are applied at once.
                4. Consumer-store assignments and area counts are recalculated.
                5. Tick the simulation.
        """

        # Step 1: All agents determine next position.
        if not self.pricing_only:
            for agent in self.agents:
                agent.evaluate_move(self)

        # Step 2: All agents determine next price.
        if not self.moving_only:
            for agent in self.agents:
                agent.evaluate_price(self)

        # Step 3: All agents apply changes at once.
        for agent in self.agents:
            agent.apply_update()

        # Step 4: Consumers are assigned to stores, and area count is recalculated.
        self._recalculate_area()

        # Step 5: Tick simulation.
        self.step_count += 1

    def export_state(self) -> Dict:
        """Export the state of the simulation.

        Returns:
            Dict: A dictionary containing the current state of the simulation.
        """
        from chain import Chain

        store_positions: list[list[int]] = []
        store_prices: list[list[int]] = []
        store_market_share: list[list[int]] = []

        # Flatten store state
        for s in self.stores:
            store_positions.append([s._id, s.position[0], s.position[1]])
            store_prices.append([s._id, s.price])
            store_market_share.append(
                [
                    s._id,
                    self.calculate_hypothetical_market_share(
                        store_id=s._id,
                        hypothetical_changes=[(s._id, s.position, s.price)],
                    ),
                ]
            )

        # Flatten chain state
        store_chain_ids: list[list[int]] = []
        for a in self.agents:
            if isinstance(a, Chain):
                for s in a.controlled_stores:
                    store_chain_ids.append([s._id, a._id])

        return {
            "step": self.step_count,
            "store-positions": store_positions,
            "store-market-shares": store_market_share,
            "store-prices": store_prices,
            "store-chain-ids": store_chain_ids,
        }


def run_simulation_experiment(params):
    """Simulation test case runner.

    Args:
        params (Tuple): Parameters to execution a simulation with.

    Returns:
        List[str]: Simulation results.
    """

    run_id, max_ticks, num_store, layout, rule, num_chains, mode, chain_allocations = (
        params
    )

    # Build simulation environment.
    sim = Simulation(
        number_of_stores=num_store,
        rules=rule,
        layout=layout,
        mode=mode,
        number_of_chains=num_chains,
        chain_allocations=chain_allocations,
    )

    # Execute test iteration.
    results = []
    for _ in range(max_ticks):
        sim.step()

        # Store entry results
        state: dict = sim.export_state()

        row_entry = [
            run_id,
            layout,
            num_store,
            rule,
            state["step"],
            log_utils.serialise_list(state["store-positions"]),
            log_utils.serialise_list(state["store-market-shares"]),
            log_utils.serialise_list(state["store-prices"]),
            log_utils.serialise_list(state["store-chain-ids"]),
        ]

        results.append(row_entry)

    print(f"Completed: Num stores: {num_store}, Layout: {layout}, Rule: {rule}")

    # Build results.
    return results
