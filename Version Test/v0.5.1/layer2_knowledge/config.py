from __future__ import annotations


# ================================================================
# LAYER 2 — KNOWLEDGE CONFIGURATION
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
# STATE BUCKETING
# ================================================================
#
# V0.5 proposal:
#   LOW / HIGH
#
# The proposal states that the threshold is determined during a
# calibration phase and then frozen before the main experiment.
#
# For the initial simulator we use 50.0 as a temporary calibration
# value. Once the calibration phase is formalized, change only these
# thresholds.
# ================================================================

STATE_BUCKET_THRESHOLDS = {
    "hunger": 50.0,
    "thirst": 50.0,
    "energy": 50.0,
    "curiosity": 50.0,
}


# ================================================================
# EFFECT BUCKETS
# ================================================================
#
# Five categories:
#
#   DEC_LARGE
#   DEC_SMALL
#   NONE
#   INC_SMALL
#   INC_LARGE
#
# The proposal says delta_1 and delta_2 should be determined by
# calibration and frozen before the main experiment.
#
# Temporary initial values for the current simulator:
#
#   |delta| < 1  -> NONE
#   1 <= |delta| < 10 -> SMALL
#   |delta| >= 10 -> LARGE
# ================================================================

DELTA_SMALL = 1.0
DELTA_LARGE = 10.0


# ================================================================
# LR UPDATE
# ================================================================

DECAY_GAMMA = 0.95

# Laplace smoothing parameter.
ALPHA = 1.0


# ================================================================
# SEMANTIC CONFIDENCE
# ================================================================

UNKNOWN_THRESHOLD = 0.60
SHOULD_THRESHOLD = 0.80


# ================================================================
# PERSISTENCE
# ================================================================

DEFAULT_KNOWLEDGE_PATH = "knowledge.json"