from __future__ import annotations

from dataclasses import dataclass, field

from .bucketing import (
    EffectMagnitude,
)
from .config import (
    ALPHA,
    DECAY_GAMMA,
    SHOULD_THRESHOLD,
    UNKNOWN_THRESHOLD,
)


# ================================================================
# RELATION CELL
# ================================================================

@dataclass
class RelationCell:
    """
    One Learned Relation cell.

    Key context:

        (state_bucket, action, state_variable)

    Evidence is stored as five decayed counters.
    """

    counts: dict[str, float] = field(
        default_factory=lambda: {
            EffectMagnitude.DEC_LARGE.value: 0.0,
            EffectMagnitude.DEC_SMALL.value: 0.0,
            EffectMagnitude.NONE.value: 0.0,
            EffectMagnitude.INC_SMALL.value: 0.0,
            EffectMagnitude.INC_LARGE.value: 0.0,
        }
    )

    # ============================================================
    # UPDATE
    # ============================================================

    def update(
        self,
        observed: EffectMagnitude,
        gamma: float = DECAY_GAMMA,
    ) -> None:
        """
        Exponential-decay evidence update.

            count_m(t)
              =
            gamma * count_m(t-1)
            + indicator(m == observed)
        """

        if not 0.0 < gamma <= 1.0:
            raise ValueError(
                "gamma must be in (0, 1]"
            )

        for magnitude in list(
            self.counts.keys()
        ):
            self.counts[magnitude] *= gamma

        self.counts[
            observed.value
        ] += 1.0

    # ============================================================
    # SUPPORT
    # ============================================================

    @property
    def best_magnitude(
        self,
    ) -> EffectMagnitude:

        best_name = max(
            self.counts,
            key=self.counts.get,
        )

        return EffectMagnitude(
            best_name
        )

    @property
    def support(self) -> float:
        return self.counts[
            self.best_magnitude.value
        ]

    @property
    def total_evidence(self) -> float:
        return sum(
            self.counts.values()
        )

    @property
    def contradiction(self) -> float:
        return (
            self.total_evidence
            - self.support
        )

    # ============================================================
    # CONFIDENCE
    # ============================================================

    @property
    def confidence(self) -> float:
        """
        Laplace-smoothed confidence:

            C =
            (support + alpha)
            /
            (support + contradiction + 2*alpha)
        """

        denominator = (
            self.support
            + self.contradiction
            + 2.0 * ALPHA
        )

        if denominator <= 0.0:
            return 0.5

        return (
            self.support + ALPHA
        ) / denominator

    # ============================================================
    # SEMANTIC LABEL
    # ============================================================

    @property
    def semantic_label(self) -> str:

        confidence = self.confidence

        # No actual evidence.
        if self.total_evidence <= 0.0:
            return "unknown"

        if confidence < UNKNOWN_THRESHOLD:
            return "unknown"

        if confidence < SHOULD_THRESHOLD:
            return "may"

        return "should"

    # ============================================================
    # LEARNED RELATION
    # ============================================================

    def relation(self) -> dict:
        return {
            "magnitude":
                self.best_magnitude.value,

            "confidence":
                self.confidence,

            "label":
                self.semantic_label,

            "support":
                self.support,

            "contradiction":
                self.contradiction,

            "total_evidence":
                self.total_evidence,

            "counts":
                dict(self.counts),
        }

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self) -> dict:
        return {
            "counts":
                dict(self.counts),
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "RelationCell":

        cell = cls()

        counts = data.get(
            "counts",
            {},
        )

        for magnitude in cell.counts:

            cell.counts[magnitude] = float(
                counts.get(
                    magnitude,
                    0.0,
                )
            )

        return cell