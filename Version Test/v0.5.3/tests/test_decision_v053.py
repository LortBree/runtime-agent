from layer3_entity.decision import (
    DecisionEngine,
)


engine = DecisionEngine(
    action_order=[
        "eat",
        "drink",
        "sleep",
        "work",
        "idle",
    ]
)


# ================================================================
# SATURATED NO-POSITIVE CASE
# ================================================================
#
# Semua relation sudah mature, sehingga novelty <= 0.25.
#
# sleep:
#   harm = 0
#
# work:
#   harm > 0
#
# eat:
#   harm > 0
#
# Expected:
#   saturated → neutral
#   least-harm → sleep
#
# NOTE:
# This case intentionally verifies semantics, not "avoid sleep".
# If sleep is actually least harmful, sleep SHOULD win.
# ================================================================

state = {
    "hunger": 20.0,
    "thirst": 20.0,
    "energy": 80.0,
    "curiosity": 80.0,
}

mature = {
    "confidence": 0.95,
    "support": 20.0,
    "contradiction": 0.0,
    "total_evidence": 20.0,
}

knowledge = {
    "eat": {
        "action_known": True,
        "effects": [
            {
                **mature,
                "variable": "hunger",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "thirst",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "energy",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
            {
                **mature,
                "variable": "curiosity",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
        ],
    },

    "drink": {
        "action_known": True,
        "effects": [
            {
                **mature,
                "variable": "hunger",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "thirst",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "energy",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
            {
                **mature,
                "variable": "curiosity",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
        ],
    },

    "sleep": {
        "action_known": True,
        "effects": [
            {
                **mature,
                "variable": "hunger",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "thirst",
                "known": True,
                "magnitude": "INC_SMALL",
            },
            {
                **mature,
                "variable": "energy",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
            {
                **mature,
                "variable": "curiosity",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
        ],
    },

    "work": {
        "action_known": True,
        "effects": [
            {
                **mature,
                "variable": "hunger",
                "known": True,
                "magnitude": "INC_LARGE",
            },
            {
                **mature,
                "variable": "thirst",
                "known": True,
                "magnitude": "INC_LARGE",
            },
            {
                **mature,
                "variable": "energy",
                "known": True,
                "magnitude": "DEC_LARGE",
            },
            {
                **mature,
                "variable": "curiosity",
                "known": True,
                "magnitude": "DEC_SMALL",
            },
        ],
    },

    "idle": {
        "action_known": True,
        "effects": [
            {
                **mature,
                "variable": "hunger",
                "known": True,
                "magnitude": "NONE",
            },
            {
                **mature,
                "variable": "thirst",
                "known": True,
                "magnitude": "NONE",
            },
            {
                **mature,
                "variable": "energy",
                "known": True,
                "magnitude": "NONE",
            },
            {
                **mature,
                "variable": "curiosity",
                "known": True,
                "magnitude": "NONE",
            },
        ],
    },
}


# ================================================================
# DECISION
# ================================================================

result = engine.select_action(
    state=state,
    knowledge=knowledge,
)


print(
    f"Selected : {result.action}"
)

print(
    f"Mode     : {result.mode}"
)

print(
    f"Score    : {result.score}"
)

print(
    f"Reason   : {result.reason}"
)

print()

for evaluation in result.evaluations:

    print(
        f"{evaluation.action:<7} "
        f"score={evaluation.score:7.3f} "
        f"harm={evaluation.harm_score:7.3f} "
        f"confidence={evaluation.confidence_mean:.3f}"
    )


assert (
    result.mode == "neutral"
)

assert (
    result.action == "idle"
)

assert (
    result.score == 0.0
)

print()
print("PASS")