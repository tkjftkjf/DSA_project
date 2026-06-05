from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoreEntry:
    name: str
    score: int
    level: int


class Leaderboard:
    """
    Keep top-N ranking with insertion sort at insertion time.
    """

    def __init__(self, capacity: int = 10) -> None:
        if capacity < 1:
            raise ValueError("capacity must be >= 1")
        self.capacity = capacity
        self._entries: list[ScoreEntry] = []

    def add(self, entry: ScoreEntry) -> None:
        self._entries.append(entry)
        self._insertion_sort_desc()
        if len(self._entries) > self.capacity:
            self._entries = self._entries[: self.capacity]

    def list(self) -> list[ScoreEntry]:
        return list(self._entries)

    def _insertion_sort_desc(self) -> None:
        for i in range(1, len(self._entries)):
            key = self._entries[i]
            j = i - 1
            # sort primarily by score, then by level
            while j >= 0 and (
                self._entries[j].score < key.score
                or (
                    self._entries[j].score == key.score
                    and self._entries[j].level < key.level
                )
            ):
                self._entries[j + 1] = self._entries[j]
                j -= 1
            self._entries[j + 1] = key

