import random
from typing import TYPE_CHECKING, Dict, List, Literal, Tuple

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
        layout (str): "plane" for 2-D grid, "line" for 1-D column (pxcor=0).
        pricing_only (bool): Stores may only change prices, not move.
        moving_only (bool): Stores may only move, not change prices.
        mode (str): "store" for stores only, "chain" for chains mode.
        width (int): Number of patch columns in the world.
        height (int): Number of patch rows in the world.
        step_count (int): Number of ticks elapsed.
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
        width: int = 41,
        height: int = 41,
    ):
        self.layout: str = layout
        self.pricing_only: bool = rules == "pricing-only"
        self.moving_only: bool = rules == "moving-only"
        self.width: int = width
        self.height: int = height
        self.step_count: int = 0
        self._stable_tick_count: int = 0

        # Coordinate bounds centred at origin, matching NetLogo's -20..20 default.
        self._min_x: int = -(width // 2)
        self._max_x: int = width // 2
        self._min_y: int = -(height // 2)
        self._max_y: int = height // 2

        # Setup our consumers, stores, and market agents.
        self.consumers: List["Consumer"] = self._setup_consumers()
        self.stores: List["Store"] = self._setup_stores(number_of_stores)
        self.agents: List["MarketAgent"] = self._setup_agents(mode, number_of_chains)

        # Snapshot of each agent's position and price for equilibrium tracking,
        # mirroring NetLogo's prev-xcor / prev-ycor / prev-price turtle variables.
        self._prev_state: Dict[int, Tuple[Tuple[int, int], int]] = {
            a._id: (a.position, a.price) for a in self.stores
        }

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
            stores.append(Store(agent_id=i, area_count=0, position=pos, price=10))

        return stores

    def _setup_agents(self, mode: str, number_of_chains: int) -> List["MarketAgent"]:
        """Setup market agents for running the simulation.

        Args:
            mode (str): Mode that the simulation is running in.
            number_of_chains (int): Number of chains to include in simulation.

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

            # Partition stores into nearly equal groups.
            for i in range(number_of_chains):
                agents.append(Chain(
                    agent_id=-i,
                    area_count=0,
                    stores=self.stores[i::number_of_chains]
                ))

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
        for agent in self.stores:
            agent._area_count = 0

        # Update consumer preferred store, and area count.
        for consumer in self.consumers:
            consumer.choose_store(self.stores)._area_count += 1

    def calculate_hypothetical_market_share(
        self,
        store_id: int,
        hypothetical_pos: Tuple[int, int],
        hypothetical_price: int,
    ) -> int:
        """Calculates the hypothetical market share for an agent with a given position
        and price with all other agents unchanged.

        Mirrors Netlogo's 'potential-market-share' and 'market-share-if-moveto'
        procedures together.

        Args:
            store_id (int): The ID of the agent.
            hypothetical_pos (Tuple[int, int]): Hypothetical position of the agent.
            hypothetical_price (Tuple[int, int]): Hypothetical price of the agent.

        Returns:
            Integer representing the hypothetical market share for the provided
            agent, position, and price.
        """

        # Find agent with given id.
        my_store = None
        for store in self.stores:
            if store._id == store_id:
                my_store = store
                break
        assert my_store is not None

        # Move agent to hypothetical position and price.
        current_position: Tuple[int, int] = my_store.position
        my_store.position = hypothetical_pos
        current_price: int = my_store.price
        my_store.price = hypothetical_price

        # Consumers evaluate market share.
        hypothetical_market_share: int = 0
        for consumer in self.consumers:
            if consumer.choose_store(self.stores) == my_store:
                hypothetical_market_share += 1

        # Move back to current position and price.
        my_store.position = current_position
        my_store.price = current_price

        return hypothetical_market_share

    # EQUILIBRIUM TRACKING _____________________________________________________________

    def _update_equilibrium_check(self):
        """Checks if simulation remains in an equilibrium.

        Mirrors NetLogo's 'update-equilibrium-check'.

        Assumptions:
            A tick is considered unstable if the agent's position or price has changed
            by more than 1 unit.
        """
        stable = True
        for agent in self.stores:
            prev_pos, prev_price = self._prev_state[agent._id]
            if abs(agent.position[0] - prev_pos[0]) > 1:
                stable = False
            if abs(agent.position[1] - prev_pos[1]) > 1:
                stable = False
            if abs(agent.price - prev_price) > 1:
                stable = False
            self._prev_state[agent._id] = (agent.position, agent.price)
        self._stable_tick_count = self._stable_tick_count + 1 if stable else 0

    def at_equilibrium(self) -> bool:
        """Returns True when the simulation has been stable for 10 consecutive ticks."""
        return self._stable_tick_count >= 10

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
                5. The equilibrium counter is updated.
                6. Tick the simulation.
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

        # Step 5: Equilibrium counter is updated.
        self._update_equilibrium_check()

        # Step 6: Tick simulation.
        self.step_count += 1


if __name__ == "__main__":
    sim = Simulation(
        number_of_stores=3, layout="plane", rules="normal"
    )  # set up for expermiening
    for _ in range(100):
        sim.step()
    print(f"Steps run: {sim.step_count}")
    print(f"Stores: {[(a.position, a.price) for a in sim.stores]}")
