from __future__ import annotations

from dataclasses import dataclass

from .config import (
    ACTIONS,
    ACTION_EFFECTS,
    BACKGROUND_DRIFT,
    DAY_LENGTH_MINUTES,
    DAY_PHASE_MINUTES,
    DEATH_CONDITIONS,
    STATE_BOUNDS,
    STATE_VARIABLES,
)
from .state import State


@dataclass
class Transition:
    """
    One observed environment transition.

        S_t --A_t--> S_{t+1}
    """

    state_before: dict
    action: str
    state_after: dict
    day: int
    phase: str
    time_minutes: float

    def as_dict(self) -> dict:
        return {
            "state_before": self.state_before,
            "action": self.action,
            "state_after": self.state_after,
            "day": self.day,
            "phase": self.phase,
            "time_minutes": self.time_minutes,
        }


class SurvivalEnvironment:
    """
    Layer 1 — Environment.

    Responsibilities:
        - maintain state
        - execute actions
        - apply action consequences
        - advance logical time
        - determine alive/dead
        - expose the observed transition

    It does NOT:
        - choose actions
        - query knowledge
        - calculate LR
        - calculate confidence
        - implement agent policy
    """

    def __init__(
        self,
        initial_state: State | None = None,
    ) -> None:

        self.state = (
            initial_state.copy()
            if initial_state is not None
            else State()
        )

        self.time_minutes = 0.0
        self.step_count = 0

    # ============================================================
    # State helpers
    # ============================================================

    @staticmethod
    def clamp(
        variable: str,
        value: float,
    ) -> float:

        lower, upper = STATE_BOUNDS[
            variable
        ]

        return max(
            lower,
            min(
                upper,
                value,
            ),
        )

    def apply_delta(
        self,
        delta: dict,
    ) -> None:

        for variable in STATE_VARIABLES:

            current = float(
                getattr(
                    self.state,
                    variable,
                )
            )

            change = float(
                delta.get(
                    variable,
                    0.0,
                )
            )

            updated = (
                current
                + change
            )

            updated = self.clamp(
                variable,
                updated,
            )

            setattr(
                self.state,
                variable,
                updated,
            )

    # ============================================================
    # Logical time
    # ============================================================

    @property
    def day(self) -> int:
        return (
            int(
                self.time_minutes
                // DAY_LENGTH_MINUTES
            )
            + 1
        )

    @property
    def phase(self) -> str:

        minute_in_day = (
            self.time_minutes
            % DAY_LENGTH_MINUTES
        )

        if (
            minute_in_day
            < DAY_PHASE_MINUTES
        ):
            return "day"

        return "night"

    # ============================================================
    # Action registry
    # ============================================================

    @property
    def available_actions(
        self,
    ) -> tuple[str, ...]:
        return ACTIONS

    # ============================================================
    # Lifecycle
    # ============================================================

    @property
    def alive(self) -> bool:
        return self.state.alive

    def reset(
        self,
        state: State | None = None,
    ) -> State:

        self.state = (
            state.copy()
            if state is not None
            else State()
        )

        self.time_minutes = 0.0
        self.step_count = 0

        return self.state.copy()

    # ============================================================
    # Environment transition
    # ============================================================

    def step(
        self,
        action: str,
    ) -> Transition:

        if action not in self.available_actions:

            raise ValueError(
                f"Unknown action: {action!r}. "
                f"Available actions: "
                f"{self.available_actions}"
            )

        state_before = (
            self.state.copy()
        )

        # --------------------------------------------------------
        # 1. Action consequence
        # --------------------------------------------------------

        self.apply_delta(
            ACTION_EFFECTS[action]
        )

        # --------------------------------------------------------
        # 2. Background environment dynamics
        # --------------------------------------------------------

        self.apply_delta(
            BACKGROUND_DRIFT
        )

        # --------------------------------------------------------
        # 3. Advance logical time
        # --------------------------------------------------------

        self.time_minutes += 1.0
        self.step_count += 1

        # --------------------------------------------------------
        # 4. Update lifecycle
        # --------------------------------------------------------

        self.update_lifecycle()

        # --------------------------------------------------------
        # 5. Return observed transition
        # --------------------------------------------------------

        return Transition(
            state_before=
                state_before.as_dict(),

            action=action,

            state_after=
                self.state.as_dict(),

            day=self.day,

            phase=self.phase,

            time_minutes=
                self.time_minutes,
        )

    # ============================================================
    # Lifecycle / terminal state
    # ============================================================

    def update_lifecycle(
        self,
    ) -> None:

        if (
            self.state.hunger
            >= DEATH_CONDITIONS[
                "hunger_max"
            ]
        ):

            self.state.alive = False
            return

        if (
            self.state.thirst
            >= DEATH_CONDITIONS[
                "thirst_max"
            ]
        ):

            self.state.alive = False
            return

        if (
            self.state.energy
            <= DEATH_CONDITIONS[
                "energy_min"
            ]
        ):

            self.state.alive = False
            return

        self.state.alive = True

    # ============================================================
    # Observation
    # ============================================================

    def observe(self) -> dict:

        return {
            "state":
                self.state.as_dict(),

            "day":
                self.day,

            "phase":
                self.phase,

            "time_minutes":
                self.time_minutes,

            "step_count":
                self.step_count,

            "alive":
                self.state.alive,

            "available_actions":
                list(
                    self.available_actions
                ),
        }