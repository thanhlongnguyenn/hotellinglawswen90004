from typing import List

from market_agent import MarketAgent
from simulation import Simulation
from store import Store

class Chain(MarketAgent):
    """
    Concrete composite of Stores to define group behaviour.
    """

    def __init__(self, agent_id: int, area_count: int, stores: List[Store]):
        super().__init__(agent_id, area_count)

        self.controlled_stores: List[Store] = []

    def evaluate_move(self, sim: Simulation):
        # TODO: Implement chain-level movement strategy
        return

    def evaluate_price(self, sim: Simulation):
        # TODO: Implement chain-level pricing strategy
        return

    def apply_update(self):
        # TODO: Apply updates across the chain
        return
