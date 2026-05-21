import math
import random
from typing import Dict, List, Literal, Tuple

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
        width (int): Number of patch columns in the world.
        height (int): Number of patch rows in the world.
        step_count (int): Number of ticks elapsed.
        consumers (List[Consumer]): All consumer patches.
        agents (List[MarketAgent]): All competing market agents.
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
        self.tick: int = 0
        self._stable_tick_count: int = 0

        # Coordinate bounds centred at origin, matching NetLogo's -20..20 default.
        self._min_x: int = -(width // 2)
        self._max_x: int = width // 2
        self._min_y: int = -(height // 2)
        self._max_y: int = height // 2

        self.consumers: List["Consumer"] = self._setup_consumers()
        self.agents: List[Store] = self._setup_stores(number_of_stores)

        # Snapshot of each agent's position and price for equilibrium tracking,
        # mirroring NetLogo's prev-xcor / prev-ycor / prev-price turtle variables.
        self._prev_state: Dict[int, Tuple[Tuple[int, int], int]] = {
            a._id: (a.position, a.price) for a in self.agents
        }

        self._recalculate_area()

    # SETUP ___________________________________________________________________

    def _setup_consumers(self) -> List["Consumer"]:
        if self.layout == "line":
            return [Consumer((0, y)) for y in range(self._min_y, self._max_y + 1)]
        return [
            Consumer((x, y))
            for x in range(self._min_x, self._max_x + 1)
            for y in range(self._min_y, self._max_y + 1)
        ]

    def _setup_stores(self, number_of_stores: int) -> List[Store]:
        positions = random.sample(
            [c.position for c in self.consumers], number_of_stores
        )
        return [
            Store(agent_id=i, area_count=0, position=pos, price=10)
            for i, pos in enumerate(positions)
        ]

    # ------------------------------------------------------- consumer queries

    def is_valid_consumer_position(self, position: Tuple[int, int]) -> bool:
        """Returns True if *position* falls on a consumer patch."""
        x, y = position
        if self.layout == "line":
            return x == 0 and self._min_y <= y <= self._max_y
        return self._min_x <= x <= self._max_x and self._min_y <= y <= self._max_y

    # MARKET SHARE LOGIC _______________________________________________________________

    def _recalculate_area(self) -> None:
        """Assigns every consumer to its preferred agent and refreshes area counts.

        Mirrors Netlogo's 'recalculate-area' procedure.
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
        """Returns the market share *store_id* would receive if it occupied
        *hypothetical_pos* at *hypothetical_price*, with all other agents
        unchanged.

        Mirrors NetLogo's potential-market-share / market-share-if-move-to.
        """
        count = 0
        for consumer in self.consumers:
            best_deal = float("inf")
            best_ids: List[int] = []
            for agent in self.agents:
                pos = hypothetical_pos if agent._id == store_id else agent.position
                price = hypothetical_price if agent._id == store_id else agent.price
                deal = math.dist(pos, consumer.position) + price
                if deal < best_deal:
                    best_deal = deal
                    best_ids = [agent._id]
                elif deal == best_deal:
                    best_ids.append(agent._id)
            if random.choice(best_ids) == store_id:
                count += 1
        return count

    # ---------------------------------------------------- equilibrium tracking

    def _update_equilibrium_check(self):
        """Increments or resets the stable-tick counter.

        Mirrors NetLogo's update-equilibrium-check: a tick is considered stable
        unless any agent changed position or price by more than 1 unit.
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
        self.tick += 1


if __name__ == "__main__":
    sim = Simulation(
        number_of_stores=3, layout="plane", rules="normal"
    )  # set up for expermiening
    for _ in range(100):
        sim.step()
    print(f"Steps run: {sim.tick}")
    print(f"Agents: {[(a.position, a.price) for a in sim.agents]}")
