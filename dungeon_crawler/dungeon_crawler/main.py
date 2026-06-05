from __future__ import annotations

import sys

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.engine.input_handler import InputHandler
from dungeon_crawler.engine.session import compute_score, create_game_manager
from dungeon_crawler.ui.menu import render_main_menu
from dungeon_crawler.ui.renderer import Renderer
from dungeon_crawler.utils.leaderboard import Leaderboard, ScoreEntry
from dungeon_crawler.utils.leaderboard_store import load_leaderboard, save_leaderboard


def main() -> int:
    leaderboard = load_leaderboard()
    while True:
        if not show_main_menu(leaderboard):
            return 0
        manager = create_game_manager()
        result = run_game_loop(manager)
        score = compute_score(manager.player, manager.turn_manager.turn_id, manager.kills)
        leaderboard.add(
            ScoreEntry(name="player", score=score, level=manager.player.level)
        )
        save_leaderboard(leaderboard)
        manager.logs.append(f"최종 점수: {score} (결과: {result})")
        _render_frame(manager)
        if input("\n메인으로 돌아가려면 Enter > ").strip().lower() == "q":
            return 0


def show_main_menu(leaderboard: Leaderboard) -> bool:
    text = render_main_menu(leaderboard)
    try:
        from rich.console import Console

        Console().clear()
        Console().print(text)
    except ModuleNotFoundError:
        print(text)
    choice = input("\n> ").strip().lower()
    return choice != "q"


def run_game_loop(manager: GameManager) -> str:
    player = manager.player
    input_handler = InputHandler()
    manager.logs.append("조작: w/a/s/d, c/v, u/r, 1~0, i, esc")

    while player.is_alive:
        if manager.dungeon_cleared:
            return "victory"

        _render_frame(manager)
        raw = input("\n명령 입력 > ").strip().lower()
        if not raw:
            continue
        if raw in {"q", "esc"}:
            manager.logs.append("메인 화면으로 이동합니다.")
            return "retreat"

        cmd = input_handler.parse_key(raw)
        if cmd is None:
            manager.logs.append("알 수 없는 입력입니다.")
            continue

        turn_consumed = False
        if cmd.kind == "undo":
            manager.undo_turn()
            continue
        if cmd.kind == "redo":
            manager.redo_turn()
            continue
        if cmd.kind == "toggle_inventory":
            manager.show_inventory = not manager.show_inventory
            state = "표시" if manager.show_inventory else "숨김"
            manager.logs.append(f"인벤토리 {state}")
            continue
        if cmd.kind == "use_slot":
            key = str(cmd.payload)
            slot_idx = 9 if key == "0" else int(key) - 1
            turn_consumed = manager.player_use_slot(slot_idx)
        elif cmd.kind == "melee_mode":
            manager.set_attack_mode("melee")
            continue
        elif cmd.kind == "ranged_mode":
            manager.set_attack_mode("ranged")
            continue
        elif cmd.kind == "move":
            dx, dy = cmd.payload  # type: ignore[misc]
            if manager.pending_attack_mode is not None:
                turn_consumed = manager.try_player_attack(dx, dy)
            else:
                turn_consumed = manager.try_player_move(dx, dy)

        if turn_consumed:
            manager.run_enemy_turns()
            manager.finalize_turn()
            if manager.dungeon_cleared:
                return "victory"
            if player.hp <= 0:
                player.is_alive = False
                manager.logs.append("플레이어가 쓰러졌습니다. 게임 오버.")
                return "defeat"

    return "defeat"


def _render_frame(manager: GameManager) -> None:
    dungeon = manager.active_dungeon
    grid = [[Renderer.WALL for _ in range(dungeon.width)] for _ in range(dungeon.height)]
    for x, y in dungeon.floor_tiles:
        grid[y][x] = Renderer.FLOOR
    for x, y in dungeon.stair_tiles:
        grid[y][x] = Renderer.STAIR
    current_floor = manager.current_floor_id
    for pos, items in manager.active_ground_items.items():
        if items:
            grid[pos[1]][pos[0]] = items[0].icon
    for entity in manager.entities:
        if entity is manager.player or not entity.is_alive:
            continue
        if entity.floor_id != current_floor:
            continue
        grid[entity.y][entity.x] = "👾"

    status_text = manager.status_text()
    log_text = "\n".join(manager.logs[-10:]) if manager.logs else "-"

    try:
        from rich.console import Console

        console = Console()
        layout_height = Renderer.compute_layout_height(console.size.height)
        map_text, _viewport = Renderer.render_scrolled_map(
            grid,
            manager.player.pos,
            map_width=dungeon.width,
            map_height=dungeon.height,
            terminal_cols=console.size.width,
            layout_height=layout_height,
        )
        console.clear()
        layout = Renderer.build_layout(map_text=map_text, status_text=status_text, log_text=log_text)
        console.print(layout, height=layout_height)
    except ModuleNotFoundError:
        layout_height = Renderer.compute_layout_height(24)
        map_text, _viewport = Renderer.render_scrolled_map(
            grid,
            manager.player.pos,
            map_width=dungeon.width,
            map_height=dungeon.height,
            terminal_cols=80,
            layout_height=layout_height,
        )
        print("\n[Map]")
        print(map_text)
        print("\n[Status]")
        print(status_text)
        print("\n[Log]")
        print(log_text)


if __name__ == "__main__":
    raise SystemExit(main())
