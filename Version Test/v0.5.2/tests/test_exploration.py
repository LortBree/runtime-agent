from layer3_entity.exploration import (
    ExplorationPolicy,
)


policy = ExplorationPolicy(
    k=5.0
)

evaluations = {
    "sleep": {
        "effects": [
            {
                "known": True,
                "support": 18.0,
                "contradiction": 0.5,
            }
        ]
    },
    "eat": {
        "effects": [
            {
                "known": True,
                "support": 3.0,
                "contradiction": 0.0,
            }
        ]
    },
    "drink": {
        "effects": [
            {
                "known": True,
                "support": 5.0,
                "contradiction": 0.0,
            }
        ]
    },
    "work": {
        "effects": [
            {
                "known": True,
                "support": 14.0,
                "contradiction": 0.0,
            }
        ]
    },
}

for candidate in policy.candidates(
    evaluations
):
    print(
        f"{candidate.action:<7} "
        f"evidence={candidate.evidence:6.2f} "
        f"novelty={candidate.novelty:.3f}"
    )

selected = policy.select(
    evaluations
)

print()
print(
    f"Selected: {selected.action}"
)

assert selected.action == "eat"

print("PASS")