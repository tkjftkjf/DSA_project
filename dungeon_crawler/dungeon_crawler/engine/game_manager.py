from __future__ import annotations

from dataclasses import dataclass, field
import random
from typing import Optional

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.actions.combat_action import CombatAction
from dungeon_crawler.actions.consume_action import ConsumeAction
from dungeon_crawler.actions.loot_action import LootAction
from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.engine.floor_manager import FloorManager
from dungeon_crawler.engine.turn_manager import TurnManager
from dungeon_crawler.engine.turn_resolver import EntityTurnPlan, TurnResolver
from dungeon_crawler.engine.undo_manager import UndoManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item
from dungeon_crawler.utils.action_validator import ActionValidator, GameContext
from dungeon_crawler.utils.decorators import validate_action
from dungeon_crawler.utils.pathfinding import find_path

ENEMY_VISION_RADIUS = 6


@dataclass
class ProjectileResult:
    hit_enemy: Optional[Entity]
    blocked_at: Optional[tuple[int, int]]
    block_reason: Optional[str]


@dataclass
class GameManager:
    player: Entity
    entities: list[Entity]
    base_seed: int = 0
    dungeon: Optional[Dungeon] = None
    floor_manager: Optional[FloorManager] = None
    undo_manager: UndoManager = field(default_factory=UndoManager)
    logs: list[str] = field(default_factory=list)
    ground_items: dict[tuple[int, int], list[Item]] = field(default_factory=dict)
    pending_attack_mode: Optional[str] = None
    kills: int = 0
    show_inventory: bool = False
    debug: bool = False

    def __post_init__(self) -> None:
        self.turn_manager = TurnManager(base_seed=self.base_seed, turn_id=0)
        self.turn_resolver = TurnResolver(undo_manager=self.undo_manager, logs=self.logs)
        self.action_validator = ActionValidator()
        for entity in self.entities:
            self.turn_manager.register(entity)

    @property
    def active_dungeon(self) -> Dungeon:
        if self.floor_manager is not None:
            return self.floor_manager.current_dungeon
        assert self.dungeon is not None
        return self.dungeon

    def game_context(self) -> GameContext:
        return GameContext(
            dungeon=self.active_dungeon,
            entities=self.entities,
            ground_items=self.ground_items,
            player=self.player,
        )

    def execute_action(self, action: Action, log_message: Optional[str] = None) -> None:
        self.turn_manager.prepare_turn_rng()
        action.execute()
        self.undo_manager.record(action)
        if log_message:
            self.logs.append(log_message)

    def finalize_turn(self) -> None:
        turn_id = self.turn_manager.turn_id
        self.undo_manager.end_turn(turn_id=turn_id)
        self.turn_manager.end_turn()

    def undo_turn(self) -> Optional[int]:
        undone_turn = self.undo_manager.undo_turn()
        if undone_turn is not None:
            self.turn_manager.set_turn_id(undone_turn)
            self.logs.append(f"[System] 턴 {undone_turn}의 행동을 되돌렸습니다.")
        return undone_turn

    def redo_turn(self) -> Optional[int]:
        redone_turn = self.undo_manager.redo_turn()
        if redone_turn is not None:
            self.turn_manager.set_turn_id(redone_turn + 1)
            self.logs.append(f"[System] 턴 {redone_turn}의 행동을 다시 적용했습니다.")
        return redone_turn

    def set_attack_mode(self, mode: str) -> None:
        self.pending_attack_mode = mode
        self.logs.append("[WASD를 통해 공격 방향을 정하세요]")

    def player_use_slot(self, slot_idx: int) -> bool:
        action = ConsumeAction(turn_id=self.turn_manager.turn_id, consumer=self.player, slot_idx=slot_idx)
        result = self.action_validator.validate(action, self.game_context())
        if not result.ok:
            self.logs.append("해당 슬롯 아이템을 사용할 수 없습니다.")
            return False
        self.execute_action(action, log_message=f"플레이어가 슬롯 {slot_idx + 1} 아이템을 사용했습니다.")
        return True

    @validate_action
    def try_player_move(self, dx: int, dy: int) -> bool:
        target = (self.player.x + dx, self.player.y + dy)
        enemy = self._enemy_at(target)
        if enemy is not None:
            return self._resolve_combat(self.player, enemy)

        action = MoveAction(
            turn_id=self.turn_manager.turn_id,
            entity=self.player,
            dungeon=self.active_dungeon,
            dx=dx,
            dy=dy,
        )
        result = self.action_validator.validate(action, self.game_context())
        if not result.ok:
            self.logs.append("이동할 수 없는 위치입니다.")
            return False

        before = self.player.pos
        self.execute_action(action)
        if self.player.pos == before:
            self.logs.append("이동할 수 없는 위치입니다.")
            return False
        self._log_move(f"플레이어 이동: {before} -> {self.player.pos}")
        self._try_auto_loot(self.player.pos)
        self._try_descend_stairs()
        return True

    @validate_action
    def try_player_attack(self, dx: int, dy: int) -> bool:
        mode = self.pending_attack_mode
        if mode is None:
            return False

        if mode == "melee":
            target = (self.player.x + dx, self.player.y + dy)
            enemy = self._enemy_at(target)
            if enemy is None:
                self.logs.append("공격 대상이 없습니다.")
                return False
            self.pending_attack_mode = None
            return self._resolve_combat(self.player, enemy)

        if mode == "ranged":
            if self.player.inventory is None or self.player.inventory.counts.get("arrow", 0) < 1:
                self.logs.append("화살이 부족합니다.")
                return False
            projectile = self._trace_projectile(dx, dy)
            try:
                self.player.inventory.remove_first_by_name("arrow")
            except ValueError:
                self.logs.append("화살이 부족합니다.")
                return False
            self.pending_attack_mode = None
            if projectile.hit_enemy is not None:
                return self._resolve_combat(self.player, projectile.hit_enemy, ranged=True)
            if projectile.blocked_at is not None:
                reason = projectile.block_reason or "장애물"
                if reason == "wall":
                    self.logs.append(f"화살이 {projectile.blocked_at}에서 벽에 막혔습니다.")
                elif reason == "item":
                    self.logs.append(f"화살이 {projectile.blocked_at} 아이템에 막혔습니다.")
                else:
                    self.logs.append(f"화살이 {projectile.blocked_at}에서 사라졌습니다.")
            return True

        return False

    def run_enemy_turns(self) -> None:
        plans: list[EntityTurnPlan] = []
        for enemy in list(self.entities):
            if enemy is self.player or not enemy.is_alive:
                continue
            if not self._on_active_floor(enemy.pos):
                continue
            state = {"fallback_idx": 0, "wander": None}
            plans.append(
                EntityTurnPlan(
                    entity=enemy,
                    propose=lambda e=enemy, s=state: self._propose_enemy_action(e, s),
                    fallback=lambda s=state: self._enemy_fallback(s),
                )
            )

        actions = self.turn_resolver.collect_actions(plans, self.game_context())
        for action in actions:
            if isinstance(action, CombatAction):
                before_hp = action.defender.hp
                was_alive = action.defender.is_alive
                self.turn_manager.prepare_turn_rng()
                action.execute()
                self.undo_manager.record(action)
                self.logs.append(
                    f"{action.attacker.name} 근접 공격 -> {action.defender.name} HP {before_hp}->{action.defender.hp}"
                )
                if was_alive and not action.defender.is_alive and action.attacker is self.player:
                    self.kills += 1
                    self.logs.append(f"EXP +{action.defender.exp_reward} (현재 {self.player.exp})")
                    if self.player.try_level_up():
                        self.logs.append(
                            f"레벨 업! LV {self.player.level} (HP {self.player.hp}, ATK {self.player.atk}, DEF {self.player.defense})"
                        )
                continue

            before = action.entity.pos if isinstance(action, MoveAction) else None
            self.turn_manager.prepare_turn_rng()
            action.execute()
            self.undo_manager.record(action)
            if isinstance(action, MoveAction) and before is not None and action.entity.pos != before:
                self._log_move(f"{action.entity.name} 이동: {before} -> {action.entity.pos}")

    def all_enemies_defeated(self) -> bool:
        return not any(
            e is not self.player and e.is_alive and self._on_active_floor(e.pos)
            for e in self.entities
        )

    def status_text(self) -> str:
        arrows = 0
        if self.player.inventory is not None:
            arrows = self.player.inventory.counts.get("arrow", 0)
        mode_line = ""
        if self.pending_attack_mode == "melee":
            mode_line = "Mode: 근접(C) - WASD로 방향 선택\n"
        elif self.pending_attack_mode == "ranged":
            mode_line = "Mode: 원거리(V) - WASD로 방향 선택\n"
        floor_line = ""
        if self.floor_manager is not None:
            floor_line = f"Floor: {self.floor_manager.current_floor}\n"
        lines = [
            mode_line.rstrip("\n") if mode_line else "",
            floor_line.rstrip("\n") if floor_line else "",
            f"Turn: {self.turn_manager.turn_id}",
            f"HP: {self.player.hp}/{self.player.max_hp}",
            f"ATK/DEF: {self.player.atk}/{self.player.defense}",
            f"EXP/LV: {self.player.exp}/{self.player.level}",
            f"Kills: {self.kills}",
            f"Arrows: {arrows}",
            f"Debug: {'ON' if self.debug else 'OFF'}",
        ]
        if self.show_inventory:
            lines.append(_inventory_lines(self.player))
        return "\n".join(line for line in lines if line)

    def _resolve_combat(self, attacker: Entity, defender: Entity, ranged: bool = False) -> bool:
        action = CombatAction(
            turn_id=self.turn_manager.turn_id,
            attacker=attacker,
            defender=defender,
            entity_pool=self.entities,
        )
        before_hp = defender.hp
        was_alive = defender.is_alive
        self.execute_action(action)
        if defender.hp == before_hp:
            return False
        kind = "원거리" if ranged else "근접"
        self.logs.append(f"{attacker.name} {kind} 공격 -> {defender.name} HP {before_hp}->{defender.hp}")

        if was_alive and not defender.is_alive and attacker is self.player:
            self.kills += 1
            self.logs.append(f"EXP +{defender.exp_reward} (현재 {self.player.exp})")
            if self.player.try_level_up():
                self.logs.append(
                    f"레벨 업! LV {self.player.level} (HP {self.player.hp}, ATK {self.player.atk}, DEF {self.player.defense})"
                )

        return True

    def _try_auto_loot(self, pos: tuple[int, int]) -> None:
        if self.player.inventory is None:
            return
        items = self.ground_items.get(pos, [])
        if not items:
            return
        item = items[0]
        action = LootAction(
            turn_id=self.turn_manager.turn_id,
            looter=self.player,
            item=item,
            position=pos,
            ground_items=self.ground_items,
        )
        result = self.action_validator.validate(action, self.game_context())
        if not result.ok:
            self.logs.append("인벤토리가 가득 차 아이템을 줍지 못했습니다.")
            return
        self.execute_action(action, log_message=f"아이템 획득: {item.icon} {item.name}")

    def _try_descend_stairs(self) -> None:
        if self.floor_manager is None:
            return
        if not self.floor_manager.is_on_stairs(self.player.pos):
            return
        if not self.floor_manager.can_descend():
            return
        target = self.floor_manager.descend()
        if target is None:
            return
        self.player.set_pos(*target)
        self.logs.append(f"Floor {self.floor_manager.current_floor}로 내려갔습니다.")

    def _propose_enemy_action(self, enemy: Entity, state: dict) -> Optional[Action]:
        if self._adjacent(enemy.pos, self.player.pos):
            return CombatAction(
                turn_id=self.turn_manager.turn_id,
                attacker=enemy,
                defender=self.player,
                entity_pool=self.entities,
            )

        if self._manhattan(enemy.pos, self.player.pos) > ENEMY_VISION_RADIUS:
            if state["wander"] is None:
                state["wander"] = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
            dx, dy = state["wander"]
            return MoveAction(
                turn_id=self.turn_manager.turn_id,
                entity=enemy,
                dungeon=self.active_dungeon,
                dx=dx,
                dy=dy,
            )

        blockers = set(self.ground_items.keys())
        blockers |= {
            e.pos
            for e in self.entities
            if e is not enemy and e is not self.player and e.is_alive
        }
        path = find_path(self.active_dungeon, enemy.pos, self.player.pos, blocked=blockers)
        if len(path) < 2:
            path = find_path(
                self.active_dungeon,
                enemy.pos,
                self.player.pos,
                blocked=blockers | {e.pos for e in self.entities if e is not enemy and e.is_alive},
            )
        if len(path) < 2:
            return None
        nxt = path[1]
        dx = nxt[0] - enemy.x
        dy = nxt[1] - enemy.y
        return MoveAction(
            turn_id=self.turn_manager.turn_id,
            entity=enemy,
            dungeon=self.active_dungeon,
            dx=dx,
            dy=dy,
        )

    def _enemy_fallback(self, state: dict) -> None:
        options = [(1, 0), (-1, 0), (0, 1), (0, -1), (0, 0)]
        idx = state["fallback_idx"] % len(options)
        state["fallback_idx"] += 1
        state["wander"] = options[idx]

    def _enemy_at(self, pos: tuple[int, int]) -> Optional[Entity]:
        for entity in self.entities:
            if entity is self.player:
                continue
            if entity.is_alive and entity.pos == pos and self._on_active_floor(pos):
                return entity
        return None

    def _on_active_floor(self, pos: tuple[int, int]) -> bool:
        floors = self.active_dungeon.floor_tiles
        return not floors or pos in floors

    def _trace_projectile(self, dx: int, dy: int) -> ProjectileResult:
        x, y = self.player.pos
        while True:
            x += dx
            y += dy
            if not self.active_dungeon.in_bounds(x, y):
                return ProjectileResult(hit_enemy=None, blocked_at=(x - dx, y - dy), block_reason="boundary")
            if not self.active_dungeon.is_walkable(x, y):
                return ProjectileResult(hit_enemy=None, blocked_at=(x, y), block_reason="wall")
            if self.ground_items.get((x, y)):
                return ProjectileResult(hit_enemy=None, blocked_at=(x, y), block_reason="item")
            enemy = self._enemy_at((x, y))
            if enemy is not None:
                return ProjectileResult(hit_enemy=enemy, blocked_at=None, block_reason=None)

    def _log_move(self, message: str) -> None:
        if self.debug:
            self.logs.append(message)

    @staticmethod
    def _adjacent(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

    @staticmethod
    def _manhattan(a: tuple[int, int], b: tuple[int, int]) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _inventory_lines(player: Entity) -> str:
    if player.inventory is None:
        return "Inventory: (none)"
    slots: list[str] = []
    for idx, item in enumerate(player.inventory.slots, start=1):
        key = "0" if idx == 10 else str(idx)
        label = f"{item.icon}" if item else "-"
        slots.append(f"{key}:{label}")
    return "Inventory: " + " ".join(slots)
