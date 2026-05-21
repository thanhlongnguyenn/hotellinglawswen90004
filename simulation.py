import random
from typing import TYPE_CHECKING, Dict, List, Literal, Tuple
import log_utils

if TYPE_CHECKING:
    from consumer import Consumer
    from store import Store


class Simulation:
    """
    High-level orchestrator replicating the NetLogo Hotelling's Law observer.

    Manages a grid of Consumer patches and a collection of MarketAgents (Stores
    or Chains), advancing the simulation one tick at a time via `step`.

    Attributes:
        layout (str): "plane" for 2-D grid, "line" for 1-D column (pxcor=0).
        pricing_only (bool): Stores may only change prices, not move.
        moving_only (bool): Stores may only move, not change prices.
        width (int): Number of patch columns in the world.
        height (int): Number of patch rows in the world.
        step_count (int): Number of ticks elapsed.
        consumers (List["Consumer"]): All consumer patches.
        agents (List["MarketAgent"]): All competing market agents.
    """

    def __init__(
        self,
        number_of_stores: int = 3,
        layout: Literal["plane", "line"] = "plane",
        rules: Literal["normal", "moving-only", "pricing-only"] = "normal",
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

        self.consumers: List["Consumer"] = self._setup_consumers()
        self.agents: List["Store"] = self._setup_stores(number_of_stores)

        # Snapshot of each agent's position and price for equilibrium tracking,
        # mirroring NetLogo's prev-xcor / prev-ycor / prev-price turtle variables.
        self._prev_state: Dict[int, Tuple[Tuple[int, int], int]] = {
            a._id: (a.position, a.price) for a in self.agents
        }

        self._recalculate_area()

    # SETUP ___________________________________________________________________

    def _setup_consumers(self) -> List["Consumer"]:
        from consumer import Consumer

        if self.layout == "line":
            return [Consumer((0, y)) for y in range(self._min_y, self._max_y + 1)]
        return [
            Consumer((x, y))
            for x in range(self._min_x, self._max_x + 1)
            for y in range(self._min_y, self._max_y + 1)
        ]

    def _setup_stores(self, number_of_stores: int) -> List["Store"]:
        from store import Store

        positions = random.sample(
            [c.position for c in self.consumers], number_of_stores
        )
        return [
            Store(agent_id=i, area_count=0, position=pos, price=10)
            for i, pos in enumerate(positions)
        ]

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
        for agent in self.agents:
            agent._area_count = 0

        # Update consumer preferred store, and area count.
        for consumer in self.consumers:
            consumer.choose_store(self.agents)._area_count += 1

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
        specified_agent = None
        for agent in self.agents:
            if agent._id == store_id:
                specified_agent = agent
                break
        assert specified_agent is not None

        # Move agent to hypothetical position and price.
        current_position: Tuple[int, int] = specified_agent.position
        specified_agent.position = hypothetical_pos
        current_price: int = specified_agent.price
        specified_agent.price = hypothetical_price

        # Consumers evaluate market share.
        hypothetical_market_share: int = 0
        for consumer in self.consumers:
            if consumer.choose_store(self.agents) == specified_agent:
                hypothetical_market_share += 1

        # Move back to current position and price.
        specified_agent.position = current_position
        specified_agent.price = current_price

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
        for agent in self.agents:
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

    def export_state(self) -> Dict:
        """Export the state of the simulation.

        Returns:
            Dict: A dictionary containing the current state of the simulation.
        """
        store_positions: list[list[int]] = []
        store_prices: list[list[int]] = []
        store_market_share: list[list[int]] = []

        # Flatten store state
        for s in self.agents:
            store_positions.append([s._id, s.position[0], s.position[1]])
            store_prices.append([s._id, s.price])
            store_market_share.append(
                [
                    s._id,
                    self.calculate_hypothetical_market_share(
                        s._id, s.position, s.price
                    ),
                ]
            )

        return {
            "step": self.step_count,
            "store-positions": store_positions,
            "store-market-shares": store_market_share,
            "store-prices": store_prices,
        }


def run_simulation_experiment(params):
    """Simulation test case runner.

    Args:
        params (Tuple): Parameters to execution a simulation with.

    Returns:
        List[str]: Simulation results.
    """

    run_id, max_ticks, num_store, rule, layout = params

    # Build simulation environment.
    sim = Simulation(
        number_of_stores=num_store,
        rules=rule,
        layout=layout,
    )

    # Execute test iteration.
    for _ in range(max_ticks):
        sim.step()
    print(f"Completed: Num stores: {num_store}, Layout: {layout}, Rule: {rule}")

    # Build results.
    state: dict = sim.export_state()
    results = [
        run_id,
        layout,
        num_store,
        rule,
        state["step"],
        log_utils.serialise_list(state["store-positions"]),
        log_utils.serialise_list(state["store-market-shares"]),
        log_utils.serialise_list(state["store-prices"]),
    ]
    return results
