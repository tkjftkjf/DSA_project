from __future__ import annotations

from dungeon_crawler.engine.game_manager import GameManager
from dungeon_crawler.engine.input_handler import InputHandler
from dungeon_crawler.models.dungeon import Dungeon
from dungeon_crawler.models.entity import Entity
from dungeon_crawler.models.inventory import Inventory
from dungeon_crawler.models.item import Item
from dungeon_crawler.ui.renderer import Renderer


def main() -> int:
    dungeon = Dungeon(width=30, height=20)
    dungeon.generate_rooms(room_count=10, seed=7, extra_cycles=2)

    floor = sorted(dungeon.floor_tiles)
    player_pos = floor[0]
    enemy_pos = floor[min(10, len(floor) - 1)]
    enemy2_pos = floor[min(18, len(floor) - 1)]

    player = Entity(
        name="player",
        x=player_pos[0],
        y=player_pos[1],
        hp=20,
        max_hp=20,
        atk=5,
        defense=1,
        inventory=Inventory(),
    )
    # starter ammo
    assert player.inventory is not None
    for _ in range(3):
        player.inventory.add_item(Item(name="arrow", icon="🏹"))

    enemy = Entity(name="enemy1", x=enemy_pos[0], y=enemy_pos[1], hp=8, max_hp=8, atk=2, defense=0, exp_reward=5)
    enemy2 = Entity(name="enemy2", x=enemy2_pos[0], y=enemy2_pos[1], hp=10, max_hp=10, atk=3, defense=1, exp_reward=7)
    manager = GameManager(
        dungeon=dungeon,
        player=player,
        entities=[player, enemy, enemy2],
        base_seed=2026,
    )
    # place loot
    manager.ground_items[floor[min(4, len(floor) - 1)]] = [Item(name="heart_red", icon="❤️", heal_amount=3)]
    manager.ground_items[floor[min(12, len(floor) - 1)]] = [Item(name="heart_blue", icon="💙", heal_amount=5)]

    input_handler = InputHandler()
    manager.logs.append("게임이 시작되었습니다. (w/a/s/d, c/v, u/r, 1~0, esc)")

    while player.is_alive:
        _render_frame(manager)
        raw = input("\n명령 입력 > ").strip().lower()
        if not raw:
            continue
        if raw == "q":
            break
        if raw == "esc":
            manager.logs.append("메인 화면으로 이동합니다.")
            break

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
            manager.logs.append(_inventory_text(player))
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
            if player.hp <= 0:
                player.is_alive = False
                manager.logs.append("플레이어가 쓰러졌습니다. 게임 오버.")
                break

    _render_frame(manager)
    return 0


def _inventory_text(player: Entity) -> str:
    if player.inventory is None:
        return "인벤토리가 없습니다."
    slots = []
    for idx, item in enumerate(player.inventory.slots, start=1):
        key = "0" if idx == 10 else str(idx)
        label = f"{item.icon} {item.name}" if item else "(empty)"
        slots.append(f"{key}:{label}")
    return "인벤토리\n" + "\n".join(slots)


def _render_frame(manager: GameManager) -> None:
    dungeon = manager.dungeon
    grid = [[Renderer.WALL for _ in range(dungeon.width)] for _ in range(dungeon.height)]
    for x, y in dungeon.floor_tiles:
        grid[y][x] = Renderer.FLOOR
    for pos, items in manager.ground_items.items():
        if items:
            grid[pos[1]][pos[0]] = items[0].icon
    for entity in manager.entities:
        if entity is manager.player or not entity.is_alive:
            continue
        grid[entity.y][entity.x] = "👾"

    viewport = Renderer.compute_viewport(
        map_width=dungeon.width,
        map_height=dungeon.height,
        player_pos=manager.player.pos,
        viewport_width=20,
        viewport_height=12,
    )
    map_text = Renderer.render_viewport(grid, player_pos=manager.player.pos, viewport=viewport)
    status_text = manager.status_text()
    log_text = "\n".join(manager.logs[-8:]) if manager.logs else "-"

    try:
        from rich.console import Console

        console = Console()
        console.clear()
        layout = Renderer.build_layout(map_text=map_text, status_text=status_text, log_text=log_text)
        console.print(layout)
    except ModuleNotFoundError:
        print("\n[Map]")
        print(map_text)
        print("\n[Status]")
        print(status_text)
        print("\n[Log]")
        print(log_text)


if __name__ == "__main__":
    raise SystemExit(main())

