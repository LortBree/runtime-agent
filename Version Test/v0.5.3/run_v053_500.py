from __future__ import annotations

import json
from pathlib import Path
from collections import Counter
from typing import Any

from layer1_environment import (
    State,
    SurvivalEnvironment,
)

from layer2_knowledge import (
    LearnedRelationStore,
)

from layer2_knowledge.bucketing import (
    bucket_state,
)

from layer3_entity import (
    EntityCore,
    DecisionEngine,
)


# ================================================================
# CONFIG
# ================================================================

TOTAL_CYCLES = 500
SEED = 42

INITIAL_STATE = State(
    hunger=60.0,
    thirst=60.0,
    energy=60.0,
    curiosity=50.0,
)

TRACE_FILE = Path(
    "baseline_053_trace.json"
)

SUMMARY_FILE = Path(
    "baseline_053_summary.txt"
)


# ================================================================
# HELPERS
# ================================================================

def serialize(value: Any) -> Any:
    if hasattr(value, "as_dict"):
        return serialize(
            value.as_dict()
        )

    if hasattr(value, "__dict__") and not isinstance(
        value,
        (str, int, float, bool),
    ):
        return {
            str(key): serialize(item)
            for key, item in value.__dict__.items()
        }

    if isinstance(
        value,
        tuple,
    ):
        return [
            serialize(item)
            for item in value
        ]

    if isinstance(
        value,
        list,
    ):
        return [
            serialize(item)
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key): serialize(item)
            for key, item in value.items()
        }

    return value


def state_bucket(
    state: dict,
) -> tuple[str, ...]:
    result = bucket_state(
        state
    )

    if isinstance(
        result,
        tuple,
    ):
        return result

    return tuple(result)


def get_lr_cells(
    knowledge,
) -> int:

    if hasattr(
        knowledge,
        "cell_count",
    ):
        return int(
            knowledge.cell_count
        )

    if hasattr(
        knowledge,
        "cells",
    ):
        return len(
            knowledge.cells
        )

    return 0


def extract_effect_evidence(
    effect: dict,
) -> float:

    total = effect.get(
        "total_evidence"
    )

    if total is not None:
        return max(
            0.0,
            float(total),
        )

    support = float(
        effect.get(
            "support",
            0.0,
        )
    )

    contradiction = float(
        effect.get(
            "contradiction",
            0.0,
        )
    )

    return max(
        0.0,
        support + contradiction,
    )


def collect_selected_evidence(
    knowledge_view: dict,
    action: str,
) -> list[dict]:

    relation = knowledge_view.get(
        action,
        {},
    )

    effects = relation.get(
        "effects",
        [],
    )

    result = []

    for effect in effects:

        result.append(
            {
                "variable":
                    effect.get(
                        "variable"
                    ),

                "magnitude":
                    effect.get(
                        "magnitude"
                    ),

                "confidence":
                    effect.get(
                        "confidence"
                    ),

                "label":
                    effect.get(
                        "label"
                    ),

                "support":
                    effect.get(
                        "support"
                    ),

                "contradiction":
                    effect.get(
                        "contradiction"
                    ),

                "total_evidence":
                    effect.get(
                        "total_evidence"
                    ),

                "evidence":
                    extract_effect_evidence(
                        effect
                    ),

                "known":
                    effect.get(
                        "known",
                        False,
                    ),
            }
        )

    return result


def calculate_action_novelty(
    evidence: float,
    k: float = 5.0,
) -> float:

    if evidence < 0.0:
        raise ValueError(
            "evidence must be >= 0"
        )

    if k <= 0.0:
        raise ValueError(
            "k must be > 0"
        )

    return k / (
        evidence + k
    )


# ================================================================
# INITIALIZE
# ================================================================

environment = SurvivalEnvironment(
    initial_state=INITIAL_STATE
)

knowledge = LearnedRelationStore()

decision_engine = DecisionEngine(
    action_order=(
        environment.available_actions
    )
)

entity = EntityCore(
    environment=environment,
    knowledge=knowledge,
    decision_engine=decision_engine,
)


# ================================================================
# STATISTICS
# ================================================================

mode_counts = Counter()

action_counts = Counter()

context_counts = Counter()

context_transitions = Counter()

exploration_actions = Counter()

neutral_actions = Counter()

exploit_actions = Counter()

neutral_harm_values: list[float] = []

exploration_novelty_values: list[float] = []

all_novelty_values: list[float] = []

context_changes = 0


# ================================================================
# TRACE
# ================================================================

trace: list[dict] = []


# ================================================================
# START
# ================================================================

print("=" * 72)
print("ENTITY CORE — V0.5.3")
print("=" * 72)

print(
    f"Initial State : "
    f"{environment.state.as_dict()}"
)

print(
    f"Running {TOTAL_CYCLES} cycles..."
)

print(
    f"Seed: {SEED}"
)

print()


# ================================================================
# MAIN LOOP
# ================================================================

for cycle in range(
    1,
    TOTAL_CYCLES + 1,
):

    if not environment.state.alive:

        print(
            f"Entity died at cycle "
            f"{cycle - 1}."
        )

        break

    # ------------------------------------------------------------
    # STATE BEFORE
    # ------------------------------------------------------------

    state_before = entity.observe()

    bucket_before = state_bucket(
        state_before
    )

    context_counts[
        bucket_before
    ] += 1

    # ------------------------------------------------------------
    # KNOWLEDGE
    # ------------------------------------------------------------

    knowledge_view = (
        entity.retrieve_knowledge(
            state_before
        )
    )

    # ------------------------------------------------------------
    # DECISION
    # ------------------------------------------------------------

    decision = entity.decide(
        state_before,
        knowledge_view,
    )

    action = decision.action
    mode = decision.mode
    score = decision.score

    mode_counts[
        mode
    ] += 1

    action_counts[
        action
    ] += 1

    if mode == "explore":
        exploration_actions[
            action
        ] += 1

    elif mode == "neutral":
        neutral_actions[
            action
        ] += 1

    elif mode == "exploit":
        exploit_actions[
            action
        ] += 1

    # ------------------------------------------------------------
    # EVALUATIONS
    # ------------------------------------------------------------

    evaluations = []

    selected_harm = None

    for evaluation in (
        decision.evaluations
    ):

        row = {
            "action":
                evaluation.action,

            "score":
                evaluation.score,

            "harm_score":
                getattr(
                    evaluation,
                    "harm_score",
                    None,
                ),

            "confidence_mean":
                evaluation.confidence_mean,

            "known_variables":
                evaluation.known_variables,

            "unknown_variables":
                evaluation.unknown_variables,

            "action_known":
                evaluation.action_known,

            "context_known":
                evaluation.context_known,
        }

        evaluations.append(
            row
        )

        if (
            evaluation.action
            == action
        ):
            selected_harm = getattr(
                evaluation,
                "harm_score",
                None,
            )

    # ------------------------------------------------------------
    # SELECTED EVIDENCE
    # ------------------------------------------------------------

    selected_evidence = (
        collect_selected_evidence(
            knowledge_view,
            action,
        )
    )

    # ------------------------------------------------------------
    # NOVELTY
    # ------------------------------------------------------------

    evidence_values = []

    for effect in selected_evidence:

        if effect["known"]:
            evidence_values.append(
                float(
                    effect["evidence"]
                )
            )

    selected_evidence_level = (
        max(evidence_values)
        if evidence_values
        else 0.0
    )

    selected_novelty = (
        calculate_action_novelty(
            selected_evidence_level
        )
    )

    all_action_novelty = {}

    for evaluation in (
        decision.evaluations
    ):

        relation = knowledge_view.get(
            evaluation.action,
            {},
        )

        effects = relation.get(
            "effects",
            [],
        )

        known_evidence = []

        for effect in effects:

            if not effect.get(
                "known",
                False,
            ):
                continue

            known_evidence.append(
                extract_effect_evidence(
                    effect
                )
            )

        evidence = (
            max(known_evidence)
            if known_evidence
            else 0.0
        )

        novelty = (
            calculate_action_novelty(
                evidence
            )
        )

        all_action_novelty[
            evaluation.action
        ] = novelty

        all_novelty_values.append(
            novelty
        )

    # ------------------------------------------------------------
    # REGIME METRICS
    # ------------------------------------------------------------

    if mode == "explore":

        exploration_novelty_values.append(
            selected_novelty
        )

    if mode == "neutral":

        if selected_harm is not None:
            neutral_harm_values.append(
                float(
                    selected_harm
                )
            )

    # ------------------------------------------------------------
    # EXECUTE
    # ------------------------------------------------------------

    transition = entity.execute(
        action
    )

    state_after = (
        transition.state_after
    )

    bucket_after = state_bucket(
        state_after
    )

    context_transitions[
        (
            bucket_before,
            bucket_after,
        )
    ] += 1

    if (
        bucket_before
        != bucket_after
    ):
        context_changes += 1

    # ------------------------------------------------------------
    # EXPERIENCE
    # ------------------------------------------------------------

    experience = (
        entity.generate_experience(
            transition
        )
    )

    # ------------------------------------------------------------
    # LEARN
    # ------------------------------------------------------------

    updates = entity.learn(
        experience
    )

    entity.experiences.append(
        experience
    )

    # ------------------------------------------------------------
    # TRACE
    # ------------------------------------------------------------

    trace.append(
        {
            "cycle":
                cycle,

            "bucket_before":
                list(
                    bucket_before
                ),

            "state_before":
                serialize(
                    state_before
                ),

            "decision":
                {
                    "action":
                        action,

                    "mode":
                        mode,

                    "score":
                        score,

                    "reason":
                        decision.reason,
                },

            "regime":
                {
                    "selected_harm":
                        selected_harm,

                    "selected_evidence":
                        selected_evidence_level,

                    "selected_novelty":
                        selected_novelty,

                    "max_novelty":
                        max(
                            all_action_novelty.values()
                        )
                        if all_action_novelty
                        else 0.0,

                    "saturated":
                        (
                            max(
                                all_action_novelty.values()
                            )
                            <= 0.25
                        )
                        if all_action_novelty
                        else True,
                },

            "evaluations":
                evaluations,

            "all_action_novelty":
                all_action_novelty,

            "transition":
                serialize(
                    transition
                ),

            "experience":
                serialize(
                    experience
                ),

            "knowledge_updates":
                serialize(
                    updates
                ),

            "state_after":
                serialize(
                    state_after
                ),

            "bucket_after":
                list(
                    bucket_after
                ),
        }
    )

    # ------------------------------------------------------------
    # LIGHT PROGRESS
    # ------------------------------------------------------------

    if cycle % 100 == 0:

        print(
            f"Progress: "
            f"{cycle}/{TOTAL_CYCLES}"
        )


# ================================================================
# FINAL METRICS
# ================================================================

completed_cycles = len(
    trace
)

final_state = (
    environment.state.as_dict()
)

lr_cells = get_lr_cells(
    knowledge
)

# ================================================================
# SAVE TRACE
# ================================================================

TRACE_FILE.write_text(
    json.dumps(
        trace,
        indent=2,
        ensure_ascii=False,
    ),
    encoding="utf-8",
)


# ================================================================
# HELPERS FOR SUMMARY
# ================================================================

def percentage(
    count: int,
) -> float:

    if completed_cycles == 0:
        return 0.0

    return (
        count
        / completed_cycles
        * 100.0
    )


def mean(
    values: list[float],
) -> float | None:

    if not values:
        return None

    return (
        sum(values)
        / len(values)
    )


# ================================================================
# BUILD SUMMARY
# ================================================================

summary = [
    "=" * 72,
    "ENTITY CORE — V0.5.3",
    "500-CYCLE BASELINE SUMMARY",
    "=" * 72,
    "",
    f"Alive          : "
    f"{environment.state.alive}",

    f"Total cycles   : "
    f"{completed_cycles}",

    f"Simulated days : "
    f"{environment.day}",

    f"LR cells       : "
    f"{lr_cells}",

    "",
    "Initial State",
    f"  {INITIAL_STATE.as_dict()}",

    "",
    "Final State",

    f"  Hunger       : "
    f"{final_state['hunger']:6.1f}",

    f"  Thirst       : "
    f"{final_state['thirst']:6.1f}",

    f"  Energy       : "
    f"{final_state['energy']:6.1f}",

    f"  Curiosity    : "
    f"{final_state['curiosity']:6.1f}",

    "",
    "Decision Statistics",

    f"  Explore      : "
    f"{mode_counts['explore']} "
    f"({percentage(mode_counts['explore']):.1f}%)",

    f"  Exploit      : "
    f"{mode_counts['exploit']} "
    f"({percentage(mode_counts['exploit']):.1f}%)",

    f"  Neutral      : "
    f"{mode_counts['neutral']} "
    f"({percentage(mode_counts['neutral']):.1f}%)",

    f"  Fallback     : "
    f"{mode_counts['fallback']} "
    f"({percentage(mode_counts['fallback']):.1f}%)",

    "",
    "Action Usage",
]


for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{action_counts[action]}"
    )


# ================================================================
# REGIME ACTION USAGE
# ================================================================

summary.extend(
    [
        "",
        "Exploration Action Usage",
    ]
)

for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{exploration_actions[action]}"
    )


summary.extend(
    [
        "",
        "Neutral Action Usage",
    ]
)

for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{neutral_actions[action]}"
    )


summary.extend(
    [
        "",
        "Exploit Action Usage",
    ]
)

for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{exploit_actions[action]}"
    )


# ================================================================
# REGIME QUALITY
# ================================================================

summary.extend(
    [
        "",
        "Regime Quality",
        f"  Mean exploration novelty : "
        f"{mean(exploration_novelty_values)}"
        if exploration_novelty_values
        else
        "  Mean exploration novelty : None",

        f"  Max exploration novelty  : "
        f"{max(exploration_novelty_values):.6f}"
        if exploration_novelty_values
        else
        "  Max exploration novelty  : None",

        f"  Min exploration novelty  : "
        f"{min(exploration_novelty_values):.6f}"
        if exploration_novelty_values
        else
        "  Min exploration novelty  : None",

        f"  Mean neutral harm        : "
        f"{mean(neutral_harm_values)}"
        if neutral_harm_values
        else
        "  Mean neutral harm        : None",

        f"  Min neutral harm         : "
        f"{min(neutral_harm_values):.6f}"
        if neutral_harm_values
        else
        "  Min neutral harm         : None",
    ]
)


# ================================================================
# CONTEXT
# ================================================================

summary.extend(
    [
        "",
        "Context Statistics",

        f"  Unique contexts : "
        f"{len(context_counts)}",

        f"  Context changes : "
        f"{context_changes}",

        f"  Change rate     : "
        f"{percentage(context_changes):.3f}",
    ]
)

summary.append(
    ""
)

summary.append(
    "Visited Contexts"
)

for bucket, count in (
    context_counts.most_common()
):

    summary.append(
        "  ("
        + ",".join(bucket)
        + ")"
        + f" : {count}"
    )


# ================================================================
# CONTEXT TRANSITIONS
# ================================================================

summary.extend(
    [
        "",
        "Most Common Context Transitions",
    ]
)

for (
    (before, after),
    count,
) in context_transitions.most_common(
    20
):

    summary.append(
        "  ("
        + ",".join(before)
        + ") -> ("
        + ",".join(after)
        + ")"
        + f" : {count}"
    )


# ================================================================
# OUTPUT
# ================================================================

summary.extend(
    [
        "",
        "Output Files",

        f"  Trace   : "
        f"{TRACE_FILE}",

        f"  Summary : "
        f"{SUMMARY_FILE}",

        f"  Records : "
        f"{len(trace)}",

        "",
        "=" * 72,
    ]
)


SUMMARY_FILE.write_text(
    "\n".join(summary),
    encoding="utf-8",
)


# ================================================================
# TERMINAL
# ================================================================

print()
print("=" * 72)
print("FINAL RESULT — V0.5.3")
print("=" * 72)

print(
    f"Alive          : "
    f"{environment.state.alive}"
)

print(
    f"Total cycles   : "
    f"{completed_cycles}"
)

print(
    f"Simulated days : "
    f"{environment.day}"
)

print(
    f"LR cells       : "
    f"{lr_cells}"
)

print("\nFinal State")

print(
    f"  Hunger       : "
    f"{final_state['hunger']:6.1f}"
)

print(
    f"  Thirst       : "
    f"{final_state['thirst']:6.1f}"
)

print(
    f"  Energy       : "
    f"{final_state['energy']:6.1f}"
)

print(
    f"  Curiosity    : "
    f"{final_state['curiosity']:6.1f}"
)

print("\nDecision Statistics")

print(
    f"  Explore      : "
    f"{mode_counts['explore']}"
)

print(
    f"  Exploit      : "
    f"{mode_counts['exploit']}"
)

print(
    f"  Neutral      : "
    f"{mode_counts['neutral']}"
)

print(
    f"  Fallback     : "
    f"{mode_counts['fallback']}"
)

print("\nAction Usage")

for action in (
    environment.available_actions
):

    print(
        f"  {action:<8}: "
        f"{action_counts[action]}"
    )

print("\nInstrumentation")

print(
    f"  Unique contexts : "
    f"{len(context_counts)}"
)

print(
    f"  Context changes : "
    f"{context_changes}"
)

print(
    f"  Trace records   : "
    f"{len(trace)}"
)

print(
    f"\nTrace saved   : "
    f"{TRACE_FILE}"
)

print(
    f"Summary saved : "
    f"{SUMMARY_FILE}"
)

print()
print("=" * 72)
print("V0.5.3 BASELINE COMPLETE")
print("=" * 72)