from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.actions.marker_action import EndTurnAction
from dungeon_crawler.engine.undo_manager import UndoManager
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.utils.action_validator import ActionValidator, GameContext, ValidationResult


ProposalFn = Callable[[], Optional[Action]]
FallbackFn = Callable[[], None]


@dataclass
class EntityTurnPlan:
    entity: Entity
    propose: ProposalFn
    fallback: FallbackFn
    max_attempts: int = 8


@dataclass
class TurnResolver:
    validator: ActionValidator = field(default_factory=ActionValidator)
    undo_manager: UndoManager | None = None
    logs: list[str] = field(default_factory=list)

    def collect_actions(
        self,
        plans: list[EntityTurnPlan],
        context: GameContext,
    ) -> list[Action]:  # noqa: PLR0911
        queue: list[Action] = []
        for plan in plans:
            if not plan.entity.is_alive:
                continue
            action = self._resolve_plan(plan, context)
            if action is not None:
                queue.append(action)
        return queue

    def execute_batch(
        self,
        actions: list[Action],
        *,
        prepare_rng: Optional[Callable[[], None]] = None,
        record: bool = True,
    ) -> None:
        for action in actions:
            if prepare_rng is not None:
                prepare_rng()
            action.execute()
            if record and self.undo_manager is not None:
                self.undo_manager.record(action)

    def _resolve_plan(self, plan: EntityTurnPlan, context: GameContext) -> Optional[Action]:
        for _ in range(plan.max_attempts):
            proposed = plan.propose()
            if proposed is None:
                plan.fallback()
                continue
            result = self.validator.validate(proposed, context)
            if result.ok:
                return proposed
            plan.fallback()
        return None


def make_end_turn_only(turn_id: int) -> list[Action]:
    return [EndTurnAction(turn_id=turn_id)]
