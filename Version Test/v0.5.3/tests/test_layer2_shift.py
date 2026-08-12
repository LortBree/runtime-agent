from layer2_knowledge import LearnedRelationStore


knowledge = LearnedRelationStore()

# ================================================================
# FIXED STATE CONTEXT
# ================================================================

state = {
    "hunger": 80.0,
    "thirst": 40.0,
    "energy": 80.0,
    "curiosity": 50.0,
}

action = "sleep"


# ================================================================
# PHASE 1 — OLD DYNAMICS
# sleep -> energy INC_LARGE
# ================================================================

old_state = {
    "hunger": 82.0,
    "thirst": 42.5,
    "energy": 100.0,
    "curiosity": 49.5,
}

print("=" * 72)
print("LAYER 2 — ENVIRONMENT SHIFT TEST")
print("=" * 72)

print("\nPHASE 1 — OLD DYNAMICS")
print("sleep -> energy +20")

for i in range(1, 6):

    updates = knowledge.update(
        state_before=state,
        action=action,
        state_after=old_state,
    )

    energy = next(
        item
        for item in updates
        if item["variable"] == "energy"
    )

    print(
        f"{i:02d} "
        f"observed={energy['observed_effect']:<10} "
        f"learned={energy['learned_effect']:<10} "
        f"confidence={energy['confidence']:.3f} "
        f"label={energy['label']}"
    )


# ================================================================
# PHASE 2 — ENVIRONMENT SHIFT
# sleep -> energy +5
# ================================================================

shifted_state = {
    "hunger": 82.0,
    "thirst": 42.5,
    "energy": 85.0,
    "curiosity": 49.5,
}

print("\nPHASE 2 — ENVIRONMENT SHIFT")
print("sleep -> energy +5")

for i in range(1, 21):

    updates = knowledge.update(
        state_before=state,
        action=action,
        state_after=shifted_state,
    )

    energy = next(
        item
        for item in updates
        if item["variable"] == "energy"
    )

    cell = knowledge.query(
        state=state,
        action=action,
        variable="energy",
    )

    counts = cell["counts"]

    print(
        f"{i:02d} "
        f"observed={energy['observed_effect']:<10} "
        f"learned={energy['learned_effect']:<10} "
        f"confidence={energy['confidence']:.3f} "
        f"label={energy['label']:<7} "
        f"LARGE={counts.get('INC_LARGE', 0.0):6.3f} "
        f"SMALL={counts.get('INC_SMALL', 0.0):6.3f}"
    )


# ================================================================
# FINAL RELATION
# ================================================================

final = knowledge.query(
    state=state,
    action=action,
    variable="energy",
)

print("\nFINAL RELATION")
print("-" * 72)

print(
    f"magnitude     : {final['magnitude']}"
)

print(
    f"confidence    : {final['confidence']:.3f}"
)

print(
    f"label         : {final['label']}"
)

print(
    f"support       : {final['support']:.3f}"
)

print(
    f"contradiction : {final['contradiction']:.3f}"
)

print(
    f"counts        : {final['counts']}"
)