from layer3_entity.decision import (
    DecisionEngine,
)


def effects(**relations):
    return [
        {
            "variable": variable,
            "magnitude": magnitude,
            "confidence": confidence,
            "known": True,
        }
        for variable, (
            magnitude,
            confidence,
        ) in relations.items()
    ]


def run_case(
    title,
    state,
    knowledge,
    expected_action,
    expected_mode="exploit",
):
    engine = DecisionEngine()

    result = engine.select_action(
        state=state,
        knowledge=knowledge,
        explore_unknown=True,
    )

    print("=" * 72)
    print(title)
    print("=" * 72)

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

    for evaluation in (
        result.evaluations
    ):

        print(
            f"{evaluation.action:<7} "
            f"score={evaluation.score:7.3f} "
            f"confidence="
            f"{evaluation.confidence_mean:.3f} "
            f"known="
            f"{evaluation.known_variables} "
            f"unknown="
            f"{evaluation.unknown_variables}"
        )

    assert (
        result.action
        == expected_action
    ), (
        f"Expected action "
        f"{expected_action!r}, "
        f"got "
        f"{result.action!r}"
    )

    assert (
        result.mode
        == expected_mode
    ), (
        f"Expected mode "
        f"{expected_mode!r}, "
        f"got "
        f"{result.mode!r}"
    )

    print("PASS")
    print()


# ================================================================
# CASE 1
# HIGH HUNGER / HIGH ENERGY
#
# eat:
#     hunger DEC_LARGE
#
# sleep:
#     energy INC_LARGE
#     hunger INC_SMALL
#
# Hunger is urgent; eat should win.
# ================================================================

run_case(
    title=
        "CASE 1 — HIGH hunger / HIGH energy",

    state={
        "hunger": 80.0,
        "thirst": 40.0,
        "energy": 80.0,
        "curiosity": 50.0,
    },

    knowledge={
        "eat": {
            "known": True,
            "effects": effects(
                hunger=(
                    "DEC_LARGE",
                    0.84,
                ),
            ),
        },

        "sleep": {
            "known": True,
            "effects": effects(
                energy=(
                    "INC_LARGE",
                    0.84,
                ),
                hunger=(
                    "INC_SMALL",
                    0.84,
                ),
            ),
        },

        "drink": {
            "known": True,
            "effects": effects(
                thirst=(
                    "DEC_LARGE",
                    0.84,
                ),
            ),
        },
    },

    expected_action="eat",
)


# ================================================================
# CASE 2
# LOW HUNGER / LOW ENERGY
#
# sleep should beat eat.
# ================================================================

run_case(
    title=
        "CASE 2 — LOW hunger / LOW energy",

    state={
        "hunger": 20.0,
        "thirst": 40.0,
        "energy": 20.0,
        "curiosity": 50.0,
    },

    knowledge={
        "eat": {
            "known": True,
            "effects": effects(
                hunger=(
                    "DEC_LARGE",
                    0.84,
                ),
            ),
        },

        "sleep": {
            "known": True,
            "effects": effects(
                energy=(
                    "INC_LARGE",
                    0.84,
                ),
            ),
        },
    },

    expected_action="sleep",
)


# ================================================================
# CASE 3
# UNKNOWN ACTION
#
# Unknown relation becomes exploration candidate.
# ================================================================

run_case(
    title="CASE 3 — Unknown relation",

    state={
        "hunger": 50.0,
        "thirst": 50.0,
        "energy": 50.0,
        "curiosity": 50.0,
    },

    knowledge={
        "eat": {
            "known": True,
            "effects": effects(
                hunger=(
                    "NONE",
                    0.84,
                ),
            ),
        },

        "drink": {
            "known": False,
            "effects": [],
        },

        "sleep": {
            "known": False,
            "effects": [],
        },

        "work": {
            "known": False,
            "effects": [],
        },

        "idle": {
            "known": False,
            "effects": [],
        },
    },

    expected_action="drink",
    expected_mode="explore",
)

# ================================================================
# CASE 4
# DETERMINISTIC TIE
#
# eat and drink have equal score.
# Fixed action order => eat wins.
# ================================================================

run_case(
    title=
        "CASE 4 — Deterministic tie",

    state={
        "hunger": 80.0,
        "thirst": 80.0,
        "energy": 50.0,
        "curiosity": 50.0,
    },

    knowledge={
        "eat": {
            "known": True,
            "effects": effects(
                hunger=(
                    "DEC_LARGE",
                    0.80,
                ),
            ),
        },

        "drink": {
            "known": True,
            "effects": effects(
                thirst=(
                    "DEC_LARGE",
                    0.80,
                ),
            ),
        },
    },

    expected_action="eat",
)


print("=" * 72)
print("ALL DECISION TESTS PASSED")
print("=" * 72)