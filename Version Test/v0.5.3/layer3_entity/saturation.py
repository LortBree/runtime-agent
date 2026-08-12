# layer3_entity/saturation.py

from __future__ import annotations

from dataclasses import dataclass


# ================================================================
# DEFAULT PARAMETERS
# ================================================================

DEFAULT_NOVELTY_THRESHOLD = 0.25


# ================================================================
# RESULT
# ================================================================

@dataclass(frozen=True)
class SaturationResult:
    """
    Result of novelty saturation analysis.
    """

    max_novelty: float
    threshold: float
    saturated: bool


# ================================================================
# SATURATION POLICY
# ================================================================

class SaturationPolicy:
    """
    V0.5.3 novelty saturation policy.

    Novelty is assumed to already be calculated by the caller.

    Decision rule:

        max_novelty > threshold
            -> exploration still meaningful

        max_novelty <= threshold
            -> exploration saturated
    """

    def __init__(
        self,
        threshold: float = DEFAULT_NOVELTY_THRESHOLD,
    ) -> None:

        if not 0.0 <= threshold <= 1.0:
            raise ValueError(
                "threshold must be between 0.0 and 1.0."
            )

        self.threshold = float(
            threshold
        )

    # ============================================================
    # EVALUATE
    # ============================================================

    def evaluate(
        self,
        novelties: list[float] | tuple[float, ...],
    ) -> SaturationResult:
        """
        Evaluate whether exploration is saturated.

        Parameters
        ----------
        novelties:
            Novelty values for the available actions.

        Returns
        -------
        SaturationResult

        Raises
        ------
        ValueError
            If no novelty values are provided or a value is outside
            [0.0, 1.0].
        """

        if not novelties:
            raise ValueError(
                "At least one novelty value is required."
            )

        for novelty in novelties:

            if not 0.0 <= float(novelty) <= 1.0:
                raise ValueError(
                    "novelty values must be between "
                    "0.0 and 1.0."
                )

        max_novelty = max(
            float(novelty)
            for novelty in novelties
        )

        saturated = (
            max_novelty
            <= self.threshold
        )

        return SaturationResult(
            max_novelty=max_novelty,
            threshold=self.threshold,
            saturated=saturated,
        )

    # ============================================================
    # BOOLEAN HELPERS
    # ============================================================

    def is_saturated(
        self,
        novelties: list[float] | tuple[float, ...],
    ) -> bool:
        """
        Return True when exploration is saturated.
        """

        return self.evaluate(
            novelties
        ).saturated

    def should_explore(
        self,
        novelties: list[float] | tuple[float, ...],
    ) -> bool:
        """
        Return True when exploration is still meaningful.
        """

        return not self.is_saturated(
            novelties
        )


# ================================================================
# NOVELTY / EVIDENCE CONVERSION
# ================================================================

def novelty_from_evidence(
    evidence: float,
    k: float = 5.0,
) -> float:
    """
    Convert evidence maturity into novelty.

        N(E) = k / (E + k)

    Properties
    ----------
    E = 0
        -> novelty = 1.0

    E -> infinity
        -> novelty -> 0.0
    """

    evidence = float(
        evidence
    )

    k = float(
        k
    )

    if evidence < 0.0:
        raise ValueError(
            "evidence must be >= 0.0."
        )

    if k <= 0.0:
        raise ValueError(
            "k must be > 0.0."
        )

    return k / (
        evidence + k
    )


def saturation_from_evidence(
    evidences: list[float] | tuple[float, ...],
    threshold: float = DEFAULT_NOVELTY_THRESHOLD,
    k: float = 5.0,
) -> SaturationResult:
    """
    Convenience function.

    Converts evidence values into novelty values and evaluates
    saturation.
    """

    novelties = [
        novelty_from_evidence(
            evidence=evidence,
            k=k,
        )
        for evidence in evidences
    ]

    policy = SaturationPolicy(
        threshold=threshold,
    )

    return policy.evaluate(
        novelties
    )