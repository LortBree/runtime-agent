from __future__ import annotations

from enum import Enum

from .config import (
    DELTA_LARGE,
    DELTA_SMALL,
    STATE_BUCKET_THRESHOLDS,
)


# ================================================================
# STATE BUCKET
# ================================================================

class StateBucket(str, Enum):
    LOW = "LOW"
    HIGH = "HIGH"


# ================================================================
# EFFECT MAGNITUDE
# ================================================================

class EffectMagnitude(str, Enum):
    DEC_LARGE = "DEC_LARGE"
    DEC_SMALL = "DEC_SMALL"
    NONE = "NONE"
    INC_SMALL = "INC_SMALL"
    INC_LARGE = "INC_LARGE"


# ================================================================
# STATE BUCKETING
# ================================================================

def bucket_state_variable(
    variable: str,
    value: float,
) -> StateBucket:

    if variable not in STATE_BUCKET_THRESHOLDS:
        raise ValueError(
            f"Unknown state variable: {variable!r}"
        )

    threshold = (
        STATE_BUCKET_THRESHOLDS[
            variable
        ]
    )

    if value < threshold:
        return StateBucket.LOW

    return StateBucket.HIGH


def bucket_state(
    state: dict,
) -> tuple[str, ...]:
    """
    Convert:

        Hunger
        Thirst
        Energy
        Curiosity

    into a deterministic LOW/HIGH tuple.
    """

    return (
        bucket_state_variable(
            "hunger",
            float(state["hunger"]),
        ).value,

        bucket_state_variable(
            "thirst",
            float(state["thirst"]),
        ).value,

        bucket_state_variable(
            "energy",
            float(state["energy"]),
        ).value,

        bucket_state_variable(
            "curiosity",
            float(state["curiosity"]),
        ).value,
    )


# ================================================================
# EFFECT BUCKETING
# ================================================================

def bucket_effect(
    delta: float,
) -> EffectMagnitude:

    if delta <= -DELTA_LARGE:
        return EffectMagnitude.DEC_LARGE

    if delta <= -DELTA_SMALL:
        return EffectMagnitude.DEC_SMALL

    if delta < DELTA_SMALL:
        return EffectMagnitude.NONE

    if delta < DELTA_LARGE:
        return EffectMagnitude.INC_SMALL

    return EffectMagnitude.INC_LARGE