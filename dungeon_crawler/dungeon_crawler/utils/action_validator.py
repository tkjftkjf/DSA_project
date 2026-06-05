from __future__ import annotations

from dataclasses import dataclass

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.actions.combat_action import CombatAction
from dungeon_crawler.actions.consume_action import ConsumeAction
from dungeon_crawler.actions.loot_action import LootAction
from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item


@dataclass(frozen=True)
class ValidationResult:
    ok: bool
    reason: str = ""
    action: Action | None = None


@dataclass
class GameContext:
    dungeon: Dungeon
    entities: list[Entity]
    ground_items: dict[tuple[int, int], list[Item]]
    player: Entity


class ActionValidator:
    def validate(self, action: Action, context: GameContext) -> ValidationResult:
        if isinstance(action, MoveAction):
            return self._validate_move(action, context)
        if isinstance(action, CombatAction):
            return self._validate_combat(action, context)
        if isinstance(action, LootAction):
            return self._validate_loot(action, context)
        if isinstance(action, ConsumeAction):
            return self._validate_consume(action, context)
        return ValidationResult(ok=True, action=action)

    def _validate_move(self, action: MoveAction, context: GameContext) -> ValidationResult:
        target = (action.entity.x + action.dx, action.entity.y + action.dy)
        if not context.dungeon.is_walkable(*target):
            return ValidationResult(ok=False, reason="not_walkable")
        for entity in context.entities:
            if entity is action.entity or not entity.is_alive:
                continue
            if entity.floor_id != action.entity.floor_id:
                continue
            if entity.pos == target:
                return ValidationResult(ok=False, reason="occupied")
        return ValidationResult(ok=True, action=action)

    def _validate_combat(self, action: CombatAction, context: GameContext) -> ValidationResult:
        if not action.defender.is_alive:
            return ValidationResult(ok=False, reason="dead_target")
        if action.attacker is action.defender:
            return ValidationResult(ok=False, reason="self_target")
        return ValidationResult(ok=True, action=action)

    def _validate_loot(self, action: LootAction, context: GameContext) -> ValidationResult:
        items = context.ground_items.get(action.position, [])
        if action.item not in items:
            return ValidationResult(ok=False, reason="item_missing")
        if action.looter.inventory is None:
            return ValidationResult(ok=False, reason="no_inventory")
        if all(slot is not None for slot in action.looter.inventory.slots):
            return ValidationResult(ok=False, reason="inventory_full")
        return ValidationResult(ok=True, action=action)

    def _validate_consume(self, action: ConsumeAction, context: GameContext) -> ValidationResult:
        inventory = action.consumer.inventory
        if inventory is None:
            return ValidationResult(ok=False, reason="no_inventory")
        if action.slot_idx < 0 or action.slot_idx >= len(inventory.slots):
            return ValidationResult(ok=False, reason="bad_slot")
        if inventory.slots[action.slot_idx] is None:
            return ValidationResult(ok=False, reason="empty_slot")
        item = inventory.slots[action.slot_idx]
        if item.heal_amount > 0 and action.consumer.hp >= action.consumer.max_hp:
            return ValidationResult(ok=False, reason="hp_full")
        return ValidationResult(ok=True, action=action)
