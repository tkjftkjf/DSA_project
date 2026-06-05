from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.utils.action_validator import ActionValidator, GameContext


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

    def collect_actions(
        self,
        plans: list[EntityTurnPlan],
        context: GameContext,
    ) -> list[Action]:
        actions: list[Action] = []
        for plan in plans:
            if not plan.entity.is_alive:
                continue
            action = self._resolve_plan(plan, context)
            if action is not None:
                actions.append(action)
        return actions

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
