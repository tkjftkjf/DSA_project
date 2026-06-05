# Dungeon Crawler (TUI Roguelike)

DS&A 과제용 턴 기반 TUI 로그라이크입니다.

**구현 명세(발표·제출 기준):** 저장소 루트 [`Spec_Implemented.md`](../Spec_Implemented.md)

## Requirements

- Python 3.9+
- `rich>=13.7.1` (`requirements.txt`)

## Quick Start (Local)

```bash
cd dungeon_crawler
pip install -r requirements.txt
python3 -m unittest discover -s tests -q
python3 -m dungeon_crawler.main
```

- 메인 메뉴: **Enter** = 시작, **`q`** = 종료
- 인게임: **키 한 개 + Enter** (`명령 입력 >`)
- 종료 후 점수는 `leaderboard.json`에 저장 (gitignore)

## Quick Start (Docker)

저장소 루트(`DSA_project`)에서:

```bash
docker build -f dungeon_crawler/Dockerfile -t dungeon-crawler .
docker run -it --rm dungeon-crawler
```

> 플레이에는 **`-it`** 필수 (TTY 없으면 `input()` 동작 안 함).  
> 이미지는 `python:3.11-slim`(Linux) — 평가 환경과 유사.

테스트만:

```bash
docker run --rm dungeon-crawler python -m unittest discover -s tests -q
```

## Controls

**인게임 상세 조작 안내는 Status 패널에 항상 표시됩니다.** 메인 메뉴에도 요약이 있습니다.

| 키 | 동작 | 턴 소모 |
|----|------|---------|
| `w` `a` `s` `d` | 이동 (적 칸 = 근접 공격) | 성공 시 ○ |
| `c` → 방향 | 근접 공격 (인접 타일만) | 대상 있을 때 ○ |
| `v` → 방향 | 원거리 (화살 -1, 빗나가도 소모) | 발사 시 ○ |
| `1`~`9`, `0` | 인벤토리 슬롯 1~10 사용 | 성공 시 ○ |
| `i` | 인벤토리 표시 토글 | × |
| `u` / `r` | 턴 단위 Undo / Redo | × |
| `q` / `esc` | 메인 메뉴 포기 | × |

- 화살은 인벤토리 슬롯이 아니라 Status의 **Arrows** (시작 3개)
- 이동 성공 시 **바닥 아이템 자동 줍기**, **계단 자동 하강**
- **3층 계단** 도달 = 클리어 / HP 0 = 패배

## Game Overview

| 항목 | 값 |
|------|-----|
| 맵 | 53×30, 층당 12방 (start 1 + stair 1 + normal 10) |
| 층 | 3층, 계단으로 하강만 |
| 플레이어 | HP 20, ATK 5, DEF 1, LVL 1, 화살 3 |
| 시드 | 게임 시작 시각 (`time.time_ns()`), 수동 입력 없음 |

## Implemented Core Features (6)

1. **Dungeon Map** — TXT 템플릿, spanning tree + cycle, A* 통로 (`generation/`)
2. **Undo** — Two-Stack + Command Pattern + 턴 RNG 동기화
3. **Turn** — 플레이어 → 적 배치 resolve (`TurnResolver`) + `turn_id`/RNG
4. **Inventory** — List(10슬롯) + defaultdict counts, 자동 루팅
5. **Enemy AI** — 시야 6, A* 추적, blocker 우회·fallback
6. **Leaderboard** — Insertion sort top-10, JSON 영속화

## Tests

```bash
python3 -m unittest discover -s tests -q
# 99 tests (24 files)
```

## Project Layout

```
dungeon_crawler/
├── dungeon_crawler/   # 패키지 (main, engine, models, actions, generation, ui, utils)
├── tests/
├── requirements.txt
└── Dockerfile
```
