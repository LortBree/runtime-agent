from __future__ import annotations

import json
from pathlib import Path

from .knowledge import (
    LearnedRelationStore,
)


class KnowledgePersistence:
    """
    Persistence adapter for Layer 2.

    The Knowledge Layer remains the semantic owner of LR.
    This class only handles serialization/storage.
    """

    def __init__(
        self,
        path: str = "knowledge.json",
    ) -> None:

        self.path = Path(path)

    def save(
        self,
        knowledge: LearnedRelationStore,
    ) -> None:

        data = knowledge.to_dict()

        self.path.write_text(
            json.dumps(
                data,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )

    def load(
        self,
    ) -> LearnedRelationStore:

        if not self.path.exists():
            return LearnedRelationStore()

        data = json.loads(
            self.path.read_text(
                encoding="utf-8"
            )
        )

        return (
            LearnedRelationStore.from_dict(
                data
            )
        )