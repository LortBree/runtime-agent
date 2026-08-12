# ================================================================
# LAYER 1 — ENVIRONMENT CONFIGURATION
# ================================================================

ACTIONS = (
    "eat",
    "drink",
    "sleep",
    "work",
    "idle",
)

STATE_VARIABLES = (
    "hunger",
    "thirst",
    "energy",
    "curiosity",
)


# ================================================================
# STATE BOUNDS
# ================================================================

STATE_BOUNDS = {
    "hunger": (0.0, 100.0),
    "thirst": (0.0, 100.0),
    "energy": (0.0, 100.0),
    "curiosity": (0.0, 100.0),
}


# ================================================================
# LOGICAL TIME
# ================================================================
#
# Proposal:
#   1 simulated day = 5 minutes
#   day phase = 3 minutes
#   night phase = 2 minutes
#
# Environment uses logical time, not wall-clock sleep().
# ================================================================

DAY_LENGTH_MINUTES = 5.0
DAY_PHASE_MINUTES = 3.0
NIGHT_PHASE_MINUTES = 2.0


# ================================================================
# ACTION EFFECTS
# ================================================================
#
# These preserve the working V0.5.x simulator coefficients.
#
# They are environment dynamics, not agent policy.
# ================================================================

ACTION_EFFECTS = {
    "eat": {
        "hunger": -28.0,
        "thirst": 0.0,
        "energy": 0.0,
        "curiosity": 0.5,
    },

    "drink": {
        "hunger": 0.0,
        "thirst": -30.0,
        "energy": 0.0,
        "curiosity": 0.0,
    },

    "sleep": {
        "hunger": 0.0,
        "thirst": 0.0,
        "energy": 20.0,
        "curiosity": -0.5,
    },

    "work": {
        "hunger": 4.0,
        "thirst": 5.0,
        "energy": -10.0,
        "curiosity": 3.0,
    },

    "idle": {
        "hunger": 2.0,
        "thirst": 2.5,
        "energy": -1.5,
        "curiosity": -0.5,
    },
}


# ================================================================
# BACKGROUND DRIFT
# ================================================================
#
# Kept separate so environment-wide dynamics can later be changed
# without modifying individual action effects.
# ================================================================

BACKGROUND_DRIFT = {
    "hunger": 0.0,
    "thirst": 0.0,
    "energy": 0.0,
    "curiosity": 0.0,
}


# ================================================================
# TERMINAL CONDITIONS
# ================================================================

DEATH_CONDITIONS = {
    "hunger_max": 100.0,
    "thirst_max": 100.0,
    "energy_min": 0.0,
}