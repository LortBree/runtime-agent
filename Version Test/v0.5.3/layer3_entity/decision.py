from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .exploration import ExplorationPolicy
from .saturation import SaturationPolicy


# ================================================================
# STATE VARIABLES
# ================================================================

STATE_VARIABLES = (
    "hunger",
    "thirst",
    "energy",
    "curiosity",
)


# ================================================================
# ACTION ORDER
# ================================================================

DEFAULT_ACTION_ORDER = (
    "eat",
    "drink",
    "sleep",
    "work",
    "idle",
)


# ================================================================
# MAGNITUDE VALUE
# ================================================================

MAGNITUDE_VALUE = {
    "DEC_LARGE": 4.0,
    "DEC_SMALL": 2.0,
    "NONE": 0.0,
    "INC_SMALL": 2.0,
    "INC_LARGE": 4.0,
}


# ================================================================
# VARIABLE DIRECTION
# ================================================================

VARIABLE_DIRECTION = {
    "hunger": -1.0,
    "thirst": -1.0,
    "energy": 1.0,
    "curiosity": 1.0,
}


# ================================================================
# CONTEXT WEIGHTS
# ================================================================

CONTEXT_WEIGHT = {
    "hunger": {
        "LOW": 0.5,
        "HIGH": 2.0,
    },

    "thirst": {
        "LOW": 0.5,
        "HIGH": 2.0,
    },

    "energy": {
        "LOW": 2.0,
        "HIGH": 0.5,
    },

    "curiosity": {
        "LOW": 1.0,
        "HIGH": 0.5,
    },
}


# ================================================================
# ACTION SCORE
# ================================================================

@dataclass(frozen=True)
class ActionScore:
    action: str
    score: float
    harm_score: float
    confidence_mean: float
    known_variables: int
    unknown_variables: int
    action_known: bool
    context_known: bool


# ================================================================
# DECISION
# ================================================================

@dataclass(frozen=True)
class Decision:
    action: str
    mode: str
    score: float | None
    reason: str
    evaluations: tuple[ActionScore, ...]


# ================================================================
# DECISION ENGINE
# ================================================================

class DecisionEngine:
    """
    Layer 3 — Decision Engine.

    V0.5.3 policy:

        1. Positive current-context score
           -> exploit.

        2. No positive score AND exploration still meaningful
           -> novelty-based exploration.

        3. No positive score AND exploration saturated
           -> least-harm action.

        4. If no current-context harm estimate exists
           -> deterministic fallback.

    Main utility/scoring formula remains unchanged.

    V0.5.3 adds a separate harm objective only for the
    saturated no-positive regime.

    No RL.
    No Q-value.
    No reward learning.
    No policy gradient.
    """

    def __init__(
        self,
        action_order: Sequence[str] = DEFAULT_ACTION_ORDER,
        context_weight: Mapping[
            str,
            Mapping[str, float],
        ] = CONTEXT_WEIGHT,
        explorer: ExplorationPolicy | None = None,
        saturation: SaturationPolicy | None = None,
    ) -> None:

        self.action_order = tuple(
            action_order
        )

        if not self.action_order:
            raise ValueError(
                "action_order must not be empty."
            )

        self.rank = {
            action: index
            for index, action
            in enumerate(
                self.action_order
            )
        }

        self.context_weight = (
            context_weight
        )

        self.explorer = (
            explorer
            if explorer is not None
            else ExplorationPolicy(
                k=5.0
            )
        )

        self.saturation = (
            saturation
            if saturation is not None
            else SaturationPolicy(
                threshold=0.25
            )
        )

    # ============================================================
    # STATE BUCKET
    # ============================================================

    @staticmethod
    def state_bucket(
        state: Mapping[str, float],
    ) -> dict[str, str]:

        return {
            variable: (
                "HIGH"
                if float(
                    state[variable]
                ) >= 50.0
                else "LOW"
            )
            for variable
            in STATE_VARIABLES
        }

    # ============================================================
    # RELATION STATUS
    # ============================================================

    @staticmethod
    def relation_known(
        relation: Mapping[str, object],
    ) -> bool:

        if not relation.get(
            "known",
            False,
        ):
            return False

        magnitude = relation.get(
            "magnitude"
        )

        return magnitude is not None

    # ============================================================
    # ACTION-LEVEL KNOWLEDGE
    # ============================================================

    @staticmethod
    def action_is_known(
        action_relation: Mapping[str, object],
    ) -> bool:
        """
        True when this action has been observed in at least one
        state context.
        """

        return bool(
            action_relation.get(
                "action_known",
                False,
            )
        )

    # ============================================================
    # MAGNITUDE DESIRABILITY
    # ============================================================

    @staticmethod
    def magnitude_desirability(
        variable: str,
        magnitude: str,
    ) -> float:

        magnitude_value = (
            MAGNITUDE_VALUE.get(
                magnitude,
                0.0,
            )
        )

        direction = (
            VARIABLE_DIRECTION[
                variable
            ]
        )

        # Hunger / thirst:
        # decrease = desirable
        if direction < 0.0:

            if magnitude.startswith(
                "DEC"
            ):
                return magnitude_value

            if magnitude.startswith(
                "INC"
            ):
                return -magnitude_value

            return 0.0

        # Energy / curiosity:
        # increase = desirable
        if magnitude.startswith(
            "INC"
        ):
            return magnitude_value

        if magnitude.startswith(
            "DEC"
        ):
            return -magnitude_value

        return 0.0

    # ============================================================
    # SCORE ONE RELATION
    # ============================================================

    def score_relation(
        self,
        variable: str,
        bucket: str,
        relation: Mapping[str, object],
    ) -> tuple[float, float, bool]:
        """
        Return:

            (utility_contribution, harm_contribution, known)

        Harm is only the negative side of desirability:

            harm =
                context_weight
                * max(0, -desirability)
                * confidence
        """

        if not self.relation_known(
            relation
        ):
            return 0.0, 0.0, False

        magnitude = str(
            relation["magnitude"]
        )

        confidence = float(
            relation.get(
                "confidence",
                0.0,
            )
        )

        desirability = (
            self.magnitude_desirability(
                variable,
                magnitude,
            )
        )

        context_weight = float(
            self.context_weight[
                variable
            ][bucket]
        )

        utility_contribution = (
            context_weight
            * desirability
            * confidence
        )

        harm_contribution = (
            context_weight
            * max(
                0.0,
                -desirability,
            )
            * confidence
        )

        return (
            utility_contribution,
            harm_contribution,
            True,
        )

    # ============================================================
    # SCORE ONE ACTION
    # ============================================================

    def score_action(
        self,
        state: Mapping[str, float],
        action: str,
        relation_result: Mapping[str, object],
    ) -> ActionScore:

        buckets = self.state_bucket(
            state
        )

        effects = relation_result.get(
            "effects",
            [],
        )

        effect_by_variable = {
            str(
                effect.get(
                    "variable"
                )
            ): effect
            for effect
            in effects
        }

        total_score = 0.0
        total_harm = 0.0

        confidences: list[float] = []

        known_variables = 0
        unknown_variables = 0

        for variable in STATE_VARIABLES:

            relation = (
                effect_by_variable.get(
                    variable,
                    {},
                )
            )

            (
                contribution,
                harm,
                known,
            ) = self.score_relation(
                variable=variable,
                bucket=buckets[
                    variable
                ],
                relation=relation,
            )

            total_score += contribution
            total_harm += harm

            if known:

                known_variables += 1

                confidences.append(
                    float(
                        relation.get(
                            "confidence",
                            0.0,
                        )
                    )
                )

            else:

                unknown_variables += 1

        confidence_mean = (
            sum(confidences)
            / len(confidences)
            if confidences
            else 0.0
        )

        action_known = (
            self.action_is_known(
                relation_result
            )
        )

        context_known = (
            known_variables > 0
        )

        return ActionScore(
            action=action,
            score=total_score,
            harm_score=total_harm,
            confidence_mean=(
                confidence_mean
            ),
            known_variables=(
                known_variables
            ),
            unknown_variables=(
                unknown_variables
            ),
            action_known=(
                action_known
            ),
            context_known=(
                context_known
            ),
        )

    # ============================================================
    # EVALUATE ALL ACTIONS
    # ============================================================

    def evaluate_actions(
        self,
        state: Mapping[str, float],
        knowledge: Mapping[
            str,
            Mapping[str, object],
        ],
    ) -> tuple[ActionScore, ...]:

        results: list[ActionScore] = []

        for action in self.action_order:

            relation_result = (
                knowledge.get(
                    action,
                    {
                        "action_known": False,
                        "known": False,
                        "effects": [],
                    },
                )
            )

            results.append(
                self.score_action(
                    state=state,
                    action=action,
                    relation_result=(
                        relation_result
                    ),
                )
            )

        return tuple(
            sorted(
                results,
                key=lambda item: (
                    -item.score,
                    -item.confidence_mean,
                    self.rank[
                        item.action
                    ],
                ),
            )
        )

    # ============================================================
    # BUILD EXPLORATION EVALUATIONS
    # ============================================================

    @staticmethod
    def _build_exploration_evaluations(
        evaluations: Sequence[ActionScore],
        knowledge: Mapping[
            str,
            Mapping[str, object],
        ],
    ) -> dict[str, dict]:

        result: dict[str, dict] = {}

        for evaluation in evaluations:

            result[
                evaluation.action
            ] = knowledge.get(
                evaluation.action,
                {},
            )

        return result

    # ============================================================
    # NOVELTY VALUES
    # ============================================================

    def _novelty_values(
        self,
        evaluations: Sequence[ActionScore],
        knowledge: Mapping[
            str,
            Mapping[str, object],
        ],
    ) -> dict[str, float]:

        exploration_evaluations = (
            self._build_exploration_evaluations(
                evaluations=evaluations,
                knowledge=knowledge,
            )
        )

        candidates = (
            self.explorer.candidates(
                exploration_evaluations
            )
        )

        return {
            candidate.action:
                candidate.novelty
            for candidate
            in candidates
        }

    # ============================================================
    # LEAST HARM
    # ============================================================

    def _select_least_harm(
        self,
        evaluations: Sequence[ActionScore],
    ) -> ActionScore | None:
        """
        Select the current-context known action with minimum
        predicted harm.

        We deliberately require context_known=True because an
        unknown current-context relation cannot provide a valid
        harm estimate.
        """

        candidates = [
            item
            for item
            in evaluations
            if item.context_known
        ]

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda item: (
                item.harm_score,
                -item.confidence_mean,
                self.rank[
                    item.action
                ],
            ),
        )

    # ============================================================
    # SELECT ACTION
    # ============================================================

    def select_action(
        self,
        state: Mapping[str, float],
        knowledge: Mapping[
            str,
            Mapping[str, object],
        ],
        explore_unknown: bool = True,
    ) -> Decision:
        """
        V0.5.3 selection hierarchy:

            1. Positive score
               -> exploit

            2. No positive + novelty unsaturated
               -> explore

            3. No positive + novelty saturated
               -> least harm

            4. No usable harm estimate
               -> fallback

        `explore_unknown` is retained as an API compatibility
        parameter. When False, exploration is skipped and the
        engine goes directly to least-harm/fallback.
        """

        evaluations = (
            self.evaluate_actions(
                state,
                knowledge,
            )
        )

        # --------------------------------------------------------
        # 1. POSITIVE CURRENT-CONTEXT SCORE
        # --------------------------------------------------------

        known_context = [
            item
            for item in evaluations
            if item.context_known
        ]

        positive_known = [
            item
            for item in known_context
            if item.score > 0.0
        ]

        if positive_known:

            selected = positive_known[0]

            return Decision(
                action=selected.action,
                mode="exploit",
                score=selected.score,
                reason=(
                    "highest positive "
                    "current-context score"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 2. NOVELTY / SATURATION
        # --------------------------------------------------------

        novelty_values = (
            self._novelty_values(
                evaluations=evaluations,
                knowledge=knowledge,
            )
        )

        novelty_list = tuple(
            novelty_values.values()
        )

        # --------------------------------------------------------
        # 2A. EXPLORE WHILE NOVELTY IS MEANINGFUL
        # --------------------------------------------------------

        if (
            explore_unknown
            and novelty_list
            and self.saturation.should_explore(
                novelty_list
            )
        ):

            exploration_evaluations = (
                self._build_exploration_evaluations(
                    evaluations=evaluations,
                    knowledge=knowledge,
                )
            )

            candidate = (
                self.explorer.select(
                    exploration_evaluations
                )
            )

            return Decision(
                action=candidate.action,
                mode="explore",
                score=None,
                reason=(
                    "no positive "
                    "current-context score; "
                    "novelty not saturated"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 3. SATURATED → LEAST HARM
        # --------------------------------------------------------

        least_harm = (
            self._select_least_harm(
                evaluations
            )
        )

        if least_harm is not None:

            return Decision(
                action=least_harm.action,
                mode="neutral",
                score=least_harm.score,
                reason=(
                    "no positive "
                    "current-context score; "
                    "exploration saturated; "
                    "selected least-harm action"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 4. TRUE FALLBACK
        # --------------------------------------------------------

        fallback = self.action_order[-1]

        return Decision(
            action=fallback,
            mode="fallback",
            score=0.0,
            reason=(
                "no positive current-context "
                "score; exploration saturated; "
                "no current-context harm estimate"
            ),
            evaluations=evaluations,
        )