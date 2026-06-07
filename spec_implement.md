# **📜 TUI 로그라이크 게임 구현 명세서 (Implemented Spec)**

> **문서 목적:** 현재 `dungeon_crawler` 코드베이스에 **실제로 구현된** 기능만을 기술한다.  
> DS&A 팀 프로젝트 평가(PPT·라이브 데모·면접)에서 **Run it · Defend it · Compare it**를 방어하기 위한 발표용 명세이다.  
> 기존 [`Spec.md`](Spec.md)는 설계 초안·To-Be가 혼재되어 있으므로, **본 문서를 발표·제출 시 기준 문서**로 사용한다.

---

## **1. 프로젝트 개요 및 실행 환경**

| 항목 | 내용 |
| :---- | :---- |
| **장르** | 턴 기반 TUI 로그라이크 (룸 템플릿 기반 던전 크롤러) |
| **목적** | DS&A 과제 — 6 Core Features 구현 및 알고리즘·자료구조 정당화 |
| **언어** | Python 3.9+ (타입 힌팅 `typing` 사용) |
| **UI** | `rich` 라이브러리 — 좌측 Map / 우측 Status + Log 분할 레이아웃 |
| **실행** | `cd dungeon_crawler && python3 -m dungeon_crawler.main` |
| **의존성** | `rich>=13.7.1` (표준 라이브러리 + rich만 사용) |
| **입력 방식** | `input()` 기반 **라인 입력** (`\n명령 입력 >` 프롬프트 후 키 입력) |
| **테스트** | `python3 -m unittest discover -s tests` — **99 tests, 24 files, 전부 통과** |

### **1.1. 평가 3원칙 (Team Project Evaluation Guidance)**

| 원칙 | 본 프로젝트 대응 |
| :---- | :---- |
| **Run it** | 메인 메뉴 → 게임 시작 → 3층 탐험 → 클리어/패배/포기 → 점수·리더보드 저장까지 한 세션 완료 |
| **Defend it** | §2 각 기능마다 DS/알고리즘, 선택 이유, 코드 위치, 복잡도 명시 |
| **Compare it** | §2·§7 각 기능마다 대안 알고리즘과 트레이드오프 기술 |

---

## **2. 6대 핵심 기능 및 DS&A 설계 (발표 핵심)**

각 절은 평가 PPT **5단계 답변 템플릿**에 대응한다:  
① DS/알고리즘 명시 → ② 선택 이유 → ③ 코드 위치 → ④ 대안 비교 → ⑤ 복잡도·한계

---

### **2.1. Dungeon Map (2D Grid & Graph)**

#### **구현 요약**

* 월드 그리드 **53×30** (`WORLD_WIDTH`, `WORLD_HEIGHT`).
* **3개 층**, 층당 **12개 방** (시작 1 + 계단 1 + normal 10).
* `templates/rooms/{start,stair,normal}/*.txt` ASCII 템플릿을 월드 좌표에 스탬핑.
* 방 간 **Spanning Tree** + 추가 순환 간선(`extra_cycles=2`)으로 그래프 구성.
* 통로는 방 **외곽 타일**을 연결점으로 잡고, **A\***로 경로를 찾은 뒤 `protected` 영역(타 방 벽·내부)을 뚫지 않고 캐빙.

#### **사용 DS / 알고리즘**

* **2D Grid** (`set` 기반 `floor_tiles`, `_blocked`)
* **Graph** (`room_nodes`, `edges`)
* **Prim 유사 Spanning Tree** + 랜덤 extra edge
* **A\*** (통로 경로)

#### **선택 이유**

* Grid는 타일 단위 이동·충돌·렌더에 직접 대응.
* Spanning Tree는 모든 방을 **최소 연결**로 보장하고, extra cycle로 탐험 루트 다양화.
* L자 직선 복도는 다른 방을 관통하는 문제가 있어, **외곽 연결 + A\***로 우회.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| 월드 크기·템플릿 로더 | `dungeon_crawler/models/room_template.py` — `WORLD_WIDTH`, `WORLD_HEIGHT`, `RoomTemplateLoader` |
| 그리드 상태 | `dungeon_crawler/models/dungeon.py` — `Dungeon`, `is_walkable()` |
| 층 생성 오케스트레이터 | `dungeon_crawler/generation/floor_generator.py` — `FloorGenerator`, `FloorGeneratorConfig` |
| 앵커 배치 | `dungeon_crawler/generation/anchor_placer.py` — `scatter_anchors()` |
| 역할 할당 (start/stair/normal) | `dungeon_crawler/generation/role_assigner.py` — `assign_room_anchors()` |
| 템플릿 배치 | `dungeon_crawler/generation/template_assigner.py` — `assign_room_templates()` |
| 스탬핑 | `dungeon_crawler/generation/room_stamper.py` — `stamp_room()` |
| 그래프 | `dungeon_crawler/generation/room_graph.py` — `build_spanning_tree()`, `build_room_graph()` |
| 통로 | `dungeon_crawler/generation/corridor_carver.py` — `find_corridor_path()`, `carve_room_corridors()` |
| 3층 관리 | `dungeon_crawler/engine/floor_manager.py` — `FloorManager.create()` |

#### **주요 상수**

| 상수 | 값 | 위치 |
| :---- | :---- | :---- |
| 맵 크기 | 53 × 30 | `room_template.py` |
| 층당 방 수 | 12 | `session.py` → `room_count=12` |
| 앵커 최소 간격 | 10 | `FloorGeneratorConfig.anchor_min_spacing` |
| 앵커 그리드 step | 4 | `anchor_placer.py` |
| 추가 순환 간선 | 2 | `session.py` → `extra_cycles=2` |
| 최소 적 스폰 | 6 (미만 시 재생성) | `FloorGeneratorConfig.min_enemy_spawns` |
| 생성 재시도 | 최대 100회 | `FloorGeneratorConfig.max_generation_attempts` |
| 층별 시드 | `base_seed + floor_id * 97` | `floor_manager.py` |

#### **템플릿 타일 인코딩**

| 문자 | 의미 |
| :---- | :---- |
| `0` | 바닥 (이동 가능) |
| `1` | 벽 (차단) |
| `2` | 계단 (다음 층 이동 트리거) |
| `3` | 적 스폰 마커 |
| `4` | 아이템 스폰 마커 |

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **BFS/DFS로 방 연결** | 연결성 검사에는 적합하나, 본 프로젝트는 **거리 기반 Greedy Spanning Tree**로 구현 단순·결정적. |
| **L자 직선 복도** | 구현은 쉬우나 중간에 다른 방을 관통 → 현재는 **A\* + protected cells**로 해결. |
| **완전 랜덤 배치** | 겹침·연결 실패 빈번 → **앵커 scatter + spacing + overlap 검사**로 안정화. |

#### **시간·공간 복잡도**

* Grid 조회: O(1) (`set` membership)
* Spanning Tree: O(R²), R = 방 개수 (≤ 12)
* 통로 A\*: O(WH log(WH)) worst case, WH = 53×30
* 공간: O(WH) floor/blocked sets + O(R) room metadata

---

### **2.2. Undo System (Stack — Command Pattern)**

#### **구현 요약**

* **Two-Stack** (`undo_stack`, `redo_stack`) + **Command Pattern**.
* 모든 행동은 `execute()` / `undo()`를 가진 원자적 Action.
* 턴 종료 시 `EndTurnAction(turn_id)` 마커로 턴 경계 표시.
* `u` / `r` 입력 시 **해당 턴의 모든 액션**을 역순 undo 또는 redo.
* Undo 후 새 행동 시 `redo_stack` 초기화.
* 턴마다 `random.seed(base_seed + turn_id)`로 RNG 고정.

#### **사용 DS / 알고리즘**

* **Stack (LIFO)** — Python `list`로 push/pop
* **Command Pattern** — Action 클래스 군

#### **선택 이유**

* Undo는 **마지막에 한 행동을 먼저 되돌리는** LIFO 패턴 → Stack이 자연스럽게 맞음.
* 전체 스냅샷 대신 **delta(변경분)만** Action에 저장 → 메모리 절약.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| Two-Stack 관리 | `dungeon_crawler/engine/undo_manager.py` — `UndoManager` |
| 턴 마커 | `dungeon_crawler/actions/marker_action.py` — `EndTurnAction` |
| 이동 | `dungeon_crawler/actions/move_action.py` — `MoveAction` |
| 전투 | `dungeon_crawler/actions/combat_action.py` — `CombatAction` |
| 루팅 | `dungeon_crawler/actions/loot_action.py` — `LootAction` |
| 소비 | `dungeon_crawler/actions/consume_action.py` — `ConsumeAction` |
| RNG 동기화 | `dungeon_crawler/engine/turn_manager.py` — `prepare_turn_rng()` |
| 플레이어 undo/redo | `dungeon_crawler/engine/game_manager.py` — `undo_turn()`, `redo_turn()` |

#### **Action 클래스 명세 (구현됨)**

| Action | execute() | undo() | 저장 상태 |
| :---- | :---- | :---- | :---- |
| **MoveAction** | 좌표 이동 | 이전 좌표 복원 | `_previous_pos` |
| **CombatAction** | 데미지, 사망 시 풀 제거·EXP | HP/alive/EXP/풀 복원 | `_damage`, `_defender_prev_hp`, `_removed_index` |
| **LootAction** | 바닥→인벤 | 인벤→바닥 | `_item`, `_inventory_slot` |
| **ConsumeAction** | 슬롯 소모·회복 | 슬롯·HP 복원 | `_item`, `_previous_hp` |
| **EndTurnAction** | (마커) | (마커) | `turn_id` |

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **전체 상태 스냅샷** | 구현 단순하나 맵·엔티티 전체 복사 → 메모리 O(맵 크기 × 턴 수). 현재는 O(턴당 액션 수). |
| **Queue** | FIFO → Undo 순서가 뒤집혀 부적합. |
| **Memento without Command** | Action 없이 상태만 저장하면 역연산 로직이 분산 → Command가 응집도 높음. |

#### **시간·공간 복잡도**

* push / pop: O(1)
* undo 1턴: O(k), k = 해당 턴 액션 수
* 공간: O(총 기록 액션 수)

---

### **2.3. Turn Management (Batch Resolve + Turn Counter)**

#### **구현 요약**

* **실제 게임 루프:** 플레이어 1액션 → `run_enemy_turns()` (현재 층 모든 적) → `finalize_turn()`.
* `TurnManager`: `turn_id` 카운터 + `prepare_turn_rng()` (턴당 `random.seed(base_seed + turn_id)`).
* `TurnResolver`: 적 propose → `ActionValidator` 검증 → 실패 시 fallback (최대 8회) → 확정 액션 `list` 반환.
* `GameManager.run_enemy_turns()`: 반환된 액션을 순차 `execute()` + `UndoManager.record()`.

#### **사용 DS / 알고리즘**

* **List (배치 큐)** — `TurnResolver.collect_actions()`가 턴 내 확정 액션 리스트 구성
* **턴 카운터** — `TurnManager.turn_id`로 RNG 동기화·Undo 마커 경계

#### **선택 이유**

* 플레이어 턴과 적 턴을 **명시적 단계**로 분리해 Undo 경계·로그가 명확.
* Spec.md의 per-entity FIFO 순환 큐는 TUI UX(플레이어 선행)와 맞지 않아 **배치 모델**만 유지.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| 메인 루프 | `dungeon_crawler/main.py` — `run_game_loop()` |
| 턴 종료·적 실행 | `dungeon_crawler/engine/game_manager.py` — `finalize_turn()`, `run_enemy_turns()` |
| 턴 ID·RNG | `dungeon_crawler/engine/turn_manager.py` — `TurnManager` |
| propose→validate | `dungeon_crawler/engine/turn_resolver.py` — `TurnResolver`, `EntityTurnPlan` |
| 검증 | `dungeon_crawler/utils/action_validator.py` — `ActionValidator` |

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **FIFO per-entity Queue** | Spec.md To-Be. 공정 순환에 적합하나 본 게임은 **플레이어→적 일괄**이 UX에 맞음. |
| **Priority Queue** | AGI(속도) 차등 캐릭터에 적합. 현재 스탯 모델에 과잉. |
| **Realtime tick** | TUI 턴제와 맞지 않음. |

#### **시간·공간 복잡도**

* 턴 ID 증가·RNG seed: O(1)
* 적 턴 1회: O(E × F), E = 적 수, F = fallback 시도 (≤ 8)

---

### **2.4. Item Inventory (List & Hash Map)**

#### **구현 요약**

* **10칸 슬롯** `list[Item | None]` + **이름별 개수** `defaultdict[str, int]`.
* 바닥 아이템은 `ground_items_by_floor[floor_id][(x,y)]`에 저장.
* 이동 시 해당 타일 아이템 **자동 루팅** (`LootAction`).
* `1`~`0` 키로 슬롯 아이템 **즉시 사용** (`ConsumeAction`).
* **화살은 인벤토리 미사용** — `Entity.arrows` 정수 변수 (시작 3개).
* HP가 이미 최대면 회복 아이템 사용 거부.

#### **사용 DS / 알고리즘**

* **List** — 고정 10슬롯 순서 (UI 슬롯 번호)
* **Hash Map** — `defaultdict`로 아이템 이름별 개수 O(1) 조회

#### **선택 이유**

* List는 **슬롯 UI(1~0 키)** 와 1:1 대응.
* Dict는 **이름별 개수 표시·검색**에 O(1).
* 10칸 규모에서 Tree는 과잉.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| 인벤토리 | `dungeon_crawler/models/inventory.py` — `Inventory` |
| 아이템 정의 | `dungeon_crawler/models/item.py` — `Item` |
| 화살 (별도 변수) | `dungeon_crawler/models/entity.py` — `Entity.arrows` |
| 초기 화살 3 | `dungeon_crawler/engine/session.py` — `create_game_manager()` |
| 루팅 | `dungeon_crawler/actions/loot_action.py` — `LootAction` |
| 소비 | `dungeon_crawler/actions/consume_action.py` — `ConsumeAction` |
| 검증 | `dungeon_crawler/utils/action_validator.py` — `_validate_loot()`, `_validate_consume()` |
| 자동 루팅 | `dungeon_crawler/engine/game_manager.py` — `_try_auto_loot()` |
| 하트 스폰 | `dungeon_crawler/engine/spawn_resolver.py` — `spawn_ground_items()` |

#### **하트 6종 (구현됨)**

| 이름 | 이모지 | 회복량 |
| :---- | :---- | :---- |
| heart_red | ❤️ | 3 |
| heart_orange | 🧡 | 5 |
| heart_yellow | 💛 | 10 |
| heart_green | 💚 | 15 |
| heart_blue | 💙 | 20 |
| heart_purple | 💜 | 30 |

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **Dict only** | 슬롯 순서·UI 매핑이 어려움. |
| **List only** | 이름별 개수 집계가 O(n). |
| **Tree (BST)** | 검색 O(log n)이나 n=10에서 이점 미미, 구현 복잡도만 증가. |

#### **시간·공간 복잡도**

* add/remove slot: O(S), S=10 (선형 탐색 빈 슬롯)
* counts 조회: O(1) average
* 공간: O(S + U), U = 유니크 아이템 종류 수

---

### **2.5. Enemy AI (A\* Pathfinding)**

#### **구현 요약**

* **시야 반경 6** (`ENEMY_VISION_RADIUS`) 이내: A\*로 플레이어 추적.
* **인접 시:** `CombatAction`으로 근접 공격.
* **시야 밖:** 랜덤 방향 배회 (턴 내 방향 유지).
* A\* 시 **바닥 아이템·다른 적**을 blocker로 처리.
* 경로 없으면 blocker 확대 후 **재시도**, 그래도 실패 시 fallback/wander.
* `TurnResolver`가 최대 **8회** fallback 시도.

#### **사용 DS / 알고리즘**

* **A\*** (4방향 그리드, 휴리스틱 = 맨해튼 거리)
* **min-heap** 우선순위 큐 (`heapq`)

#### **선택 이유**

* 가중치 없는 그리드에서 A\*는 **최단 경로** 보장 + 맨해튼 휴리스틱으로 구현 단순.
* BFS도 동일 결과이나, A\*는 휴리스틱으로 탐색 노드 수를 줄일 수 있음.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| A\* | `dungeon_crawler/utils/pathfinding.py` — `find_path()` |
| AI 제안 | `dungeon_crawler/engine/game_manager.py` — `_propose_enemy_action()`, `_enemy_fallback()` |
| 적 턴 배치 | `dungeon_crawler/engine/game_manager.py` — `run_enemy_turns()` |
| 검증·fallback | `dungeon_crawler/engine/turn_resolver.py` — `_resolve_plan()` |

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **BFS** | 비가중 그리드에서 A\*와 동등한 최단 경로. 본 프로젝트 A\* 휴리스틱=맨해튼 → 사실상 동급. |
| **DFS** | 최단 보장 없음, 벽에 갇히기 쉬움. |
| **Dijkstra** | 가중치 없는 그리드에서 A\*와 동일, 오버킬. |

#### **시간·공간 복잡도**

* A\*: O(E log V), V ≤ WH, E ≤ 4V
* 공간: O(V) closed/open set

---

### **2.6. Leaderboard (Insertion Sort — Top-K)**

#### **구현 요약**

* 최대 **10개** 기록 유지 (`Leaderboard(capacity=10)`).
* 새 기록 삽입 시 **Insertion Sort**로 score 내림차순, level 내림차순 정렬.
* JSON 파일 `dungeon_crawler/leaderboard.json`에 영속화.
* 메인 메뉴에서 리더보드 표시.

#### **사용 DS / 알고리즘**

* **Array (list)** + **Insertion Sort**
* Top-K 유지 (capacity 초과 시 truncate)

#### **선택 이유**

* 기록 수 n ≤ 10으로 **작은 배열** → Insertion Sort가 단순·충분.
* Top-10만 필요 → 전체 대용량 정렬 불필요.

#### **코드 위치**

| 역할 | 파일 · 함수/클래스 |
| :---- | :---- |
| 정렬·Top-K | `dungeon_crawler/utils/leaderboard.py` — `Leaderboard._insertion_sort_desc()` |
| JSON 저장 | `dungeon_crawler/utils/leaderboard_store.py` — `load_leaderboard()`, `save_leaderboard()` |
| 메뉴 표시 | `dungeon_crawler/ui/menu.py` — `render_main_menu()` |
| 점수 계산 | `dungeon_crawler/engine/session.py` — `compute_score()` |
| 게임 종료 저장 | `dungeon_crawler/main.py` — `main()` |

#### **점수 공식**

```
score = exp + level * 100 + turn_id * 2 + kills * 50
```

#### **대안 비교**

| 대안 | 비교 |
| :---- | :---- |
| **전체 Tim Sort O(n log n)** | n≤10에서 이점 없음. |
| **Min-Heap Top-K O(n log k)** | k=10 고정이면 적합하나, n이 작아 Insertion Sort로 충분. |
| **Bubble Sort O(n²)** | n=10이면 체감 동일하나 비교·swap 상수 더 큼. |

#### **시간·공간 복잡도**

* 삽입 + 정렬: O(n²) worst, n ≤ 10
* 공간: O(capacity) = O(10)

---

## **3. 게임플레이 및 엔티티 명세 (현재 구현)**

### **3.1. Entity 스탯 및 성장**

| 속성 | 플레이어 시작값 | 비고 |
| :---- | :---- | :---- |
| HP / maxHP | 20 / 20 | |
| ATK | 5 | |
| DEF | 1 | |
| Level | 1 | |
| EXP | 0 | Status: `EXP: 현재/필요` (필요 = `level * 10`) |
| Arrows | 3 | 인벤토리 슬롯 아님 |

* **데미지:** `max(1, attacker.atk - defender.defense)`
* **레벨업:** `while exp >= level * 10` → level++, maxHP+2, atk+1, def+1, **HP 풀회복**
* **적 스탯:** 층별 RNG 범위 (`SpawnResolver.FLOOR_STAT_RANGES`)

| 층 | HP | ATK | DEF | EXP 보상 |
| :---- | :---- | :---- | :---- | :---- |
| 1 | 6–10 | 2–4 | 0–1 | 4–8 |
| 2 | 10–16 | 3–6 | 0–2 | 8–14 |
| 3 | 14–22 | 5–8 | 1–3 | 12–20 |

### **3.2. 조작 (상세)**

#### **3.2.1. 입력 방식**

* **라인 입력:** 매 프레임마다 `명령 입력 >` 프롬프트가 표시되고, **키 하나(또는 `esc`)를 입력한 뒤 Enter**를 눌러야 한다.
* **대소문자 무시:** `W`와 `w` 동일 (`InputHandler.parse_key`가 `lower()` 처리).
* **한 줄에 한 명령:** `wd`, `c w` 같은 연속 입력은 지원하지 않는다. 이동·공격마다 Enter가 필요하다.
* **실시간 키 입력 없음:** `pynput` 미연동. Enter 없이 키만 누르는 방식은 동작하지 않는다.

#### **3.2.2. 메인 메뉴 (리더보드 화면)**

| 입력 | 동작 |
| :---- | :---- |
| **Enter** (빈 입력 포함) | 새 게임 시작 |
| `q` | 프로그램 종료 |

* 상위 10개 점수·터미널 너비가 표시된다 (`ui/menu.py`).
* 게임 종료(승리/패배/포기) 후 `메인으로 돌아가려면 Enter >`에서 **Enter** → 메인 메뉴 복귀, **`q`** → 프로그램 종료.

#### **3.2.3. 인게임 — 턴을 소모하는 행동**

아래 행동이 **성공**하면 `turn_consumed = True` → **현재 층 모든 적 턴** → `finalize_turn()` (턴 ID 증가, `EndTurnAction` 마커).

| 입력 | 동작 | 성공 조건 | 실패 시 (턴 미소모) |
| :---- | :---- | :---- | :---- |
| `w` `a` `s` `d` | 한 칸 이동 | 목표 타일 이동 가능 | 벽·점유·맵 밖 |
| `w` `a` `s` `d` | 이동 중 전투 | 목표 타일에 **적** 있음 → 근접 `CombatAction` | — |
| `c` → `w/a/s/d` | 근접 공격 | 해당 방향 **인접 타일**에 적 존재 | 대상 없음 |
| `v` → `w/a/s/d` | 원거리 발사 | 화살 ≥ 1 (발사 시 **항상 1 소모**) | 화살 0개 |
| `1`~`9`, `0` | 슬롯 아이템 사용 | 슬롯에 아이템 있음, HP 미만일 때(회복품) | 빈 슬롯, HP 가득 |

**이동 성공 시 자동 처리 (추가 입력 불필요):**

1. **자동 루팅** — 해당 타일 바닥 아이템이 있고 인벤토리 여유가 있으면 `LootAction` 실행.
2. **계단 하강** — 계단 타일(`▃▅`) 위이면 자동으로 다음 층 `start_spawn`으로 이동. 3층 계단이면 **클리어**.

#### **3.2.4. 인게임 — 턴을 소모하지 않는 행동**

| 입력 | 동작 |
| :---- | :---- |
| `c` | 근접 공격 모드 진입. Status에 `Mode: 근접(C) - WASD로 방향 선택` 표시. 로그: `[WASD를 통해 공격 방향을 정하세요]` |
| `v` | 원거리 공격 모드 진입. Status에 `Mode: 원거리(V) - WASD로 방향 선택` 표시. 동일 안내 로그. |
| `i` | 인벤토리 표시 on/off (Status 패널에 `Inventory: 1:❤️ 2:- ... 0:-` 형식) |
| `u` | **Undo** — 직전 턴(`EndTurnAction` 마커까지)의 모든 액션 역실행. 로그: `[System] 턴 N의 행동을 되돌렸습니다.` |
| `r` | **Redo** — Undo로 되돌린 턴 재적용 |
| (빈 입력) | 무시 |
| 알 수 없는 키 | 로그: `알 수 없는 입력입니다.` |

* **Undo/Redo 후** 플레이어가 새 행동을 하면 Redo 스택이 초기화된다 (`UndoManager` 규칙).
* **공격 모드 중** `c`/`v`를 다시 누르면 모드가 덮어씌워진다. `esc`로 모드만 취소하는 전용 키는 없다.

#### **3.2.5. 이동·공격 방향**

| 키 | 방향 | 좌표 변화 |
| :---- | :---- | :---- |
| `w` | 위 | `dy = -1` |
| `s` | 아래 | `dy = +1` |
| `a` | 왼쪽 | `dx = -1` |
| `d` | 오른쪽 | `dx = +1` |

* **일반 이동:** 공격 모드가 **꺼져 있을 때** WASD는 이동. 적이 있는 칸으로 가면 **이동 대신 근접 공격**.
* **공격 모드:** `c` 또는 `v` 입력 **이후** WASD는 이동이 아니라 **해당 방향 공격/발사**.
* 공격 모드에서 방향을 정하면 `pending_attack_mode`가 해제된다 (한 번의 공격 시도 후 모드 종료).

#### **3.2.6. 인벤토리·화살**

| 항목 | 설명 |
| :---- | :---- |
| **슬롯** | 10칸 (`1`~`9` = 슬롯 1~9, `0` = 슬롯 10) |
| **표시** | `i`로 토글. `key:아이콘` 또는 `key:-` (빈 칸) |
| **아이템 종류** | 하트 6종 (❤️🧡💛💚💙💜), 회복량 3~30 |
| **HP 가득** | 회복 아이템 사용 거부, 로그: `체력이 가득 차 아이템을 사용할 수 없습니다.` |
| **화살 🏹** | 인벤토리 **슬롯 아님**. Status `Arrows: N`. 시작 3개. `v`+방향 발사 시 1 소모 (명중/빗나감 무관) |

#### **3.2.7. 종료·포기**

| 입력 | 결과 | 리더보드 |
| :---- | :---- | :---- |
| `q` / `esc` (인게임) | 메인 메뉴 복귀 (`retreat`) | 현재까지 점수 저장 |
| HP ≤ 0 | 패배 (`defeat`) | 저장 |
| 3층 계단 클리어 | 승리 (`victory`) | 저장 |

#### **3.2.8. 한 턴의 흐름 (조작 관점)**

```
[화면 렌더] → 명령 입력 > (한 키 + Enter)
  → (턴 소모 행동이면) 플레이어 액션 실행
  → run_enemy_turns()  # 현재 층 적 전원
  → finalize_turn()    # turn_id++, EndTurnAction
  → (승리/패배 검사)
[다시 화면 렌더]
```

* 턴을 소모하지 않은 입력(모드 전환, Undo, 인벤토리 토글 등)은 **적 턴 없이** 바로 다음 입력을 받는다.

#### **3.2.9. 빠른 참조표**

| 입력 | 동작 | 턴 소모 |
| :---- | :---- | :---- |
| `w` / `a` / `s` / `d` | 이동 (또는 공격 모드 시 방향 공격) | 성공 시 ○ |
| `c` | 근접 모드 진입 | × |
| `v` | 원거리 모드 진입 | × |
| `1` ~ `9`, `0` | 슬롯 아이템 사용 | 성공 시 ○ |
| `i` | 인벤토리 표시 토글 | × |
| `u` / `r` | Undo / Redo | × |
| `q` / `esc` | 메인 메뉴 포기 | × (세션 종료) |
| (빈 입력) | 무시 | × |

### **3.3. 전투·원거리**

* **근접:** 인접 타일 적에게 `CombatAction` (이동으로 충돌 시에도 전투).
* **원거리:** 직선 궤적 추적. 벽·맵 밖·바닥 아이템에서 정지. 적 명중 시 `CombatAction`.
* **화살:** 발사 시 1 소모 (명중/빗나감 무관). `Entity.arrows`에서 차감.

### **3.4. 층·계단·승리 조건**

* **3개 층** 독립 생성 (`FloorManager`).
* 계단 타일(`2`) 위로 이동 시 **자동 하강** → 다음 층 `start_spawn`.
* **3층 계단** 진입 시 `dungeon_cleared = True` → **클리어 (victory)**.
* 패배: HP ≤ 0. 포기: `q` / `esc`.

### **3.5. 세션 시드**

* `derive_session_seed()` = `time.time_ns() % 2**31` (게임 시작 시각).
* 맵 생성·스폰·턴 RNG `base_seed`에 사용. **수동 시드 입력 없음**.

---

## **4. 맵 생성 파이프라인 상세**

```
scatter_anchors → assign_room_anchors → assign_room_templates
    → stamp_room → build_room_graph → carve_room_corridors
    → (enemy_spawn < 6 이면 seed+131 재시도, 최대 100회)
```

### **4.1. normal 템플릿 보장**

* `room_count >= 12`일 때 normal 10종 템플릿을 **각 1회씩** 배치 (`_build_normal_template_plan`).
* 추가 normal 슬롯이 있으면 랜덤 중복 허용.

### **4.2. start 방**

* `start_templates_only()` — **5×5** 템플릿만 시작 방으로 사용.

### **4.3. 통로 (corridor_carver)**

* 연결점: 각 방 **perimeter floor tiles** 중 맨해튼 거리 최소 쌍 (여러 후보 시도).
* `protected`: 타 방 템플릿 영역 + 연결 양방의 벽 → 통과·캐빙 금지.
* 경로: A\* on passable cells.

### **4.4. 구 Spec.md(To-Be)와의 차이**

| 항목 | 구 Spec.md (To-Be) | **현재 구현** |
| :---- | :---- | :---- |
| 맵 크기 | 80×45 | **53×30** |
| 방 배치 | 5×5 메타 그리드 + 병합 | **앵커 scatter + overlap 검사** |
| normal 보장 | (미명시) | **10종 각 1회** |
| 통로 | 0 타일 개구부만 | **외곽 연결 + A\*** |
| 화살 | 인벤토리 | **`Entity.arrows` 별도** |
| 승리 | (적 전멸 등) | **3층 계단 클리어** |
| Debug 모드 | ON/OFF | **제거됨** |

---

## **5. UI / 렌더링 아키텍처**

### **5.1. Layout**

* `rich.layout.Layout` — 좌 2 : 우 1 (`Map` | `Status` + `Log`).
* **전체 패널 높이:** `layout_height = terminal_height - INPUT_RESERVE_ROWS` (2줄 = 입력 프롬프트 예약).
* `console.print(layout, height=layout_height)` 로 **Map·Status·Log 블록 전체** 높이 제한.

### **5.2. Dynamic Viewport**

* `Renderer.compute_viewport_size()` — 터미널·이모지 2칸 너비 고려.
* 플레이어 중심 카메라 (`compute_viewport`).
* 맵 타일 행 수 ≈ `layout_height - PANEL_BORDER_ROWS` (2).

### **5.3. 표시 기호**

| 대상 | 기호 |
| :---- | :---- |
| 벽 (비바닥) | 🟫 |
| 바닥 | ⬛ |
| 계단 | ▃▅ |
| 플레이어 | 🧙 |
| 적 (현재 층) | 👾 |
| 바닥 아이템 | 아이템 이모지 (첫 번째) |

### **5.4. Status 패널**

```
Turn: {turn_id}
HP: {hp}/{max_hp}
ATK/DEF: {atk}/{defense}
LVL: {level}
EXP: {exp}/{level * 10}
Kills: {kills}
Arrows: {arrows}
(+ i 토글 시 Inventory: 1:❤️ 2:- ...)
```

### **5.5. Log**

* 최근 **10줄** append-only.
* Undo 시 기존 로그 삭제 없이 `[System] 턴 N의 행동을 되돌렸습니다.` 추가.

---

## **6. 프로젝트 디렉터리 구조**

```
DSA_project/
├── Spec.md                      # 설계 초안 (To-Be 혼재)
├── Spec_Implemented.md          # 본 문서 (As-Is, 발표 기준)
└── dungeon_crawler/
    ├── requirements.txt
    ├── leaderboard.json         # 런타임 리더보드 저장
    ├── dungeon_crawler/
    │   ├── main.py              # 엔트리, 게임 루프, 렌더
    │   ├── engine/
    │   │   ├── game_manager.py
    │   │   ├── session.py
    │   │   ├── floor_manager.py
    │   │   ├── turn_manager.py
    │   │   ├── turn_resolver.py
    │   │   ├── undo_manager.py
    │   │   ├── spawn_resolver.py
    │   │   └── input_handler.py
    │   ├── generation/
    │   │   ├── floor_generator.py
    │   │   ├── anchor_placer.py
    │   │   ├── role_assigner.py
    │   │   ├── template_assigner.py
    │   │   ├── template_pools.py
    │   │   ├── room_stamper.py
    │   │   ├── room_graph.py
    │   │   ├── corridor_carver.py
    │   │   ├── geometry.py
    │   │   └── types.py
    │   ├── models/
    │   │   ├── dungeon.py
    │   │   ├── entity.py
    │   │   ├── item.py
    │   │   ├── inventory.py
    │   │   ├── room_template.py
    │   │   └── room_node.py
    │   ├── actions/
    │   │   ├── move_action.py
    │   │   ├── combat_action.py
    │   │   ├── loot_action.py
    │   │   ├── consume_action.py
    │   │   └── marker_action.py
    │   ├── utils/
    │   │   ├── pathfinding.py
    │   │   ├── action_validator.py
    │   │   ├── leaderboard.py
    │   │   └── leaderboard_store.py
    │   ├── ui/
    │   │   ├── renderer.py
    │   │   └── menu.py
    │   └── templates/rooms/
    │       ├── start/   (6 files)
    │       ├── stair/   (6 files)
    │       └── normal/  (10 files)
    └── tests/           (24 files, 99 tests)
```

---

## **7. 발표용 부록 (Evaluation PPTX 연동)**

### **7.1. 제출 전 체크리스트 (Slide 2)**

- [ ] AI+X Studio 컴퓨터에서 `python3 -m dungeon_crawler.main` 실행 확인
- [ ] 시작 → 플레이 → 클리어/패배/포기 → 리더보드 저장까지 크래시 없음
- [ ] 6대 기능 코드 존재 (§2 참조)
- [ ] 각 기능 DS/알고리즘·대안·복잡도 설명 가능
- [ ] PPT 내용이 **본 문서(Spec_Implemented.md)** 와 일치
- [ ] 각 기능 **파일명·함수명** 암기 (§2 코드 위치 표)
- [ ] §7.3 예상 질문 리허설

### **7.2. 기능별 5단계 답변 스크립트 (Slide 10)**

**Dungeon Map**  
"We use a 2D Grid and a Graph (spanning tree + A\* corridors). The grid maps directly to walkability and rendering; the graph guarantees all rooms are connected. Code is in `generation/floor_generator.py` and `corridor_carver.py`. BFS could connect rooms too, but we use greedy spanning tree for simplicity; straight L-corridors cut through rooms, so we use A\* with protected cells. Grid lookup is O(1); spanning tree is O(R²) for R≤12 rooms."

**Undo System**  
"We use a two-stack LIFO structure with the Command Pattern. Undo is last-in-first-out, matching Stack access. `UndoManager` in `engine/undo_manager.py` pushes `MoveAction`, `CombatAction`, etc., and pops until `EndTurnAction`. A Queue would replay in the wrong order. Push/pop are O(1); memory grows with actions per session."

**Turn Management**  
"We use a batch resolve loop: player acts, then `TurnResolver.collect_actions()` validates enemy proposals, then `GameManager` executes them. `TurnManager` only tracks `turn_id` and per-turn RNG seed. A FIFO per-entity queue (in our old Spec) would rotate all entities fairly, but player-then-enemies phases fit our TUI better. Enemy fallback tries up to 8 validated proposals per turn."

**Item Inventory**  
"We use a List for 10 UI slots and a defaultdict Hash Map for name counts in `models/inventory.py`. Arrows are a separate `Entity.arrows` int, not inventory slots. A Tree would be overkill for 10 slots; Dict-only loses slot order for keys 1–0."

**Enemy AI**  
"We use A\* in `utils/pathfinding.py` with Manhattan heuristic. Enemies within radius 6 chase; otherwise wander. Blockers include items and other enemies; we retry with expanded blockers. BFS gives the same shortest path on unweighted grids; DFS doesn't guarantee shortest. A\* is O(E log V) on the grid."

**Leaderboard**  
"We use Insertion Sort on a small array (capacity 10) in `utils/leaderboard.py`. Only top-10 matters; n is tiny so O(n²) is fine. A Heap would be O(n log k) for larger n, but unnecessary here. Scores persist to `leaderboard.json`."

### **7.3. 예상 질문 치트시트 (Slide 9)**

| 주제 | 핵심 답 + 코드 |
| :---- | :---- |
| **맵 DS** | 2D Grid (`Dungeon.floor_tiles`, `_blocked`) + Graph (`room_nodes`, `edges`). 이동: `is_walkable()`. |
| **이동 경로 검사** | 플레이어·적: `ActionValidator._validate_move` + `pathfinding.find_path` (A\*). |
| **Undo Stack** | Delta만 저장 (`actions/*`). 전체 스냅샷 대비 메모리 절약. `undo_manager.py`. |
| **Turn** | `TurnManager` = turn_id + RNG. `TurnResolver` = propose→validate list. PQ는 속도 차등 시. |
| **Inventory** | List+Dict. 화살은 `entity.arrows`. 10칸에서 Tree 이점 없음. |
| **Enemy AI** | A\*, vision=6, `game_manager._propose_enemy_action`. BFS 동급, DFS 비최단. |
| **Leaderboard** | Insertion sort, top-10. Heap은 대규모 n용. `leaderboard.py`. |

### **7.4. 구현 범위 밖 (발표 시 혼동 방지)**

다음은 **Spec.md To-Be에만 있고 현재 코드에 없음**, 또는 **의도적으로 미구현**:

| 항목 | 상태 |
| :---- | :---- |
| `pynput` 실시간 키 입력 | 미구현 (`input()` 사용) |
| `@validate_action` decorator | 제거됨 (`ActionValidator` 직접 호출) |
| Debug 모드 / 이동 디버그 로그 | 미구현 |
| 메타그리드 5×5 병합 | 미구현 (anchor scatter 배치) |
| 보스 적 / `boss` 템플릿 | 미구현 |
| 적 전멸 승리 | 미구현 (3층 계단 = 클리어) |
| per-entity FIFO 턴 큐 / `DelayedAction` | 미구현 (배치 턴) |
| 층 올라가기 (ascend) | 미구현 (하강만) |
| Fog of war | 미구현 |
| 수동 시드 / 리플레이 UI | 미구현 |
| 맵 80×45 | 현재 53×30 |

---

## **8. 테스트 및 수용 기준**

### **8.1. 실행**

```bash
cd dungeon_crawler
python3 -m unittest discover -s tests
```

**결과:** 99 tests, 0 failures (기준 시점).

### **8.2. 테스트 ↔ 기능 매핑**

| 테스트 파일 | 검증 대상 |
| :---- | :---- |
| `test_dungeon_generation.py` | 방 겹침 없음, spanning tree, 통로, 벽 관통 없음 |
| `test_floor_generation.py` | 월드 크기, start/stair, normal 10종, 경로 도달, 적 스폰 수 |
| `test_floor_manager.py` | 3층 생성, 하강, stair_links |
| `test_room_template_loader.py` | TXT 파싱 |
| `test_session.py` | 시드, 점수, `create_game_manager` |
| `test_undo_manager.py` | Two-Stack, 턴 마커 |
| `test_turn_manager.py` | turn_id, RNG seed |
| `test_turn_resolver.py` | propose→validate→fallback |
| `test_action_validator.py` | 이동/소비/층간 점유 |
| `test_move_action.py` | Move execute/undo |
| `test_combat_action.py` | Combat, EXP, kill |
| `test_loot_action.py` | Loot execute/undo |
| `test_consume_action.py` | Consume, max HP cap |
| `test_pathfinding.py` | A\*, blockers |
| `test_ranged_projectile.py` | 화살 소모, 피격 |
| `test_gameplay_flow.py` | 전투, 루팅, 계단, 3층 클리어, 레벨업 |
| `test_spawn_resolver.py` | 층별 스탯·하트 RNG |
| `test_renderer.py` | 뷰포트, 스크롤 |
| `test_viewport_size.py` | 터미널 크기, layout_height 예약 |
| `test_leaderboard.py` | Insertion sort, top-10 |
| `test_leaderboard_store.py` | JSON 영속화 |
| `test_menu.py` | 메인 메뉴 |
| `test_input_handler.py` | 키 파싱 |
| `test_game_manager.py` | execute, undo/redo |

### **8.3. 수용 기준 (Implemented)**

| # | 항목 | 기대 결과 |
| :---- | :---- | :---- |
| 1 | 월드 크기 | 53×30 |
| 2 | 3층·계단 | 1–2층 계단 진입 시 하강, 3층 계단 시 victory |
| 3 | TXT 템플릿 | 0/1/2/3/4 파싱, start 5×5 |
| 4 | normal 10종 | room_count=12 시 층당 10종 각 1회 |
| 5 | 통로 | 다른 방 벽 관통 없음 (`test_corridors_do_not_punch_through_room_walls`) |
| 6 | Undo/Redo | 턴 단위 복원, RNG `base_seed+turn_id` |
| 7 | 인벤토리 | 10슬롯, 자동 루팅, HP full 시 consume 거부 |
| 8 | 화살 | `Entity.arrows`, V+WASD, 미명중도 소모 |
| 9 | Enemy AI | A\*, vision 6, blocker retry |
| 10 | Leaderboard | top-10 insertion sort, JSON 저장 |
| 11 | UI | layout_height = terminal − 2, 3패널 |
| 12 | 층간 유령 점유 | 다른 층 적이 이동 block 안 함 |

---

## **9. 문서 이력**

| 버전 | 날짜 | 설명 |
| :---- | :---- | :---- |
| Implemented v1 | 2026-06-05 | 현재 코드 기준 최초 작성. 평가 PPTX·Spec.md 형식 통합. |
