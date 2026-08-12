from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


STATE_VARIABLES = (
    "hunger",
    "thirst",
    "energy",
    "curiosity",
)

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


@dataclass(frozen=True)
class ActionScore:
    action: str
    score: float
    confidence_mean: float
    known_variables: int
    unknown_variables: int
    action_known: bool
    context_known: bool


@dataclass(frozen=True)
class Decision:
    action: str
    mode: str
    score: float | None
    reason: str
    evaluations: tuple[ActionScore, ...]


class DecisionEngine:

    def __init__(
        self,
        action_order: Sequence[str] = DEFAULT_ACTION_ORDER,
        context_weight: Mapping[
            str,
            Mapping[str, float],
        ] = CONTEXT_WEIGHT,
    ) -> None:

        self.action_order = tuple(
            action_order
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

    # ============================================================
    # STATE BUCKET
    # ============================================================

    @staticmethod
    def state_bucket(
        state: Mapping[str, float],
    ) -> dict[str, str]:

        return {
            variable:
                (
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

        This is different from whether the CURRENT context is known.
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
    ) -> tuple[float, bool]:

        if not self.relation_known(
            relation
        ):
            return 0.0, False

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

        contribution = (
            context_weight
            * desirability
            * confidence
        )

        return contribution, True

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
            str(effect.get("variable")):
                effect
            for effect in effects
        }

        total = 0.0
        confidences = []

        known_variables = 0
        unknown_variables = 0

        for variable in STATE_VARIABLES:

            relation = (
                effect_by_variable.get(
                    variable,
                    {},
                )
            )

            contribution, known = (
                self.score_relation(
                    variable=variable,
                    bucket=buckets[
                        variable
                    ],
                    relation=relation,
                )
            )

            total += contribution

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
            score=total,
            confidence_mean=
                confidence_mean,
            known_variables=
                known_variables,
            unknown_variables=
                unknown_variables,
            action_known=
                action_known,
            context_known=
                context_known,
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

        results = []

        for action in self.action_order:

            relation_result = (
                knowledge.get(
                    action,
                    {
                        "action_known":
                            False,

                        "known":
                            False,

                        "effects":
                            [],
                    },
                )
            )

            results.append(
                self.score_action(
                    state=state,
                    action=action,
                    relation_result=
                        relation_result,
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

        evaluations = (
            self.evaluate_actions(
                state,
                knowledge,
            )
        )

        # --------------------------------------------------------
        # CURRENT CONTEXT KNOWN
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

        # --------------------------------------------------------
        # 1. EXPLOIT KNOWN CURRENT-CONTEXT RELATION
        # --------------------------------------------------------

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
        # ACTION-LEVEL UNKNOWN
        # --------------------------------------------------------
        #
        # Only explore an action that has NEVER been observed.
        #
        # An action with no relation in the current context but
        # known elsewhere is NOT treated as a brand-new action.
        # --------------------------------------------------------

        action_unknown = [
            item
            for item in evaluations
            if not item.action_known
        ]

        if (
            explore_unknown
            and action_unknown
        ):

            selected = action_unknown[0]

            return Decision(
                action=selected.action,
                mode="explore",
                score=None,
                reason=(
                    "action has no learned "
                    "relation in any context"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 3. BEST KNOWN CURRENT CONTEXT
        # --------------------------------------------------------

        if known_context:

            selected = max(
                known_context,
                key=lambda item: (
                    item.score,
                    item.confidence_mean,
                    -self.rank[
                        item.action
                    ],
                ),
            )

            return Decision(
                action=selected.action,
                mode="exploit",
                score=selected.score,
                reason=(
                    "highest current-context "
                    "known score"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 4. ACTION KNOWN, CURRENT CONTEXT UNKNOWN
        # --------------------------------------------------------
        #
        # If all actions are known globally but none has evidence
        # in the current state context, choose a deterministic
        # known action instead of repeatedly calling it "explore".
        #
        # This is deliberately conservative until we have a
        # separate interpolation/generalization mechanism.
        # --------------------------------------------------------

        action_known = [
            item
            for item in evaluations
            if item.action_known
        ]

        if action_known:

            selected = action_known[0]

            return Decision(
                action=selected.action,
                mode="exploit",
                score=selected.score,
                reason=(
                    "action known globally; "
                    "current context unknown"
                ),
                evaluations=evaluations,
            )

        # --------------------------------------------------------
        # 5. TRUE FALLBACK
        # --------------------------------------------------------

        fallback = self.action_order[-1]

        return Decision(
            action=fallback,
            mode="fallback",
            score=0.0,
            reason=(
                "no learned action relation "
                "available"
            ),
            evaluations=evaluations,
        )