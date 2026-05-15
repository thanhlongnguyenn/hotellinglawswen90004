import math
import random


class Consumer:
    """
    Class that represents a consumer agent within the Hotelling's Law
    simulation framework.
    """

    def __init__(self, position_x: int, position_y: int):
        """Constructor for Consumer class.

        Args:
            position_x (int): Position of the consumer in the x-axis.
            position_y (int): Position of the consumer in the y-axis.
        """

        self.position: list[int] = [position_x, position_y]
        return None

    def choose_stores(self, stores: list[Store]) -> Store:
        """Consumer selects the store that has the best deal, defined as the smallest
        sum of price and distance.

        Assumption:
            For similarity to NetLogo implementation, distance is implemented as euclidean
                distance from centroid to centroid.
            For similarity to the Netlogo implementation, min-one-of is implemented as
                a random selection for the agents that report the lowest value.

        Args:
            stores (list[Store]): Stores that the consumer can choose from.

        Returns:
            Store that the consumer will consume from.
        """

        # Find stores with best deal.
        best_deal: float = (
            math.dist(stores[0].position, self.position) + stores[0].price
        )
        best_deal_stores: set[Store] = set(stores[0])
        for store in stores:
            deal: float = math.dist(store.position, self.position) + store.price

            if deal < best_deal:
                # New best deal found.
                best_deal = deal
                best_deal_stores = set(store)

            elif deal == best_deal:
                # Equal best deal found.
                best_deal_stores.add(store)

        # Select store to consume from.
        return random.choice(best_deal_stores)
