from layer1_environment import (
    State,
)

from layer2_knowledge import (
    LearnedRelationStore,
)


knowledge = LearnedRelationStore()

before = State(
    hunger=80.0,
    thirst=40.0,
    energy=80.0,
    curiosity=50.0,
)

after = State(
    hunger=82.0,
    thirst=42.5,
    energy=100.0,
    curiosity=49.5,
)

print("=" * 72)
print("KNOWLEDGE LAYER — V0.5.1")
print("=" * 72)

print("\nExperience:")
print("Action: sleep()")

print("\nLearning...")

updates = knowledge.update(
    state_before=before.as_dict(),
    action="sleep",
    state_after=after.as_dict(),
)

for item in updates:
    print(
        f"{item['variable']:<10} "
        f"delta={item['delta']:+6.2f} "
        f"observed={item['observed_effect']:<10} "
        f"learned={item['learned_effect']:<10} "
        f"confidence={item['confidence']:.3f} "
        f"label={item['label']}"
    )

print("\nQuery:")
print(
    knowledge.evaluate_action(
        state=before.as_dict(),
        action="sleep",
    )
)

print("\nSummary:")
print(
    knowledge.summary()
)