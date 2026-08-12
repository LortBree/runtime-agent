from layer1_environment import (
    State,
    SurvivalEnvironment,
)

from layer2_knowledge import (
    LearnedRelationStore,
)

from layer3_entity import (
    EntityCore,
)


# ================================================================
# ENVIRONMENT
# ================================================================

environment = SurvivalEnvironment(
    initial_state=State(
        hunger=80.0,
        thirst=40.0,
        energy=80.0,
        curiosity=50.0,
    )
)


# ================================================================
# KNOWLEDGE
# ================================================================

knowledge = LearnedRelationStore()


# ================================================================
# WARM-UP KNOWLEDGE
# ================================================================

state_before = {
    "hunger": 80.0,
    "thirst": 40.0,
    "energy": 80.0,
    "curiosity": 50.0,
}

state_after = {
    "hunger": 82.0,
    "thirst": 42.5,
    "energy": 100.0,
    "curiosity": 49.5,
}

for _ in range(5):

    knowledge.update(
        state_before=state_before,
        action="sleep",
        state_after=state_after,
    )


# ================================================================
# ENTITY
# ================================================================

entity = EntityCore(
    environment=environment,
    knowledge=knowledge,
)


# ================================================================
# TEST
# ================================================================

print("=" * 72)
print("ENTITY CORE — V0.5.1")
print("=" * 72)

print("\nInitial State")
print(
    environment.state.as_dict()
)

print("\nKnown sleep relation")
print(
    knowledge.evaluate_action(
        state=
            state_before,
        action="sleep",
    )
)

print("\nRunning 5 cycles...\n")

for i in range(1, 6):

    result = entity.cycle()

    decision = result[
        "decision"
    ]

    print(
        f"Cycle {i:02d} "
        f"| mode={decision.mode:<7} "
        f"| action={decision.action:<6} "
        f"| score={decision.score}"
    )

    print(
        f"  state="
        f"{result['transition']['state_after']}"
    )

    print(
        f"  LR cells="
        f"{knowledge.cell_count}"
    )

print("\nFinal State")
print(
    environment.state.as_dict()
)

print(
    "\nExperiences:",
    len(entity.experiences),
)

print(
    "LR cells:",
    knowledge.cell_count,
)