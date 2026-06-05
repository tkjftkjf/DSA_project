from __future__ import annotations

from dataclasses import dataclass, field
import random

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.actions.combat_action import CombatAction
from dungeon_crawler.actions.consume_action import ConsumeAction
from dungeon_crawler.actions.loot_action import LootAction
from dungeon_crawler.actions.move_action import MoveAction
from dungeon_crawler.engine.turn_manager import TurnManager
from dungeon_crawler.engine.undo_manager import UndoManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.item import Item
from dungeon_crawler.utils.pathfinding import find_path


@dataclass
class GameManager:
    dungeon: Dungeon
    player: Entity
    entities: list[Entity]
    base_seed: int = 0
    undo_manager: UndoManager = field(default_factory=UndoManager)
    logs: list[str] = field(default_factory=list)
    ground_items: dict[tuple[int, int], list[Item]] = field(default_factory=dict)
    pending_attack_mode: str | None = None

    def __post_init__(self) -> None:
        self.turn_manager = TurnManager(base_seed=self.base_seed, turn_id=0)
        for entity in self.entities:
            self.turn_manager.register(entity)

    def execute_action(self, action: Action, log_message: str | None = None) -> None:
        self.turn_manager.prepare_turn_rng()
        action.execute()
        self.undo_manager.record(action)
        if log_message:
            self.logs.append(log_message)

    def finalize_turn(self) -> None:
        turn_id = self.turn_manager.turn_id
        self.undo_manager.end_turn(turn_id=turn_id)
        self.turn_manager.end_turn()

    def undo_turn(self) -> int | None:
        undone_turn = self.undo_manager.undo_turn()
        if undone_turn is not None:
            self.turn_manager.set_turn_id(undone_turn)
            self.logs.append(f"[System] 턴 {undone_turn}의 행동을 되돌렸습니다.")
        return undone_turn

    def redo_turn(self) -> int | None:
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
        try:
            self.execute_action(action, log_message=f"플레이어가 슬롯 {slot_idx + 1} 아이템을 사용했습니다.")
        except (ValueError, IndexError):
            self.logs.append("해당 슬롯 아이템을 사용할 수 없습니다.")
            return False
        return True

    def try_player_move(self, dx: int, dy: int) -> bool:
        target = (self.player.x + dx, self.player.y + dy)
        enemy = self._enemy_at(target)
        if enemy is not None:
            return self._resolve_combat(self.player, enemy)

        action = MoveAction(
            turn_id=self.turn_manager.turn_id,
            entity=self.player,
            dungeon=self.dungeon,
            dx=dx,
            dy=dy,
        )
        before = self.player.pos
        self.execute_action(action)
        if self.player.pos == before:
            self.logs.append("이동할 수 없는 위치입니다.")
            return False
        self.logs.append(f"플레이어 이동: {before} -> {self.player.pos}")
        self._try_auto_loot(self.player.pos)
        return True

    def try_player_attack(self, dx: int, dy: int) -> bool:
        mode = self.pending_attack_mode
        self.pending_attack_mode = None
        if mode is None:
            return False

        if mode == "melee":
            target = (self.player.x + dx, self.player.y + dy)
            enemy = self._enemy_at(target)
            if enemy is None:
                self.logs.append("공격 대상이 없습니다.")
                return False
            return self._resolve_combat(self.player, enemy)

        if mode == "ranged":
            if self.player.inventory is None or self.player.inventory.counts.get("arrow", 0) < 1:
                self.logs.append("화살이 부족합니다.")
                return False
            enemy = self._first_enemy_in_ray(dx, dy)
            if enemy is None:
                self.logs.append("사격 경로에 적이 없습니다.")
                return False
            # consume one arrow immediately (undo-able via ConsumeAction model was for heals only;
            # keep ranged ammo simple with direct inventory mutation).
            try:
                self.player.inventory.remove_first_by_name("arrow")
            except ValueError:
                self.logs.append("화살이 부족합니다.")
                return False
            return self._resolve_combat(self.player, enemy, ranged=True)

        return False

    def run_enemy_turns(self) -> None:
        for enemy in list(self.entities):
            if enemy is self.player or not enemy.is_alive:
                continue

            if self._adjacent(enemy.pos, self.player.pos):
                self._resolve_combat(enemy, self.player)
                continue

            # A*: walls + items + other monsters as dynamic blockers
            blockers = set(self.ground_items.keys())
            blockers |= {e.pos for e in self.entities if e is not enemy and e is not self.player and e.is_alive}
            path = find_path(self.dungeon, enemy.pos, self.player.pos, blocked=blockers)
            if len(path) >= 2:
                nxt = path[1]
                dx = nxt[0] - enemy.x
                dy = nxt[1] - enemy.y
            else:
                dx, dy = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])

            action = MoveAction(
                turn_id=self.turn_manager.turn_id,
                entity=enemy,
                dungeon=self.dungeon,
                dx=dx,
                dy=dy,
            )
            before = enemy.pos
            self.execute_action(action)
            if enemy.pos != before:
                self.logs.append(f"{enemy.name} 이동: {before} -> {enemy.pos}")

    def status_text(self) -> str:
        arrows = 0
        if self.player.inventory is not None:
            arrows = self.player.inventory.counts.get("arrow", 0)
        return (
            f"Turn: {self.turn_manager.turn_id}\n"
            f"HP: {self.player.hp}/{self.player.max_hp}\n"
            f"ATK/DEF: {self.player.atk}/{self.player.defense}\n"
            f"EXP/LV: {self.player.exp}/{self.player.level}\n"
            f"Arrows: {arrows}"
        )

    def _resolve_combat(self, attacker: Entity, defender: Entity, ranged: bool = False) -> bool:
        action = CombatAction(
            turn_id=self.turn_manager.turn_id,
            attacker=attacker,
            defender=defender,
            entity_pool=self.entities,
        )
        before_hp = defender.hp
        self.execute_action(action)
        if defender.hp == before_hp:
            return False
        kind = "원거리" if ranged else "근접"
        self.logs.append(f"{attacker.name} {kind} 공격 -> {defender.name} HP {before_hp}->{defender.hp}")
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
        try:
            self.execute_action(action, log_message=f"아이템 획득: {item.icon} {item.name}")
        except ValueError:
            self.logs.append("인벤토리가 가득 차 아이템을 줍지 못했습니다.")

    def _enemy_at(self, pos: tuple[int, int]) -> Entity | None:
        for entity in self.entities:
            if entity is self.player:
                continue
            if entity.is_alive and entity.pos == pos:
                return entity
        return None

    def _first_enemy_in_ray(self, dx: int, dy: int) -> Entity | None:
        x, y = self.player.pos
        while True:
            x += dx
            y += dy
            if not self.dungeon.in_bounds(x, y):
                return None
            if not self.dungeon.is_walkable(x, y):
                return None
            enemy = self._enemy_at((x, y))
            if enemy is not None:
                return enemy

    @staticmethod
    def _adjacent(a: tuple[int, int], b: tuple[int, int]) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1

