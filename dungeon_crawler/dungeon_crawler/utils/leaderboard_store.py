from __future__ import annotations

import json
from pathlib import Path

from dungeon_crawler.utils.leaderboard import Leaderboard, ScoreEntry

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "leaderboard.json"


def load_leaderboard(path: Path | None = None, capacity: int = 10) -> Leaderboard:
    board = Leaderboard(capacity=capacity)
    file_path = path or DEFAULT_PATH
    if not file_path.exists():
        return board

    data = json.loads(file_path.read_text(encoding="utf-8"))
    for row in data:
        board.add(ScoreEntry(name=row["name"], score=row["score"], level=row["level"]))
    return board


def save_leaderboard(board: Leaderboard, path: Path | None = None) -> None:
    file_path = path or DEFAULT_PATH
    payload = [
        {"name": e.name, "score": e.score, "level": e.level}
        for e in board.list()
    ]
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
