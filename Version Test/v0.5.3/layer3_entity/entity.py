from __future__ import annotations

from .decision import (
    Decision,
    DecisionEngine,
)
from .experience import Experience


class EntityCore:
    """
    Layer 3 — Entity Core.

    EntityCore is intentionally thin.

    It orchestrates:

        Observe
          ↓
        Retrieve Knowledge
          ↓
        Decision
          ↓
        Execute
          ↓
        Generate Experience
          ↓
        Update Knowledge
    """

    def __init__(
        self,
        environment,
        knowledge,
        decision_engine: DecisionEngine | None = None,
    ) -> None:

        self.environment = environment
        self.knowledge = knowledge

        self.decision_engine = (
            decision_engine
            if decision_engine is not None
            else DecisionEngine(
                action_order=
                    environment.available_actions
            )
        )

        self.experiences: list[
            Experience
        ] = []

    # ============================================================
    # OBSERVE
    # ============================================================

    def observe(self) -> dict:
        return self.environment.state.as_dict()

    # ============================================================
    # RETRIEVE KNOWLEDGE
    # ============================================================

    def retrieve_knowledge(
        self,
        state: dict,
    ) -> dict:
        return (
            self.knowledge
            .evaluate_all_actions(
                state
            )
        )

    # ============================================================
    # DECIDE
    # ============================================================

    def decide(
        self,
        state: dict,
        knowledge_view: dict,
    ) -> Decision:

        return (
            self.decision_engine
            .select_action(
                state=state,
                knowledge=knowledge_view,
            )
        )

    # ============================================================
    # EXECUTE
    # ============================================================

    def execute(
        self,
        action: str,
    ):
        return self.environment.step(
            action
        )

    # ============================================================
    # EXPERIENCE
    # ============================================================

    @staticmethod
    def generate_experience(
        transition,
    ) -> Experience:

        return Experience(
            state_before=
                transition.state_before,
            action=
                transition.action,
            state_after=
                transition.state_after,
        )

    # ============================================================
    # LEARN
    # ============================================================

    def learn(
        self,
        experience: Experience,
    ) -> list[dict]:

        return (
            self.knowledge.update(
                state_before=
                    experience.state_before,

                action=
                    experience.action,

                state_after=
                    experience.state_after,
            )
        )

    # ============================================================
    # ONE CYCLE
    # ============================================================

    def cycle(self) -> dict:
        """
        Execute one complete Entity lifecycle.
        """

        # --------------------------------------------------------
        # 1. Observe
        # --------------------------------------------------------

        state = self.observe()

        # --------------------------------------------------------
        # 2. Retrieve Knowledge
        # --------------------------------------------------------

        knowledge_view = (
            self.retrieve_knowledge(
                state
            )
        )

        # --------------------------------------------------------
        # 3. Decision
        # --------------------------------------------------------

        decision = self.decide(
            state,
            knowledge_view,
        )

        # --------------------------------------------------------
        # 4. Execute
        # --------------------------------------------------------

        transition = self.execute(
            decision.action
        )

        # --------------------------------------------------------
        # 5. Generate Experience
        # --------------------------------------------------------

        experience = (
            self.generate_experience(
                transition
            )
        )

        # --------------------------------------------------------
        # 6. Update Knowledge
        # --------------------------------------------------------

        updates = self.learn(
            experience
        )

        self.experiences.append(
            experience
        )

        return {
            "state_before": state,
            "knowledge": knowledge_view,
            "decision": decision,
            "transition":
                transition.as_dict(),
            "experience":
                experience.as_dict(),
            "knowledge_updates":
                updates,
        }