from __future__ import annotations

import math
import random

from store import Store


class Consumer:
    """
    Class that represents a consumer agent within the Hotelling's Law
    simulation framework.
    """

    position: tuple[int, int]

    def __init__(self, position: tuple[int, int]):
        """Constructor for Consumer class.

        Args:
            position (tuple[int, int]): Position of the consumer.
        """

        self.position = position
        self.preferred_store = None

    def choose_store(self, stores: list[Store]) -> Store:
        """Consumer selects the store that has the best deal, defined as the smallest
        sum of price and distance.

        Mirrors NetLogo's 'choose-store' procedure.
        
        Assumption:
            For similarity to NetLogo implementation, distance is implemented as euclidean
                distance from centroid to centroid.
            For similarity to the Netlogo implementation, min-one-of is implemented as
                a random selection for the agents that report the lowest value.

        Args:
            stores (list[Store]): Stores that the consumer can choose from.
        
        Returns:
            Store instance that is preferred by the consumer.
        """

        # Find stores with best deal.
        best_deal: float = (
            math.dist(stores[0].position, self.position) + stores[0].price
        )
        best_deal_stores: list[Store] = [stores[0]]
        for store in stores:
            deal: float = math.dist(store.position, self.position) + store.price

            if deal < best_deal:
                # New best deal found.
                best_deal = deal
                best_deal_stores = [store]

            elif deal == best_deal:
                # Equal best deal found.
                best_deal_stores.append(store)

        # Select store to consume from.
        return random.choice(best_deal_stores)
