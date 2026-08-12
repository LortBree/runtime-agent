from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Experience:
    """
    Experience defined as:

        E_t = (S_t, A_t, S_{t+1})
    """

    state_before: dict
    action: str
    state_after: dict

    def as_dict(self) -> dict:
        return {
            "state_before": dict(
                self.state_before
            ),
            "action": self.action,
            "state_after": dict(
                self.state_after
            ),
        }