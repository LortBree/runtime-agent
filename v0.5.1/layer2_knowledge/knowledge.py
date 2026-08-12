from __future__ import annotations

from .bucketing import (
    bucket_effect,
    bucket_state,
)
from .config import (
    ACTIONS,
    STATE_VARIABLES,
)
from .relation import RelationCell


class LearnedRelationStore:
    """
    Layer 2 — Learned Relational Knowledge.

    Relation key:

        (
            state_bucket,
            action,
            state_variable
        )

    Example:

        (
            ("HIGH", "LOW", "HIGH", "LOW"),
            "sleep",
            "energy"
        )

    Each cell stores evidence for five effect magnitudes:

        DEC_LARGE
        DEC_SMALL
        NONE
        INC_SMALL
        INC_LARGE
    """

    def __init__(self) -> None:
        self.cells: dict[
            tuple[
                tuple[str, ...],
                str,
                str,
            ],
            RelationCell,
        ] = {}

    # ============================================================
    # KEY
    # ============================================================

    @staticmethod
    def make_key(
        state_bucket: tuple[str, ...],
        action: str,
        variable: str,
    ) -> tuple[
        tuple[str, ...],
        str,
        str,
    ]:
        return (
            tuple(state_bucket),
            action,
            variable,
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    @staticmethod
    def _validate_action(
        action: str,
    ) -> None:

        if action not in ACTIONS:
            raise ValueError(
                f"Unknown action: {action!r}. "
                f"Available actions: {ACTIONS}"
            )

    @staticmethod
    def _validate_variable(
        variable: str,
    ) -> None:

        if variable not in STATE_VARIABLES:
            raise ValueError(
                f"Unknown state variable: {variable!r}. "
                f"Available variables: {STATE_VARIABLES}"
            )

    # ============================================================
    # CELL ACCESS
    # ============================================================

    def get_cell(
        self,
        state_bucket: tuple[str, ...],
        action: str,
        variable: str,
    ) -> RelationCell | None:

        self._validate_action(action)
        self._validate_variable(variable)

        key = self.make_key(
            state_bucket,
            action,
            variable,
        )

        return self.cells.get(key)

    def get_or_create_cell(
        self,
        state_bucket: tuple[str, ...],
        action: str,
        variable: str,
    ) -> RelationCell:

        self._validate_action(action)
        self._validate_variable(variable)

        key = self.make_key(
            state_bucket,
            action,
            variable,
        )

        if key not in self.cells:
            self.cells[key] = RelationCell()

        return self.cells[key]

    # ============================================================
    # ACTION-LEVEL KNOWLEDGE
    # ============================================================

    def action_is_known(
        self,
        action: str,
    ) -> bool:
        """
        Return True when this action has been observed in at least
        one state context.

        This is intentionally different from context-level knowledge.

        Example:

            eat may be known globally,
            while eat in the current state bucket may be unknown.
        """

        self._validate_action(action)

        return any(
            key[1] == action
            for key in self.cells
        )

    # ============================================================
    # LEARN
    # ============================================================

    def update(
        self,
        state_before: dict,
        action: str,
        state_after: dict,
    ) -> list[dict]:
        """
        Convert one experience:

            S_t, A_t, S_{t+1}

        into four LR updates.

        Process:

            state_before
                ↓
            state bucket
                ↓
            delta per variable
                ↓
            effect magnitude
                ↓
            decayed counter update
        """

        self._validate_action(action)

        state_bucket = bucket_state(
            state_before
        )

        updates: list[dict] = []

        for variable in STATE_VARIABLES:

            before = float(
                state_before[variable]
            )

            after = float(
                state_after[variable]
            )

            delta = after - before

            observed_effect = bucket_effect(
                delta
            )

            cell = self.get_or_create_cell(
                state_bucket=state_bucket,
                action=action,
                variable=variable,
            )

            cell.update(
                observed_effect
            )

            relation = cell.relation()

            updates.append(
                {
                    "state_bucket":
                        state_bucket,

                    "action":
                        action,

                    "variable":
                        variable,

                    "delta":
                        delta,

                    "observed_effect":
                        observed_effect.value,

                    "learned_effect":
                        relation["magnitude"],

                    "confidence":
                        relation["confidence"],

                    "label":
                        relation["label"],

                    "support":
                        relation["support"],

                    "contradiction":
                        relation["contradiction"],

                    "counts":
                        relation["counts"],
                }
            )

        return updates

    # ============================================================
    # QUERY ONE RELATION
    # ============================================================

    def query(
        self,
        state: dict,
        action: str,
        variable: str,
    ) -> dict:

        self._validate_action(action)
        self._validate_variable(variable)

        state_bucket = bucket_state(
            state
        )

        cell = self.get_cell(
            state_bucket,
            action,
            variable,
        )

        # --------------------------------------------------------
        # Unknown
        # --------------------------------------------------------

        if cell is None:

            return {
                "state_bucket":
                    state_bucket,

                "action":
                    action,

                "variable":
                    variable,

                "magnitude":
                    None,

                "confidence":
                    0.5,

                "label":
                    "unknown",

                "known":
                    False,

                "support":
                    0.0,

                "contradiction":
                    0.0,

                "total_evidence":
                    0.0,

                "counts":
                    {},
            }

        # --------------------------------------------------------
        # Known / learned
        # --------------------------------------------------------

        relation = cell.relation()

        return {
            "state_bucket":
                state_bucket,

            "action":
                action,

            "variable":
                variable,

            "magnitude":
                relation["magnitude"],

            "confidence":
                relation["confidence"],

            "label":
                relation["label"],

            "known":
                relation["label"] != "unknown",

            "support":
                relation["support"],

            "contradiction":
                relation["contradiction"],

            "total_evidence":
                relation["total_evidence"],

            "counts":
                relation["counts"],
        }

    # ============================================================
    # QUERY ONE ACTION
    # ============================================================

    def evaluate_action(
        self,
        state: dict,
        action: str,
    ) -> dict:
        """
        Return all four state-variable relations for one action.

        Two levels of knowledge are exposed:

            action_known
                -> action has been observed in any context

            known
                -> current state context has at least one
                   learned relation for this action
        """

        self._validate_action(action)

        state_bucket = bucket_state(
            state
        )

        relations = []

        for variable in STATE_VARIABLES:

            relations.append(
                self.query(
                    state=state,
                    action=action,
                    variable=variable,
                )
            )

        known_count = sum(
            1
            for relation in relations
            if relation["known"]
        )

        action_known = (
            self.action_is_known(
                action
            )
        )

        return {
            "state_bucket":
                state_bucket,

            "action":
                action,

            # Action-level knowledge:
            # has this action appeared in ANY context?
            "action_known":
                action_known,

            # Context-level knowledge:
            # does this action have a relation in the
            # CURRENT state bucket?
            "known":
                known_count > 0,

            "known_count":
                known_count,

            "effects":
                relations,
        }

    
    # ============================================================
    # QUERY ALL ACTIONS
    # ============================================================

    def evaluate_all_actions(
        self,
        state: dict,
    ) -> dict[str, dict]:

        return {
            action:
                self.evaluate_action(
                    state=state,
                    action=action,
                )
            for action in ACTIONS
        }

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    @property
    def cell_count(self) -> int:
        return len(self.cells)

    def summary(self) -> dict:

        state_action_pairs = {
            (
                key[0],
                key[1],
            )
            for key in self.cells
        }

        return {
            "cells":
                len(self.cells),

            "state_context_action_count":
                len(state_action_pairs),
        }

    # ============================================================
    # SERIALIZATION
    # ============================================================

    def to_dict(self) -> dict:
        """
        Convert the entire LR store into JSON-compatible data.
        """

        serialized_cells = {}

        for (
            key,
            cell,
        ) in self.cells.items():

            state_bucket, action, variable = key

            serialized_key = "|".join(
                (
                    ",".join(
                        state_bucket
                    ),
                    action,
                    variable,
                )
            )

            serialized_cells[
                serialized_key
            ] = cell.to_dict()

        return {
            "cells":
                serialized_cells,
        }

    @classmethod
    def from_dict(
        cls,
        data: dict,
    ) -> "LearnedRelationStore":
        """
        Reconstruct LR store from serialized data.
        """

        store = cls()

        serialized_cells = data.get(
            "cells",
            {},
        )

        for (
            serialized_key,
            cell_data,
        ) in serialized_cells.items():

            parts = serialized_key.split(
                "|"
            )

            if len(parts) != 3:
                continue

            state_bucket = tuple(
                parts[0].split(",")
            )

            action = parts[1]
            variable = parts[2]

            store._validate_action(
                action
            )

            store._validate_variable(
                variable
            )

            key = store.make_key(
                state_bucket,
                action,
                variable,
            )

            store.cells[key] = (
                RelationCell.from_dict(
                    cell_data
                )
            )

        return store