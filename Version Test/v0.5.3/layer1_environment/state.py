from __future__ import annotations

from dataclasses import dataclass


@dataclass
class State:
    """
    Layer 1 state representation.

    State variables:
        hunger
        thirst
        energy
        curiosity

    alive:
        lifecycle flag maintained by the environment.
    """

    hunger: float = 60.0
    thirst: float = 60.0
    energy: float = 60.0
    curiosity: float = 50.0
    alive: bool = True

    def copy(self) -> "State":
        return State(
            hunger=self.hunger,
            thirst=self.thirst,
            energy=self.energy,
            curiosity=self.curiosity,
            alive=self.alive,
        )

    def as_dict(self) -> dict:
        return {
            "hunger": float(self.hunger),
            "thirst": float(self.thirst),
            "energy": float(self.energy),
            "curiosity": float(self.curiosity),
            "alive": bool(self.alive),
        }