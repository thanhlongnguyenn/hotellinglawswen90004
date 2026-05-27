from abc import ABC, abstractmethod

from simulation import Simulation

class MarketAgent(ABC):
    """
    Abstract superclass to represent seller entities in the simulation "market".

    Attributes:
        _id (int): Unique identifier for the MarketAgent.
        _area_count (int): The number of consumer "patches" currently served by this
            agent, representing its market share.
    """

    _id: int
    _area_count: int

    def __init__(self, agent_id: int):
        """
        Initialises the MarketAgent with a unique identifier.

        Args:
            agent_id (int): Unique identifier for the MarketAgent.
        """
        self._id: int = agent_id

        # Only set if the class hasn't overridden it with a property descriptor
        if (not hasattr(type(self), '_area_count')
            or not isinstance(getattr(type(self), '_area_count'), property)):
            self._area_count: int = 0

    @abstractmethod
    def evaluate_move(self, sim: Simulation):
        """
        Determines (and internally caches) the optimal position the MarketAgent should
        move to (or remain at).

        Args:
            sim (Simulation): The current state of the simulation, providing necessary
                context for decision-making.
        """
        pass

    @abstractmethod
    def evaluate_price(self, sim: Simulation):
        """
        Determines (and internally caches) the optimal price the MarketAgent should
        charge.

        Args:
            sim (Simulation): The current state of the simulation, providing necessary
                context for decision-making.
        """
        pass

    @abstractmethod
    def apply_update(self):
        """Enacts the cached changes simultaneously."""
        pass
