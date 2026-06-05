from __future__ import annotations

from dataclasses import dataclass, field

from dungeon_crawler.actions.base_action import Action
from dungeon_crawler.actions.marker_action import EndTurnAction


@dataclass(slots=True)
class UndoManager:
    """
    Two-stack undo/redo manager.

    Contract:
    - Actions are pushed as they execute.
    - When a turn completes, an EndTurnAction(turn_id) marker must be pushed.
    - undo_turn() reverts all actions for the most recent completed turn.
    - redo_turn() reapplies the most recently undone turn.
    - If new actions are recorded after an undo, redo history is cleared.
    """

    undo_stack: list[Action] = field(default_factory=list)
    redo_stack: list[Action] = field(default_factory=list)

    def record(self, action: Action) -> None:
        # New branch after undo invalidates redo history
        if self.redo_stack:
            self.redo_stack.clear()
        self.undo_stack.append(action)

    def end_turn(self, turn_id: int) -> None:
        if self.redo_stack:
            self.redo_stack.clear()
        self.undo_stack.append(EndTurnAction(turn_id=turn_id))

    def can_undo(self) -> bool:
        return any(isinstance(a, EndTurnAction) for a in self.undo_stack)

    def can_redo(self) -> bool:
        return bool(self.redo_stack) and any(isinstance(a, EndTurnAction) for a in self.redo_stack)

    def undo_turn(self) -> int | None:
        """Undo the latest completed turn. Returns undone turn_id, or None."""
        if not self.can_undo():
            return None

        # Pop until marker; marker defines the turn boundary
        marker = self._pop_until_marker(self.undo_stack)
        assert marker is not None
        turn_id = marker.turn_id
        self.redo_stack.append(marker)

        # Undo actions belonging to that turn
        while self.undo_stack:
            top = self.undo_stack[-1]
            if isinstance(top, EndTurnAction):
                break
            action = self.undo_stack.pop()
            action.undo()
            self.redo_stack.append(action)

        return turn_id

    def redo_turn(self) -> int | None:
        """Redo the most recently undone turn. Returns redone turn_id, or None."""
        if not self.can_redo():
            return None

        marker = self._pop_until_marker(self.redo_stack)
        assert marker is not None
        turn_id = marker.turn_id

        # redo_stack currently contains: ... [EndTurn] [actions undone in reverse push order]
        # We need to replay actions in original execution order:
        # - The last undone action should execute first? Actually during undo we appended each popped action.
        #   redo_stack order (top last): marker, a1, a2, ... (where a_last was undone first).
        # So we pull until next marker or stack end, then reverse to execute.
        actions_to_redo: list[Action] = []
        while self.redo_stack:
            top = self.redo_stack[-1]
            if isinstance(top, EndTurnAction):
                break
            actions_to_redo.append(self.redo_stack.pop())

        actions_to_redo.reverse()
        for action in actions_to_redo:
            action.execute()
            self.undo_stack.append(action)

        self.undo_stack.append(marker)
        return turn_id

    @staticmethod
    def _pop_until_marker(stack: list[Action]) -> EndTurnAction | None:
        while stack:
            a = stack.pop()
            if isinstance(a, EndTurnAction):
                return a
        return None

