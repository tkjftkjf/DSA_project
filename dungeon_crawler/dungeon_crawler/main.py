from __future__ import annotations

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.ui.renderer import Renderer


def main() -> int:
    dungeon = Dungeon(width=30, height=20)
    dungeon.generate_rooms(room_count=10, seed=7, extra_cycles=2)

    player = Entity(name="player", x=2, y=2, hp=20, max_hp=20, atk=5, defense=1)
    enemy = Entity(name="enemy", x=6, y=5, hp=8, max_hp=8, atk=2, defense=0, exp_reward=5)
    manager = GameManager(
        dungeon=dungeon,
        player=player,
        entities=[player, enemy],
        base_seed=2026,
    )

    # Build a basic floor/wall grid from generated room tiles.
    grid = [[Renderer.WALL for _ in range(dungeon.width)] for _ in range(dungeon.height)]
    for x, y in dungeon.floor_tiles:
        grid[y][x] = Renderer.FLOOR

    viewport = Renderer.compute_viewport(
        map_width=dungeon.width,
        map_height=dungeon.height,
        player_pos=player.pos,
        viewport_width=20,
        viewport_height=12,
    )
    map_text = Renderer.render_viewport(grid, player_pos=player.pos, viewport=viewport)
    status_text = f"Turn: {manager.turn_manager.turn_id}\nHP: {player.hp}/{player.max_hp}\nATK/DEF: {player.atk}/{player.defense}"
    log_text = "게임이 시작되었습니다."

    try:
        from rich.console import Console

        console = Console()
        layout = Renderer.build_layout(map_text=map_text, status_text=status_text, log_text=log_text)
        console.print(layout)
    except ModuleNotFoundError:
        print("[Map]")
        print(map_text)
        print("\n[Status]")
        print(status_text)
        print("\n[Log]")
        print(log_text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

