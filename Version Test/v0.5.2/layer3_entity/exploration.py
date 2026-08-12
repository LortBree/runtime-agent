# layer3_entity/exploration.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class ExplorationCandidate:
    """
    One action candidate for the no-positive-score regime.
    """

    action: str
    novelty: float
    evidence: float


class ExplorationPolicy:
    """
    V0.5.2 exploratory policy.

    Purpose
    -------
    Used only when the normal Decision layer finds no action
    with positive utility/score.

    Principle
    ---------
    Prefer actions whose current-context knowledge is less mature.

    Novelty function:

        N(a|S) = 1 - E / (E + k)

    where:
        E = total decayed evidence for the action in the
            current state context
        k = smoothing constant

    Properties:
        E = 0       -> novelty = 1.0
        E -> inf    -> novelty -> 0.0

    This module does NOT:
        - calculate survival utility
        - change Decision scoring
        - modify LR
        - update knowledge
        - execute actions
        - use rewards / Q-values / RL

    It only ranks exploration candidates.
    """

    def __init__(
        self,
        k: float = 5.0,
    ) -> None:
        if k <= 0.0:
            raise ValueError(
                "k must be > 0."
            )

        self.k = float(k)

    # ============================================================
    # EVIDENCE EXTRACTION
    # ============================================================

    @staticmethod
    def _extract_evidence(
        evaluation: dict[str, Any],
    ) -> float:
        """
        Extract total current-context evidence from an action
        evaluation.

        Priority:
            1. total_evidence from effects
            2. support + contradiction from effects
            3. zero

        The maximum value across known effects is used because
        each action may have several state-variable relations.
        """

        effects = evaluation.get(
            "effects",
            [],
        )

        if not effects:
            return 0.0

        evidence_values: list[float] = []

        for effect in effects:

            if not effect.get(
                "known",
                False,
            ):
                continue

            total_evidence = effect.get(
                "total_evidence"
            )

            if total_evidence is not None:
                evidence_values.append(
                    max(
                        0.0,
                        float(total_evidence),
                    )
                )
                continue

            support = float(
                effect.get(
                    "support",
                    0.0,
                )
            )

            contradiction = float(
                effect.get(
                    "contradiction",
                    0.0,
                )
            )

            evidence_values.append(
                max(
                    0.0,
                    support + contradiction,
                )
            )

        if not evidence_values:
            return 0.0

        return max(
            evidence_values
        )

    # ============================================================
    # NOVELTY
    # ============================================================

    def novelty(
        self,
        evidence: float,
    ) -> float:
        """
        Compute novelty from evidence maturity.

            novelty = 1 - E / (E + k)

        Equivalent stable form:

            novelty = k / (E + k)
        """

        if evidence < 0.0:
            raise ValueError(
                "evidence must be >= 0."
            )

        return self.k / (
            evidence + self.k
        )

    # ============================================================
    # BUILD CANDIDATES
    # ============================================================

    def candidates(
        self,
        evaluations: dict[str, dict[str, Any]]
        | Iterable[tuple[str, dict[str, Any]]],
    ) -> list[ExplorationCandidate]:
        """
        Build exploration candidates.

        Unknown actions are treated as maximally novel.

        Known actions are ranked by current-context evidence.
        """

        if isinstance(
            evaluations,
            dict,
        ):
            items = evaluations.items()
        else:
            items = evaluations

        candidates: list[
            ExplorationCandidate
        ] = []

        for action, evaluation in items:

            evidence = (
                self._extract_evidence(
                    evaluation
                )
            )

            novelty = self.novelty(
                evidence
            )

            candidates.append(
                ExplorationCandidate(
                    action=action,
                    novelty=novelty,
                    evidence=evidence,
                )
            )

        return candidates

    # ============================================================
    # SELECT
    # ============================================================

    def select(
        self,
        evaluations: dict[str, dict[str, Any]]
        | Iterable[tuple[str, dict[str, Any]]],
    ) -> ExplorationCandidate:
        """
        Select the most novel action.

        Tie-breaking is deterministic:
            1. higher novelty
            2. lower evidence
            3. action name

        Deterministic tie-breaking keeps experiments reproducible.
        """

        candidates = self.candidates(
            evaluations
        )

        if not candidates:
            raise ValueError(
                "No exploration candidates available."
            )

        return min(
            candidates,
            key=lambda candidate: (
                -candidate.novelty,
                candidate.evidence,
                candidate.action,
            ),
        )