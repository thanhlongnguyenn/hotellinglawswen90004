import random
from typing import Tuple

from market_agent import MarketAgent
from simulation import Simulation

class Store(MarketAgent):
    """
    Concrete class to replicate NetLogo store "turtles".

    Attributes:
        position (Tuple[int, int]): The (x, y) coordinates of the store's location.
        price (int): The current price the store charges.
        next_position (Tuple[int, int]): The buffered position the store will move to.
        next_price (int): The buffered price the store will charge.
    """

    def __init__(self, agent_id: int, position: Tuple[int, int],
        price: int):
        """
        Initialises the Store with a unique identifier and initial position and price.
        
        Args:
            agent_id (int): Unique identifier for the Store.
            position (Tuple[int, int]): The (x, y) coordinates of the store's location.
            price (int): The initial price the store charges.
        """

        super().__init__(agent_id)
        
        self.position: Tuple[int, int] = position
        self.price: int = price
        self.next_position: Tuple[int, int] = position
        self.next_price: int = price

    def evaluate_move(self, sim: Simulation):
        """
        Considers a unit step in 4 cardinal directions on valid consumer patches
        and caches the one with the highest hypothetical market share.
        """

        x, y = self.position
        cardinal_moves = [(x, y+1), (x, y-1), (x+1, y), (x-1, y)]
        
        # Filter neighbors to ensure they are within valid consumer coordinates
        possible_moves = [
            move for move in cardinal_moves if sim.is_valid_consumer_position(move)
        ]

        random.shuffle(possible_moves) # Shuffle to prevent bias for tie-breaks

        # If we have market share, the status quo is favored in case of ties
        if self._area_count > 0:
            possible_moves.insert(0, self.position)  

        best_move = self.position
        max_market_share = -1

        # Evaluate each move hypothetically
        for move in possible_moves:
            hypothetical_share = sim.calculate_hypothetical_market_share(
                store_id=self._id,
                hypothetical_changes=[(self._id, move, self.price)]
            )

            if hypothetical_share > max_market_share:
                max_market_share = hypothetical_share
                best_move = move

        self.next_position = best_move

    def evaluate_price(self, sim: Simulation):
        """
        Evaluates changing price by -1 or +1 and caches the price that maximises
        revenue.
        """

        # Status quo is placed first to win ties. Shuffle others to have equal chances.
        alternatives = [self.price - 1, self.price + 1]
        random.shuffle(alternatives)
        possible_prices = [self.price] + alternatives

        best_price = self.price
        max_revenue = -1
        all_zeros = True

        for target_price in possible_prices:
            hypothetical_share = sim.calculate_hypothetical_market_share(
                store_id=self._id,
                hypothetical_changes=[(self._id, self.position, target_price)]
            )
            revenue = hypothetical_share * target_price
            
            if revenue > 0:
                all_zeros = False

            if revenue > max_revenue:
                max_revenue = revenue
                best_price = target_price

        # If all potential revenues are zero, the store lowers its price (if it can)
        if all_zeros and self.price > 1:
            self.next_price = self.price - 1
        else:
            self.next_price = best_price

    def apply_update(self):
        """Updates the store's position and price simultaneously."""
        self.position = self.next_position
        self.price = self.next_price
