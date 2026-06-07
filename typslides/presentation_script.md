# 발표 대본 — Core Features × DS&A

> 슬라이드에는 **키만** 표시됩니다. 아래 내용을 말로 풀어서 설명하세요.  
> 각 슬라이드 약 **30~45초** 목표.

---

## Dungeon Map

### 이동 및 충돌 검사 — set

- **장점:** 사용하는 타일만을 기억하여, 메모리를 아낄 수 있음. Python 내부적으로 hash table로 구현되어 있어 빠른 조회.
- **단점:** 맵의 크기(53×30)를 표현할 수 없어, 범위 검사를 따로 진행해야 함.

---

### 이동 및 충돌 검사 — 2D array

- **장점:** 인덱스 접근 O(1), 구현 직관적
- **단점:** 전체 1,590칸 항상 할당
- **설명:** 바닥이 없는 빈 공간까지 메모리 점유

---

### Graph

**한 줄:** 12개 방을 노드로, 복도로 이어지는 관계를 `edges`로 표현합니다.

`room_nodes`는 방 ID → `RoomNode`(타일 집합, 앵커, center)이고, `edges`는 `(room_a, room_b)` 무방향 간선 set입니다. 방이 최대 12개라 인접 행렬 12×12는 과하고, 간선 set이면 연결 관계만 깔끔하게 다룹니다. 이 그래프 위에서 spanning tree를 만들고, 통로 캐빙은 edge마다 한 번씩 돕니다.

- **복잡도:** 노드 O(R), 간선 O(R) ~ O(R²) (extra cycles 포함)

---

### Greedy Spanning Tree

**한 줄:** 모든 방이 최소 한 번은 연결되도록 spanning tree를 만듭니다.

`build_spanning_tree()`는 connected / unconnected 집합을 두고, 맨해튼 거리가 가장 가까운 방 쌍을 골라 간선을 추가합니다. BFS로 “연결됐는지”만 검사할 수도 있지만, 우리는 **생성 단계에서 연결을 보장**해야 해서 spanning tree가 맞습니다. `extra_cycles=2`로 랜덤 간선을 더해 루프를 만들어 탐험 루트를 다양하게 합니다.

- **복잡도:** O(R²), R ≤ 12

---

### 맵 생성 — 통로 생성

**한 줄:** 방과 방 사이 통로를 A*로 찾고, 다른 방 내부는 `protected`로 막습니다.

우리는 각 방 **외곽 바닥 타일(perimeter)** 을 연결점으로 잡고, `protected`에 타 방 템플릿 영역을 넣은 뒤 A*로 경로를 찾습니다. 맨해튼 휴리스틱, 4방향, `heapq` min-heap입니다. 경로 타일을 `floor_tiles`에 추가해 복도를 완성합니다.

- **선택 이유:** L자 직선 복도의 경우, 다른 방을 막힌 벽으로 보고 우회하지 않아, 방을 뚫고 통로가 생성되는 문제가 발생함.
- **복잡도:** O(WH log WH) worst, WH = 53×30

---

## Undo System

### 행동 되돌리기 (Undo)

**한 줄:** `undo_stack` / `redo_stack`으로 턴 단위 Undo/Redo를 합니다.

Undo는 **가장 최근 행동부터** 되돌려야 하므로 FIFO인 Queue는 맞지 않습니다. 전체 맵 스냅샷은 구현은 쉬우나 턴이 쌓일수록 메모리가 O(맵×턴)으로 커집니다. 우리는 Action에 변경분(delta)만 저장해서 O(턴당 액션 수)로 유지합니다. `EndTurnAction(turn_id)` 마커까지 pop하면 한 턴 전체가 복원됩니다.

- **복잡도:** push/pop O(1), undo 1턴 O(k)

---

### Action 기록

**한 줄:** 추상 `Action(ABC)` 아래 원자적 커맨드가 `execute()` / `undo()` 쌍을 구현합니다.

- **선택 이유:** 이동·전투·루팅·소비 등 행동을 **원자적 Action 객체**로 캡슐화하고, 추상 클래스가 `execute()` / `undo()` 계약을 강제합니다. `UndoManager`는 구체 타입을 몰라도 `action.undo()`만 호출하므로 undo 흐름이 통일됩니다.

`Action(ABC)`(`base_action.py`)는 `turn_id`와 추상 메서드 `execute()`, `undo()`만 정의합니다. 구체 클래스(`MoveAction`, `CombatAction`, `LootAction`, `ConsumeAction`)는 frozen dataclass로 **한 번의 게임 변경**만 담고, execute 시 `_previous_pos`, `_defender_prev_hp` 같은 **delta**만 저장합니다. undo는 그 delta로 역연산합니다. 턴 경계는 `EndTurnAction` 마커도 같은 ABC를 상속해 스택에 쌓입니다.

Memento(전체 스냅샷) 대신 delta만 Action에 두면 메모리는 O(턴당 액션 수)로 유지됩니다. `game_manager.execute_action()` → `undo_manager.record(action)` → `undo_turn()`에서 pop 후 `action.undo()` — undo 로직이 각 Action 클래스 안에 응집됩니다.

- **예:** `MoveAction` — execute: 좌표 이동 + `_previous_pos` 저장 / undo: 이전 좌표 복원
- **예:** `LootAction` — execute: 바닥→인벤 / undo: 인벤→바닥

---

## Turn Management

### Batch Action List (적 턴 일괄 처리)

**한 줄:** 플레이어 1액션 후, 현재 층 적 전원의 행동을 **먼저 모두 확정**하고 리스트로 **순차 실행**합니다.

턴 흐름은 `플레이어 행동 → run_enemy_turns() → finalize_turn()`입니다. 플레이어 이동·공격·아이템 사용 등이 성공하면 적 턴이 시작되고, 턴이 끝날 때 `EndTurnAction` 마커가 쌓여 Undo 경계가 됩니다.

**1단계 — 수집 (`TurnResolver.collect_actions`)**  
현재 층 살아 있는 적마다 `EntityTurnPlan`을 만듭니다. 각 적은 `propose()`로 행동 후보를 제안합니다.
- 인접 → `CombatAction` (근접 공격)
- 시야 6 이내 → A* 경로의 다음 칸 `MoveAction`
- 시야 밖 → 랜덤 방향 `MoveAction` (wander)

`ActionValidator`로 검증합니다. 벽·점유·맵 밖이면 `fallback()`으로 방향을 바꿔 최대 8회 재시도합니다. 통과한 Action만 `list[Action]`에 추가합니다. **이 단계에서는 아직 보드 상태를 바꾸지 않습니다.**

**2단계 — 실행 (`run_enemy_turns`)**  
확정된 리스트를 순서대로 `execute()` + `undo_manager.record()`합니다. 전투 Action은 HP 변화 로그를 남깁니다.

FIFO per-entity Queue는 액터가 번갈아 한 번씩 행동하는 구조인데, 이 게임은 **플레이어가 항상 먼저, 그다음 적 전원**이 UX에 맞습니다. 계획(collect)과 실행(execute)을 분리해, 한 턴의 적 행동 전체가 Undo·로그 단위로 묶입니다.

- **복잡도:** 적 턴 O(E × F), E = 적 수, F ≤ 8 (fallback 상한)

---

### Turn Counter

**한 줄:** `turn_id`로 턴 경계와 RNG를 고정합니다.

`finalize_turn()`마다 `turn_id`가 증가하고, `prepare_turn_rng()`가 `random.seed(base_seed + turn_id)`를 호출합니다. Undo 후 같은 턴을 redo하면 동일한 랜덤 결과가 나와야 해서 turn_id가 RNG와 Undo 마커 경계를 동시에 잡습니다. 속도 차등이 없어 Priority Queue는 과잉입니다.

- **복잡도:** O(1)

---

## Item Inventory

### List

**한 줄:** 10칸 고정 슬롯 `list[Item | None]`, 키 `1`~`0`과 1:1.

Dict만 쓰면 “1번 슬롯에 뭐가 있지?”를 UI 키와 연결하기 어렵습니다. List index 0~9가 곧 슬롯 1~10입니다. n=10이라 BST의 O(log n) 이점은 없고 구현만 복잡해집니다. 빈 슬롯 찾기는 최대 10번 선형 탐색입니다.

- **복잡도:** 슬롯 연산 O(10)

---

### Hash Map

**한 줄:** `defaultdict[str, int]`로 아이템 이름별 개수를 O(1) 조회합니다.

List만 있으면 “하트 몇 개?”를 매번 슬롯 전체를 돌아야 합니다. Dict는 이름 → 개수를 바로 보여줄 수 있습니다. 화살은 인벤 슬롯이 아니라 `Entity.arrows` 정수로 따로 둡니다.

- **복잡도:** count 조회 O(1) avg

---

## Enemy AI

### A*

**한 줄:** 시야 6 이내이면 A*로 플레이어까지 최단 경로, 한 칸 이동.

가중치 없는 2D 맵에서 BFS도 최단 경로를 주지만, A*는 맨해튼 휴리스틱으로 탐색 노드를 줄일 수 있습니다. DFS는 최단 보장이 없고 벽에 갇히기 쉽습니다. blocker로 벽·바닥 아이템·다른 적을 두고, 경로 없으면 fallback wander합니다.

- **복잡도:** O(E log V), V ≤ WH

---

### min-heap

**한 줄:** A* open set을 `heapq` min-heap으로 관리합니다.

f = g + h가 작은 노드부터 꺼내야 하므로 우선순위 큐가 필요합니다. 매번 리스트를 정렬하면 push마다 O(n)이라, heap이 O(log n) push/pop로 유리합니다. `pathfinding.py`와 `corridor_carver.py` 둘 다 heapq를 씁니다.

---

## Leaderboard

### Array (list)

**한 줄:** 최대 10개 `ScoreEntry`를 list로 보관, JSON 영속화.

Linked List는 인덱스 접근이 O(n)이고 Top-10 고정 규모에서 이점이 없습니다. 게임 종료 시 `leaderboard.json`에 저장하고 메인 메뉴에서 표시합니다.

- **공간:** O(10)

---

### Insertion Sort

**한 줄:** 새 기록 삽입 후 insertion sort로 score 내림차순 정렬.

n ≤ 10이면 O(n²)도 체감상 즉시입니다. Tim Sort O(n log n)은 이 규모에서 이점이 없고, Min-Heap top-K는 n이 커질 때 유리하지만 capacity 10에 과잉입니다. 정렬 후 capacity 초과분은 잘라 Top-10만 유지합니다.

- **복잡도:** O(n²), n ≤ 10

---

## 슬라이드 ↔ 대본 매핑

| 슬라이드 제목 | 이 대본 섹션 |
|---------------|--------------|
| Dungeon Map · 타일 이동 · 충돌 검사 | Dungeon Map > 이동 및 충돌 검사 — set / 2D array |
| Dungeon Map · Graph | Dungeon Map > Graph |
| Dungeon Map · Greedy Spanning Tree | Dungeon Map > Greedy Spanning Tree |
| Dungeon Map · 맵 생성 — 통로 캐빙 | Dungeon Map > 맵 생성 — 통로 생성 |
| Undo System · 행동 되돌리기 | Undo System > 행동 되돌리기 (Undo) |
| Undo System · Action 기록 | Undo System > Action 기록 |
| Turn Management · Batch Action List | Turn Management > Batch Action List |
| Turn Management · Turn Counter | Turn Management > Turn Counter |
| Item Inventory · List | Item Inventory > List |
| Item Inventory · Hash Map | Item Inventory > Hash Map |
| Enemy AI · A* | Enemy AI > A* |
| Enemy AI · min-heap | Enemy AI > min-heap |
| Leaderboard · Array | Leaderboard > Array |
| Leaderboard · Insertion Sort | Leaderboard > Insertion Sort |

**총 14장** (Core Feature × DS&A)
