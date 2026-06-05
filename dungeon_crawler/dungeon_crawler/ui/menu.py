from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dungeon_crawler.utils.leaderboard import Leaderboard


def get_terminal_size() -> tuple[int, int]:
    try:
        from rich.console import Console

        size = Console().size
        return size.width, size.height
    except Exception:
        cols, rows = shutil.get_terminal_size(fallback=(80, 24))
        return cols, rows


def format_leaderboard_text(leaderboard: Leaderboard, width: int) -> str:
    lines = ["=== LEADERBOARD ==="]
    entries = leaderboard.list()
    if not entries:
        lines.append("(no records yet)")
    else:
        for idx, entry in enumerate(entries, start=1):
            lines.append(
                f"{idx:>2}. {entry.name:<12} score={entry.score:<5} lv={entry.level}"
            )
    lines.append("")
    lines.append(f"Terminal: {width} cols")
    lines.append("")
    lines.append("── 조작 안내 ──")
    lines.append("Enter: 게임 시작 | q: 종료")
    lines.append("인게임: 키 입력 후 Enter (한 줄에 한 키)")
    lines.append("w/a/s/d 이동 | c/v→방향 공격")
    lines.append("1~9,0 아이템 | i 인벤 | u/r Undo")
    lines.append("q,esc 포기 | 3층 계단=클리어")
    return "\n".join(lines)


def render_main_menu(leaderboard: Leaderboard) -> str:
    width, height = get_terminal_size()
    body = format_leaderboard_text(leaderboard, width)
    border = "=" * min(width, 60)
    return f"{border}\nDUNGEON CRAWLER\n{border}\n\n{body}\n\n(viewport height: {height})"
