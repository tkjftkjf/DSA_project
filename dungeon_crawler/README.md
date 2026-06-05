# Dungeon Crawler (TUI Roguelike)

DS&A 과제용 턴 기반 TUI 로그라이크 프로토타입입니다.

## Quick Start (Local)

```bash
cd dungeon_crawler
python3 -m unittest discover -s tests -t . -p "test_*.py"
python3 -m dungeon_crawler.main
```

게임은 **리더보드 메인 화면**에서 시작합니다. Enter로 시작, `q`로 종료합니다.  
플레이 종료(승리/패배/esc) 후 점수가 리더보드에 저장됩니다 (`leaderboard.json`).

## Quick Start (Docker)

저장소 루트(`DSA_project`)에서 실행:

```bash
docker build -f dungeon_crawler/Dockerfile -t dungeon-crawler .
docker run -it --rm dungeon-crawler
```

테스트:

```bash
docker run --rm dungeon-crawler python -m unittest discover -s tests -t . -p "test_*.py"
```

## Controls

- `w/a/s/d`: 이동
- `c`: 근접 공격 모드 진입 후 `w/a/s/d`로 방향 선택
- `v`: 원거리 공격 모드 진입 후 `w/a/s/d`로 방향 선택 (화살 소모)
- `1~0`: 인벤토리 슬롯 아이템 사용
- `i`: 인벤토리 텍스트 출력
- `u/r`: 턴 단위 Undo/Redo
- `esc` 또는 `q`: 종료

## Implemented Core Features

- Dungeon room graph generation (preset room templates + spanning tree + cycle + corridors)
- Undo/Redo two-stack system with turn markers
- FIFO turn manager + deterministic per-turn RNG seed
- Inventory list/hash-map model + loot/consume action
- A* pathfinding with dynamic blockers + enemy vision/wander
- Insertion-sort leaderboard with JSON persistence
- Rich 기반 dynamic viewport renderer + main menu leaderboard screen
- Turn loop: move/combat(C/V+WASD), item use, undo/redo, victory/defeat scoring
