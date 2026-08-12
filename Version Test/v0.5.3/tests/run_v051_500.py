from __future__ import annotations

import json
from collections import Counter
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
    "baseline_500_trace.json"
)

SUMMARY_FILE = Path(
    "baseline_500_summary.txt"
)


# ================================================================
# ENVIRONMENT / KNOWLEDGE / ENTITY
# ================================================================

environment = SurvivalEnvironment(
    initial_state=INITIAL_STATE
)

knowledge = LearnedRelationStore()

entity = EntityCore(
    environment=environment,
    knowledge=knowledge,
)


# ================================================================
# AGGREGATE STATISTICS
# ================================================================

mode_counts = {
    "explore": 0,
    "exploit": 0,
    "fallback": 0,
}

action_counts = {
    action: 0
    for action in environment.available_actions
}


# ================================================================
# CONTEXT STATISTICS
# ================================================================

bucket_visit_counts = Counter()

bucket_transition_counts = Counter()


# ================================================================
# DECISION EVIDENCE STATISTICS
# ================================================================

decision_evidence_summary = {
    action: {
        "uses": 0,
        "min_support": None,
        "max_support": None,
        "mean_support": 0.0,
        "min_confidence": None,
        "max_confidence": None,
        "mean_confidence": 0.0,
        "relation_count": 0,
    }
    for action in environment.available_actions
}


# ================================================================
# RAW TRACE
# ================================================================

trace: list[dict[str, Any]] = []


# ================================================================
# HELPER FUNCTIONS
# ================================================================

def bucket_from_state(
    state: dict,
) -> tuple[str, ...]:

    return bucket_state(state)


def serialize_bucket(
    bucket: tuple[str, ...],
) -> list[str]:

    return list(bucket)


def serialize_value(
    value: Any,
) -> Any:
    """
    Convert common project objects into JSON-safe values.
    """

    if isinstance(
        value,
        tuple,
    ):
        return [
            serialize_value(item)
            for item in value
        ]

    if isinstance(
        value,
        dict,
    ):
        return {
            str(key):
                serialize_value(item)
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        list,
    ):
        return [
            serialize_value(item)
            for item in value
        ]

    return value


def summarize_evidence(
    action: str,
    relation: dict,
) -> None:
    """
    Record evidence quality for relation cells used by the
    selected action.
    """

    effects = relation.get(
        "effects",
        [],
    )

    stats = decision_evidence_summary[
        action
    ]

    used_count = 0

    for effect in effects:

        if not effect.get(
            "known",
            False,
        ):
            continue

        support = float(
            effect.get(
                "support",
                0.0,
            )
        )

        confidence = float(
            effect.get(
                "confidence",
                0.0,
            )
        )

        stats["min_support"] = (
            support
            if stats["min_support"] is None
            else min(
                stats["min_support"],
                support,
            )
        )

        stats["max_support"] = (
            support
            if stats["max_support"] is None
            else max(
                stats["max_support"],
                support,
            )
        )

        stats["mean_support"] += (
            support
        )

        stats["min_confidence"] = (
            confidence
            if stats["min_confidence"] is None
            else min(
                stats["min_confidence"],
                confidence,
            )
        )

        stats["max_confidence"] = (
            confidence
            if stats["max_confidence"] is None
            else max(
                stats["max_confidence"],
                confidence,
            )
        )

        stats["mean_confidence"] += (
            confidence
        )

        used_count += 1

    if used_count > 0:

        stats["uses"] += 1
        stats["relation_count"] += (
            used_count
        )


def build_selected_effects(
    relation: dict,
) -> list[dict]:

    effects = relation.get(
        "effects",
        [],
    )

    selected_effects = []

    for effect in effects:

        selected_effects.append(
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

                "known":
                    effect.get(
                        "known"
                    ),
            }
        )

    return selected_effects


# ================================================================
# STARTUP
# ================================================================

print("=" * 72)
print("ENTITY CORE — V0.5.1")
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
        bucket_from_state(
            state_before
        )
    )

    bucket_visit_counts[
        bucket_before
    ] += 1

    # ------------------------------------------------------------
    # KNOWLEDGE BEFORE DECISION
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
        state=state_before,
        knowledge_view=knowledge_view,
    )

    action = decision.action
    mode = decision.mode
    score = decision.score

    mode_counts[mode] += 1
    action_counts[action] += 1

    # ------------------------------------------------------------
    # SELECTED RELATION / EVIDENCE
    # ------------------------------------------------------------

    selected_relation = (
        knowledge_view.get(
            action,
            {},
        )
    )

    summarize_evidence(
        action,
        selected_relation,
    )

    selected_effects = (
        build_selected_effects(
            selected_relation
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

    bucket_after = (
        bucket_from_state(
            state_after
        )
    )

    # ------------------------------------------------------------
    # CONTEXT TRANSITION
    # ------------------------------------------------------------

    bucket_transition_counts[
        (
            bucket_before,
            bucket_after,
        )
    ] += 1

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
    # RAW TRACE
    # ------------------------------------------------------------

    trace.append(
        {
            "cycle":
                cycle,

            "bucket_before":
                serialize_bucket(
                    bucket_before
                ),

            "decision": {
                "action":
                    action,

                "mode":
                    mode,

                "score":
                    score,

                "reason":
                    decision.reason,
            },

            "selected_relation":
                selected_effects,

            "state_before":
                serialize_value(
                    state_before
                ),

            "state_after":
                serialize_value(
                    state_after
                ),

            "bucket_after":
                serialize_bucket(
                    bucket_after
                ),

            "knowledge_updates":
                serialize_value(
                    knowledge_updates
                ),
        }
    )

    # ------------------------------------------------------------
    # LIGHT TERMINAL PROGRESS
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

context_changes = sum(
    1
    for item in trace
    if (
        item["bucket_before"]
        != item["bucket_after"]
    )
)


# ================================================================
# SAVE RAW TRACE
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

summary_lines: list[str] = []

summary_lines.extend(
    [
        "=" * 72,
        "ENTITY CORE — V0.5.1",
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
        f"{knowledge.cell_count}",

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
        "Action Usage",
    ]
)


for action, count in (
    action_counts.items()
):

    summary_lines.append(
        f"  {action:<8}: {count}"
    )


# ================================================================
# CONTEXT SUMMARY
# ================================================================

summary_lines.extend(
    [
        "",
        "Context Summary",

        f"  Unique contexts visited : "
        f"{len(bucket_visit_counts)}",

        f"  Context changes          : "
        f"{context_changes}",

        (
            f"  Context change rate      : "
            f"{context_changes / completed_cycles:.3f}"
            if completed_cycles > 0
            else
            "  Context change rate      : 0.000"
        ),

        "",
        "Visited Contexts",
    ]
)


for bucket, count in (
    bucket_visit_counts.most_common()
):

    summary_lines.append(
        "  "
        + "("
        + ",".join(bucket)
        + ")"
        + f" : {count}"
    )


# ================================================================
# CONTEXT TRANSITIONS
# ================================================================

summary_lines.extend(
    [
        "",
        "Most Common Context Transitions",
    ]
)


for (
    (before, after),
    count,
) in bucket_transition_counts.most_common(
    20
):

    summary_lines.append(
        "  "
        + "("
        + ",".join(before)
        + ")"
        + " -> "
        + "("
        + ",".join(after)
        + ")"
        + f" : {count}"
    )


# ================================================================
# EVIDENCE MATURITY
# ================================================================

summary_lines.extend(
    [
        "",
        "Evidence Maturity by Selected Action",
    ]
)


for action in (
    environment.available_actions
):

    stats = (
        decision_evidence_summary[
            action
        ]
    )

    if stats["relation_count"] == 0:

        summary_lines.append(
            f"  {action:<8}: "
            f"no known relation selected"
        )

        continue

    relation_count = (
        stats["relation_count"]
    )

    mean_support = (
        stats["mean_support"]
        / relation_count
    )

    mean_confidence = (
        stats["mean_confidence"]
        / relation_count
    )

    summary_lines.append(
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
# TRACE INFORMATION
# ================================================================

summary_lines.extend(
    [
        "",
        "Trace Files",

        f"  Raw trace   : "
        f"{TRACE_FILE}",

        f"  Summary     : "
        f"{SUMMARY_FILE}",

        f"  Records     : "
        f"{len(trace)}",

        "",
        "=" * 72,
    ]
)


# ================================================================
# SAVE SUMMARY
# ================================================================

SUMMARY_FILE.write_text(
    "\n".join(
        summary_lines
    ),
    encoding="utf-8",
)


# ================================================================
# TERMINAL SUMMARY
# ================================================================

print()
print("=" * 72)
print("FINAL RESULT")
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
    f"{knowledge.cell_count}"
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

print("\nAction Usage")

for action, count in (
    action_counts.items()
):

    print(
        f"  {action:<8}: "
        f"{count}"
    )

print("\nInstrumentation")

print(
    f"  Unique contexts : "
    f"{len(bucket_visit_counts)}"
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
print("INSTRUMENTED BASELINE COMPLETE")
print("=" * 72)