from __future__ import annotations

import json
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
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
    "baseline_052_trace.json"
)

SUMMARY_FILE = Path(
    "baseline_052_summary.txt"
)


# ================================================================
# HELPERS
# ================================================================

def serialize(
    value: Any,
) -> Any:
    """
    Convert dataclasses / tuples / mappings into JSON-safe data.
    """

    if is_dataclass(value):
        return serialize(
            asdict(value)
        )

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
            for key, item
            in value.items()
        }

    return value


def get_lr_cell_count(
    knowledge,
) -> int:
    """
    Compatible with the current LR implementation.
    """

    if hasattr(
        knowledge,
        "cells",
    ):
        return len(
            knowledge.cells
        )

    if hasattr(
        knowledge,
        "cell_count",
    ):
        return int(
            knowledge.cell_count
        )

    return 0


def get_state_bucket(
    state: dict,
) -> tuple[str, ...]:
    """
    Use Layer 2's actual bucketing implementation.
    """

    result = bucket_state(
        state
    )

    if isinstance(
        result,
        tuple,
    ):
        return result

    return tuple(
        result
    )


def get_effect_evidence(
    effect: dict,
) -> float:
    """
    Extract current-context evidence from one LR effect.

    Preferred:
        total_evidence

    Fallback:
        support + contradiction
    """

    if effect.get(
        "total_evidence"
    ) is not None:

        return max(
            0.0,
            float(
                effect[
                    "total_evidence"
                ]
            ),
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


def selected_action_evidence(
    knowledge_view: dict,
    action: str,
) -> dict:
    """
    Summarize evidence maturity for the selected action.
    """

    relation = knowledge_view.get(
        action,
        {},
    )

    effects = relation.get(
        "effects",
        [],
    )

    rows = []

    for effect in effects:

        row = {
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
                get_effect_evidence(
                    effect
                ),

            "known":
                effect.get(
                    "known",
                    True,
                ),
        }

        rows.append(
            row
        )

    return {
        "action":
            action,

        "action_known":
            relation.get(
                "action_known",
                False,
            ),

        "known":
            relation.get(
                "known",
                False,
            ),

        "effects":
            rows,
    }


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

bucket_visits = Counter()

bucket_transitions = Counter()

zero_score_actions = Counter()

positive_score_count = 0

zero_score_count = 0

negative_score_count = 0

exploration_action_counts = Counter()

explore_reason_counts = Counter()

context_change_count = 0


# ================================================================
# EVIDENCE MATURITY
# ================================================================

evidence_stats = {
    action: {
        "uses": 0,
        "relation_count": 0,
        "support_sum": 0.0,
        "confidence_sum": 0.0,
        "min_support": None,
        "max_support": None,
        "min_confidence": None,
        "max_confidence": None,
    }
    for action
    in environment.available_actions
}


# ================================================================
# RAW TRACE
# ================================================================

trace: list[dict] = []


# ================================================================
# HEADER
# ================================================================

print("=" * 72)
print("ENTITY CORE — V0.5.2")
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

    state_before = (
        entity.observe()
    )

    bucket_before = (
        get_state_bucket(
            state_before
        )
    )

    bucket_visits[
        bucket_before
    ] += 1

    # ------------------------------------------------------------
    # RETRIEVE KNOWLEDGE
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

    # ------------------------------------------------------------
    # SCORE REGIME
    # ------------------------------------------------------------

    if score is not None:

        if score > 0.0:
            positive_score_count += 1

        elif score == 0.0:
            zero_score_count += 1
            zero_score_actions[
                action
            ] += 1

        else:
            negative_score_count += 1

    # ------------------------------------------------------------
    # EXPLORATION STATS
    # ------------------------------------------------------------

    if mode == "explore":

        exploration_action_counts[
            action
        ] += 1

        explore_reason_counts[
            decision.reason
        ] += 1

    # ------------------------------------------------------------
    # EVIDENCE MATURITY OF SELECTED ACTION
    # ------------------------------------------------------------

    evidence_view = (
        selected_action_evidence(
            knowledge_view,
            action,
        )
    )

    selected_effects = (
        evidence_view["effects"]
    )

    stats = evidence_stats[
        action
    ]

    known_effect_count = 0

    for effect in selected_effects:

        if not effect["known"]:
            continue

        evidence = float(
            effect["evidence"]
        )

        confidence = float(
            effect.get(
                "confidence",
                0.0,
            )
        )

        support = float(
            effect.get(
                "support",
                0.0,
            )
        )

        stats[
            "support_sum"
        ] += support

        stats[
            "confidence_sum"
        ] += confidence

        stats[
            "min_support"
        ] = (
            support
            if stats[
                "min_support"
            ] is None
            else min(
                stats[
                    "min_support"
                ],
                support,
            )
        )

        stats[
            "max_support"
        ] = (
            support
            if stats[
                "max_support"
            ] is None
            else max(
                stats[
                    "max_support"
                ],
                support,
            )
        )

        stats[
            "min_confidence"
        ] = (
            confidence
            if stats[
                "min_confidence"
            ] is None
            else min(
                stats[
                    "min_confidence"
                ],
                confidence,
            )
        )

        stats[
            "max_confidence"
        ] = (
            confidence
            if stats[
                "max_confidence"
            ] is None
            else max(
                stats[
                    "max_confidence"
                ],
                confidence,
            )
        )

        stats[
            "relation_count"
        ] += 1

        known_effect_count += 1

    if known_effect_count > 0:
        stats[
            "uses"
        ] += 1

    # ------------------------------------------------------------
    # EXECUTE
    # ------------------------------------------------------------

    transition = entity.execute(
        action
    )

    state_after = (
        transition.state_after
    )

    bucket_after = (
        get_state_bucket(
            state_after
        )
    )

    bucket_transitions[
        (
            bucket_before,
            bucket_after,
        )
    ] += 1

    if (
        bucket_before
        != bucket_after
    ):
        context_change_count += 1

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

    knowledge_updates = (
        entity.learn(
            experience
        )
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
                        decision.action,

                    "mode":
                        decision.mode,

                    "score":
                        decision.score,

                    "reason":
                        decision.reason,
                },

            "selected_evidence":
                selected_effects,

            "evaluations":
                serialize(
                    decision.evaluations
                ),

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
                    knowledge_updates
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
# FINAL COUNTS
# ================================================================

completed_cycles = len(
    trace
)

final_state = (
    environment.state.as_dict()
)

lr_cells = get_lr_cell_count(
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
        default=str,
    ),
    encoding="utf-8",
)


# ================================================================
# BUILD SUMMARY
# ================================================================

summary: list[str] = []

summary.extend(
    [
        "=" * 72,
        "ENTITY CORE — V0.5.2",
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
        f"{mode_counts['explore']}",

        f"  Exploit      : "
        f"{mode_counts['exploit']}",

        f"  Fallback     : "
        f"{mode_counts['fallback']}",

        "",
        "Score Regime",

        f"  Positive     : "
        f"{positive_score_count}",

        f"  Zero         : "
        f"{zero_score_count}",

        f"  Negative     : "
        f"{negative_score_count}",

        "",
        "Action Usage",
    ]
)


for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{action_counts[action]}"
    )


# ================================================================
# ZERO-SCORE ACTIONS
# ================================================================

summary.extend(
    [
        "",
        "Zero-Score Decisions",
    ]
)

for action in (
    environment.available_actions
):

    summary.append(
        f"  {action:<8}: "
        f"{zero_score_actions[action]}"
    )


# ================================================================
# EXPLORATION
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
        f"{exploration_action_counts[action]}"
    )


summary.append(
    ""
)

summary.append(
    "Exploration Reasons"
)

for reason, count in (
    explore_reason_counts.items()
):

    summary.append(
        f"  {reason}: {count}"
    )


# ================================================================
# CONTEXT
# ================================================================

summary.extend(
    [
        "",
        "Context Statistics",

        f"  Unique contexts : "
        f"{len(bucket_visits)}",

        f"  Context changes : "
        f"{context_change_count}",
    ]
)

if completed_cycles > 0:

    summary.append(
        f"  Change rate     : "
        f"{context_change_count / completed_cycles:.3f}"
    )


summary.extend(
    [
        "",
        "Visited Contexts",
    ]
)


for bucket, count in (
    bucket_visits.most_common()
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
) in bucket_transitions.most_common(
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
# EVIDENCE MATURITY
# ================================================================

summary.extend(
    [
        "",
        "Evidence Maturity by Selected Action",
    ]
)


for action in (
    environment.available_actions
):

    stats = evidence_stats[
        action
    ]

    relation_count = (
        stats[
            "relation_count"
        ]
    )

    if relation_count == 0:

        summary.append(
            f"  {action:<8}: "
            f"no known selected relation"
        )

        continue

    mean_support = (
        stats[
            "support_sum"
        ]
        / relation_count
    )

    mean_confidence = (
        stats[
            "confidence_sum"
        ]
        / relation_count
    )

    summary.append(
        f"  {action:<8}: "
        f"uses={stats['uses']:4d} "
        f"relations={relation_count:4d} "
        f"support="
        f"{stats['min_support']:.3f}"
        f".."
        f"{stats['max_support']:.3f} "
        f"mean="
        f"{mean_support:.3f} "
        f"confidence="
        f"{stats['min_confidence']:.3f}"
        f".."
        f"{stats['max_confidence']:.3f} "
        f"mean="
        f"{mean_confidence:.3f}"
    )


# ================================================================
# FILES
# ================================================================

summary.extend(
    [
        "",
        "Output Files",
        f"  Trace   : {TRACE_FILE}",
        f"  Summary : {SUMMARY_FILE}",
        f"  Records : {len(trace)}",
        "",
        "=" * 72,
    ]
)


SUMMARY_FILE.write_text(
    "\n".join(
        summary
    ),
    encoding="utf-8",
)


# ================================================================
# TERMINAL SUMMARY
# ================================================================

print()
print("=" * 72)
print("FINAL RESULT — V0.5.2")
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
    f"  Fallback     : "
    f"{mode_counts['fallback']}"
)

print("\nScore Regime")

print(
    f"  Positive     : "
    f"{positive_score_count}"
)

print(
    f"  Zero         : "
    f"{zero_score_count}"
)

print(
    f"  Negative     : "
    f"{negative_score_count}"
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
    f"{len(bucket_visits)}"
)

print(
    f"  Context changes : "
    f"{context_change_count}"
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
print("V0.5.2 BASELINE COMPLETE")
print("=" * 72)