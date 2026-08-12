from __future__ import annotations

from layer1_environment import (
    State,
    SurvivalEnvironment,
)

from layer2_knowledge import (
    LearnedRelationStore,
)

from layer3_entity import (
    EntityCore,
    DecisionEngine,
)


# ================================================================
# CONFIG
# ================================================================

FORCED_CYCLES = 30


SATURATION_STATE = {
    "hunger": 50.0,
    "thirst": 0.0,
    "energy": 80.0,
    "curiosity": 50.0,
}


# ================================================================
# CREATE ENVIRONMENT + KNOWLEDGE
# ================================================================

environment = SurvivalEnvironment(
    initial_state=State(
        hunger=50.0,
        thirst=40.0,
        energy=80.0,
        curiosity=50.0,
    )
)

knowledge = LearnedRelationStore()

entity = EntityCore(
    environment=environment,
    knowledge=knowledge,
)


# ================================================================
# PHASE 1 — REAL OBSERVATION
# ================================================================
#
# First establish a real DEC_LARGE relation:
#
#     thirst 40 -> 10
#
# through Environment.
# ================================================================

print("=" * 72)
print("LAYER 3 — SATURATION SELF-CORRECTION")
print("=" * 72)

print("\nPHASE 1 — INITIAL REAL EFFECT")
print("-" * 72)

transition = environment.step(
    "drink"
)

experience = (
    entity.generate_experience(
        transition
    )
)

updates = entity.learn(
    experience
)

entity.experiences.append(
    experience
)

print(
    "Before:",
    transition.state_before,
)

print(
    "After :",
    transition.state_after,
)

for update in updates:

    if update["variable"] == "thirst":

        print(
            f"thirst "
            f"delta={update['delta']:+.2f} "
            f"observed="
            f"{update['observed_effect']:<10} "
            f"learned="
            f"{update['learned_effect']:<10} "
            f"confidence="
            f"{update['confidence']:.3f} "
            f"label="
            f"{update['label']}"
        )


# ================================================================
# PHASE 2 — MOVE TO SATURATION
# ================================================================
#
# Reset ONLY the environment.
#
# Knowledge remains intact.
#
# This creates:
#
#     thirst = 0
#
# while keeping the previously learned DEC_LARGE evidence.
# ================================================================

environment.reset(
    State(
        hunger=50.0,
        thirst=0.0,
        energy=80.0,
        curiosity=50.0,
    )
)

print("\nPHASE 2 — SATURATION STATE")
print("-" * 72)

print(
    environment.state.as_dict()
)


# ================================================================
# CAPTURE THE SATURATION CONTEXT
# ================================================================

saturation_state = (
    environment.state.as_dict()
)


# ================================================================
# PHASE 3 — FORCED REAL OBSERVATION
# ================================================================
#
# IMPORTANT:
# DecisionEngine is NOT involved here.
#
# We deliberately force "drink" so that we can measure LR
# adaptation independently from decision behavior.
#
# Every observation still comes through:
#
#     Environment
#       ↓
#     Transition
#       ↓
#     Experience
#       ↓
#     Knowledge.update()
# ================================================================

print(
    "\nPHASE 3 — FORCED DRINK OBSERVATIONS"
)

print("-" * 72)

magnitude_converged_at = None
semantic_converged_at = None


for cycle in range(
    1,
    FORCED_CYCLES + 1,
):

    transition = (
        environment.step(
            "drink"
        )
    )

    experience = (
        entity.generate_experience(
            transition
        )
    )

    updates = entity.learn(
        experience
    )

    entity.experiences.append(
        experience
    )

    thirst_update = next(
        update
        for update in updates
        if update["variable"]
        == "thirst"
    )

    relation = knowledge.query(
        state=saturation_state,
        action="drink",
        variable="thirst",
    )

    print(
        f"{cycle:02d} "
        f"observed="
        f"{thirst_update['observed_effect']:<10} "
        f"learned="
        f"{str(relation['magnitude']):<10} "
        f"confidence="
        f"{relation['confidence']:.3f} "
        f"label="
        f"{relation['label']:<7} "
        f"support="
        f"{relation['support']:7.3f} "
        f"contradiction="
        f"{relation['contradiction']:7.3f} "
        f"thirst="
        f"{environment.state.thirst:5.1f}"
    )

    # ------------------------------------------------------------
    # Convergence detection
    # ------------------------------------------------------------

    if (
        magnitude_converged_at is None
        and relation["magnitude"] == "NONE"
    ):
        magnitude_converged_at = cycle

    if (
        semantic_converged_at is None
        and relation["magnitude"] == "NONE"
        and relation["label"] == "should"
    ):
        semantic_converged_at = cycle


# ================================================================
# PHASE 4 — FINAL LR RESULT
# ================================================================

final_relation = knowledge.query(
    state=saturation_state,
    action="drink",
    variable="thirst",
)

print()
print("=" * 72)
print("PHASE 4 — LR CONVERGENCE")
print("=" * 72)

print(
    f"Final magnitude     : "
    f"{final_relation['magnitude']}"
)

print(
    f"Final confidence    : "
    f"{final_relation['confidence']:.3f}"
)

print(
    f"Final label         : "
    f"{final_relation['label']}"
)

print(
    f"Support             : "
    f"{final_relation['support']:.3f}"
)

print(
    f"Contradiction       : "
    f"{final_relation['contradiction']:.3f}"
)

print(
    f"m* -> NONE at       : "
    f"{magnitude_converged_at}"
)

print(
    f"NONE + should at    : "
    f"{semantic_converged_at}"
)

print(
    f"Final thirst        : "
    f"{environment.state.thirst:.1f}"
)


# ================================================================
# ASSERT LR ADAPTATION
# ================================================================

assert (
    final_relation["magnitude"]
    == "NONE"
), (
    "LR did not converge to NONE."
)

assert (
    final_relation["confidence"]
    >= 0.80
), (
    "LR confidence did not recover to should level."
)

assert (
    final_relation["label"]
    == "should"
), (
    "Final NONE relation is not labeled should."
)


# ================================================================
# PHASE 5 — DECISION HANDOFF
# ================================================================
#
# Now, and ONLY now, we let DecisionEngine consume the learned LR.
#
# We explicitly query the saturation context.
# ================================================================

print()
print("=" * 72)
print("PHASE 5 — DECISION HANDOFF")
print("=" * 72)

decision_engine = DecisionEngine(
    action_order=(
        "eat",
        "drink",
        "sleep",
        "work",
        "idle",
    )
)

knowledge_view = (
    knowledge.evaluate_all_actions(
        saturation_state
    )
)

decision = (
    decision_engine.select_action(
        state=saturation_state,
        knowledge=knowledge_view,
        explore_unknown=False,
    )
)

print(
    f"Selected action : "
    f"{decision.action}"
)

print(
    f"Mode            : "
    f"{decision.mode}"
)

print(
    f"Score           : "
    f"{decision.score}"
)

print(
    f"Reason          : "
    f"{decision.reason}"
)

print("\nAction scores:")

for evaluation in (
    decision.evaluations
):

    print(
        f"{evaluation.action:<7} "
        f"score={evaluation.score:7.3f} "
        f"confidence="
        f"{evaluation.confidence_mean:.3f} "
        f"known="
        f"{evaluation.known_variables}"
    )


# ================================================================
# FINAL DECISION ASSERTION
# ================================================================
#
# We do NOT assert that a particular alternative action must win.
#
# We only assert the property we care about:
#
#     drink must no longer have a positive contribution
#     from the saturated thirst relation.
# ================================================================

drink_evaluation = next(
    item
    for item in decision.evaluations
    if item.action == "drink"
)

assert (
    drink_evaluation.score
    <= 0.0
), (
    "Drink still has positive decision score "
    "after LR learned NONE at saturation."
)


print()
print("=" * 72)
print("ALL SATURATION TESTS PASSED")
print("=" * 72)