import itertools
import random
from typing import List, Tuple

from market_agent import MarketAgent
from simulation import Simulation
from store import Store

class Chain(MarketAgent):
    """
    Concrete composite of Stores to define group behaviour. Coordinates
    movements and pricing strategies collectively to maximise chain outcomes.
    """

    def __init__(self, agent_id: int, stores: List[Store]):
        super().__init__(agent_id)

        self.controlled_stores: List[Store] = stores

    @property
    def _area_count(self) -> int:
        """Dynamically aggregate market share from controlled stores."""
        return sum(store._area_count for store in self.controlled_stores)

    def evaluate_move(self, sim: Simulation):
        """
        Evaluates all joint combinations of moves for all controlled stores.
        Selects the combination that maximises the chain's overall market share.
        """
        if not self.controlled_stores:
            return

        # Generate lists of valid individual moves for every single store
        stores_possible_moves: List[List[Tuple[int, int]]] = []
        
        for store in self.controlled_stores:
            x, y = store.position
            cardinal_moves = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
            possible_moves = [
                move for move in cardinal_moves if sim.is_valid_consumer_position(move)
            ]
            
            if store._area_count > 0:
                possible_moves.insert(0, store.position)
                
            stores_possible_moves.append(possible_moves)

        # Generate all combinations of moves
        joint_move_combinations = list(itertools.product(*stores_possible_moves))

        # Place status quo at the start and shuffle the rest to prevent bias for ties
        status_quo_move = joint_move_combinations[0]
        other_moves = joint_move_combinations[1:]
        random.shuffle(other_moves)
        joint_move_combinations = [status_quo_move] + other_moves

        best_joint_move = None
        max_chain_market_share = -1

        # Evaluate each combination of moves
        for joint_move in joint_move_combinations:
            hypothetical_changes = []
            for i, store in enumerate(self.controlled_stores):
                hypothetical_changes.append((store._id, joint_move[i], store.price))

            total_chain_share = 0
            for store in self.controlled_stores:
                total_chain_share += sim.calculate_hypothetical_market_share(
                    store_id=store._id,
                    hypothetical_changes=hypothetical_changes
                )

            if total_chain_share > max_chain_market_share:
                max_chain_market_share = total_chain_share
                best_joint_move = joint_move

        # Cache the best move in each store
        if best_joint_move:
            for i, store in enumerate(self.controlled_stores):
                store.next_position = best_joint_move[i]

    def evaluate_price(self, sim: Simulation):
        """
        Evaluates all joint combinations of price changes (-1, 0, +1) for all
        controlled stores. Selects the combination that maximises the chain's
        overall revenue.
        """
        if not self.controlled_stores:
            return

        # Generate lists of valid individual prices for every single store
        stores_possible_prices: List[List[int]] = []
        
        for store in self.controlled_stores:
            stores_possible_prices.append([
                store.price,
                store.price - 1,
                store.price + 1
            ])

        # Generate all combinations of prices
        joint_price_combinations = list(itertools.product(*stores_possible_prices))

        # Place status quo at the start and shuffle the rest to prevent bias for ties
        status_quo_price = joint_price_combinations[0]
        other_prices = joint_price_combinations[1:]
        random.shuffle(other_prices)
        joint_price_combinations = [status_quo_price] + other_prices

        best_joint_price = None
        max_chain_revenue = -1
        all_combinations_zero_revenue = True

        # Evaluate each combination of price changes
        for joint_price in joint_price_combinations:
            hypothetical_changes = []
            for i, store in enumerate(self.controlled_stores):
                hypothetical_changes.append((store._id, store.position, joint_price[i]))

            # Calculate individual contributions within combination
            total_chain_revenue = 0
            current_combination_has_revenue = False
            
            for i, store in enumerate(self.controlled_stores):
                individual_share = sim.calculate_hypothetical_market_share(
                    store_id=store._id,
                    hypothetical_changes=hypothetical_changes
                )
                
                revenue = individual_share * joint_price[i]
                if revenue > 0:
                    current_combination_has_revenue = True
                total_chain_revenue += revenue

            if current_combination_has_revenue:
                all_combinations_zero_revenue = False

            if total_chain_revenue > max_chain_revenue:
                max_chain_revenue = total_chain_revenue
                best_joint_price = joint_price

        # Cache the best price or apply emergency procedure if all configurations fail
        if all_combinations_zero_revenue:
            for store in self.controlled_stores:
                if store.price > 1:
                    store.next_price = store.price - 1
                else:
                    store.next_price = store.price
        else:
            if best_joint_price:
                for i, store in enumerate(self.controlled_stores):
                    store.next_price = best_joint_price[i]

    def apply_update(self):
        """
        Applies updates across the entire chain simultaneously.
        """
        for store in self.controlled_stores:
            store.apply_update()
