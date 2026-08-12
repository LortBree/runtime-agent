from layer3_entity.saturation import (
    DEFAULT_NOVELTY_THRESHOLD,
    SaturationPolicy,
    novelty_from_evidence,
    saturation_from_evidence,
)


# ================================================================
# BASIC NOVELTY
# ================================================================

assert (
    novelty_from_evidence(
        0.0
    )
    == 1.0
)

assert abs(
    novelty_from_evidence(
        5.0
    )
    - 0.5
) < 1e-9

assert abs(
    novelty_from_evidence(
        15.0
    )
    - 0.25
) < 1e-9


# ================================================================
# DEFAULT THRESHOLD
# ================================================================

assert (
    DEFAULT_NOVELTY_THRESHOLD
    == 0.25
)


# ================================================================
# NOT SATURATED
# ================================================================

policy = SaturationPolicy(
    threshold=0.25
)

result = policy.evaluate(
    [
        0.60,
        0.40,
        0.20,
    ]
)

assert result.max_novelty == 0.60
assert result.saturated is False
assert policy.should_explore(
    [
        0.60,
        0.40,
        0.20,
    ]
) is True


# ================================================================
# SATURATED
# ================================================================

result = policy.evaluate(
    [
        0.20,
        0.18,
        0.21,
    ]
)

assert result.max_novelty == 0.21
assert result.saturated is True
assert policy.is_saturated(
    [
        0.20,
        0.18,
        0.21,
    ]
) is True


# ================================================================
# EXACT THRESHOLD
# ================================================================

result = policy.evaluate(
    [
        0.25,
        0.20,
    ]
)

assert result.saturated is True


# ================================================================
# EVIDENCE-BASED SATURATION
# ================================================================

result = saturation_from_evidence(
    evidences=[
        20.0,
        18.0,
        15.0,
    ],
    threshold=0.25,
    k=5.0,
)

# E=15 -> novelty=0.25
# Therefore max novelty is 0.25 and the regime is saturated.
assert abs(
    result.max_novelty
    - 0.25
) < 1e-9

assert result.saturated is True


# ================================================================
# PRINT
# ================================================================

print(
    "Novelty values:"
)

for evidence in (
    0.0,
    1.0,
    5.0,
    10.0,
    15.0,
    20.0,
):

    novelty = novelty_from_evidence(
        evidence
    )

    print(
        f"evidence={evidence:5.1f} "
        f"novelty={novelty:.3f}"
    )

print()
print(
    f"Threshold = "
    f"{DEFAULT_NOVELTY_THRESHOLD:.2f}"
)

print(
    "PASS"
)