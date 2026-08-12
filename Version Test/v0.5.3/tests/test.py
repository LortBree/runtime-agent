from layer1_environment import State
from layer2_knowledge import LearnedRelationStore


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

for i in range(1, 6):
    updates = knowledge.update(
        state_before=before.as_dict(),
        action="sleep",
        state_after=after.as_dict(),
    )

    print(f"\nExperience {i}")

    for item in updates:
        print(
            f"{item['variable']:<10} "
            f"observed={item['observed_effect']:<10} "
            f"learned={item['learned_effect']:<10} "
            f"confidence={item['confidence']:.3f} "
            f"label={item['label']}"
        )