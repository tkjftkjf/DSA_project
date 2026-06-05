from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.engine.turn_manager import TurnManager
from dungeon_crawler.engine.undo_manager import UndoManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity


@dataclass
class GameManager:
    dungeon: Dungeon
    player: Entity
    entities: list[Entity]
    base_seed: int = 0
    undo_manager: UndoManager = field(default_factory=UndoManager)
    logs: list[str] = field(default_factory=list)

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

