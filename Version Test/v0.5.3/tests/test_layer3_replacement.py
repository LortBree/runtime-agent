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
# SETUP
# ================================================================

knowledge = LearnedRelationStore()

environment = SurvivalEnvironment(
    initial_state=State(
        hunger=50.0,
        thirst=40.0,
        energy=80.0,
        curiosity=50.0,
    )
)

entity = EntityCore(
    environment=environment,
    knowledge=knowledge,
)


# ================================================================
# PHASE 1
# Learn real drink effect:
#
# thirst 40 -> 10
# ================================================================

print("=" * 72)
print("PHASE 1 — LEARN DRINK EFFECT")
print("=" * 72)

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

for update in updates:

    if update["variable"] == "thirst":

        print(
            f"thirst "
            f"delta={update['delta']:+.2f} "
            f"observed={update['observed_effect']:<10} "
            f"learned={update['learned_effect']:<10} "
            f"confidence={update['confidence']:.3f} "
            f"label={update['label']}"
        )


# ================================================================
# PHASE 2
# Learn real eat effect in the SAME context.
#
# Reset to:
# hunger=50
# thirst=0
# energy=80
# curiosity=50
#
# IMPORTANT:
# We use the actual Environment to generate the experience.
# ================================================================

environment.reset(
    State(
        hunger=50.0,
        thirst=0.0,
        energy=80.0,
        curiosity=50.0,
    )
)

saturation_state = (
    environment.state.as_dict()
)

print()
print("=" * 72)
print("PHASE 2 — LEARN EAT EFFECT")
print("=" * 72)

transition = environment.step(
    "eat"
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

for update in updates:

    if update["variable"] == "hunger":

        print(
            f"hunger "
            f"delta={update['delta']:+.2f} "
            f"observed={update['observed_effect']:<10} "
            f"learned={update['learned_effect']:<10} "
            f"confidence={update['confidence']:.3f} "
            f"label={update['label']}"
        )


# ================================================================
# PHASE 3
# Force drink at thirst=0 repeatedly.
#
# This creates NONE evidence for drink.
# ================================================================

environment.reset(
    State(
        hunger=50.0,
        thirst=0.0,
        energy=80.0,
        curiosity=50.0,
    )
)

print()
print("=" * 72)
print("PHASE 3 — FORCE DRINK AT SATURATION")
print("=" * 72)

for cycle in range(1, 8):

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

    relation = knowledge.query(
        state=saturation_state,
        action="drink",
        variable="thirst",
    )

    print(
        f"{cycle:02d} "
        f"observed="
        f"{next(
            u['observed_effect']
            for u in updates
            if u['variable'] == 'thirst'
        ):<10} "
        f"learned="
        f"{relation['magnitude']!s:<10} "
        f"confidence="
        f"{relation['confidence']:.3f} "
        f"label="
        f"{relation['label']}"
    )


# ================================================================
# PHASE 4
# DECISION HANDOFF
# ================================================================

print()
print("=" * 72)
print("PHASE 4 — DECISION HANDOFF")
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

print()
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


# ================================================================
# ASSERTIONS
# ================================================================

drink_relation = knowledge.query(
    state=saturation_state,
    action="drink",
    variable="thirst",
)

eat_relation = knowledge.query(
    state=saturation_state,
    action="eat",
    variable="hunger",
)

drink_score = next(
    item.score
    for item in decision.evaluations
    if item.action == "drink"
)

eat_score = next(
    item.score
    for item in decision.evaluations
    if item.action == "eat"
)


assert (
    drink_relation["magnitude"]
    == "NONE"
), (
    "Drink relation did not converge to NONE."
)

assert (
    drink_score == 0.0
), (
    f"Expected drink score 0, "
    f"got {drink_score}"
)

assert (
    eat_score > 0.0
), (
    f"Expected eat score > 0, "
    f"got {eat_score}"
)

assert (
    decision.action == "eat"
), (
    f"Expected Decision to select eat, "
    f"got {decision.action}"
)


print()
print("=" * 72)
print("ACTION REPLACEMENT TEST PASSED")
print("=" * 72)