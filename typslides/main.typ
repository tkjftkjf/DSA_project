#import "@preview/typslides:1.3.3": *

// 본문 제목 — TOC에는 안 뜸 (outlined 미사용 heading)
#let slide-heading(body) = block(below: 0.55em)[
  #text(size: 22pt, weight: "bold", fill: rgb("3059AB"))[#body]
]

// DSA 비교 블록 색상
#let chosen-fill = rgb("E6F4EA")
#let chosen-stroke = rgb("2E7D32")
#let alt-fill = rgb("FDECEC")
#let alt-stroke = rgb("C62828")

#let dsa-block(kind, name, pros, cons, desc) = {
  let (fill, stroke) = if kind == "chosen" {
    (chosen-fill, chosen-stroke)
  } else {
    (alt-fill, alt-stroke)
  }
  block(
    fill: fill,
    stroke: 1.5pt + stroke,
    radius: 8pt,
    inset: 10pt,
    width: 100%,
  )[
    #text(size: 15pt, weight: "bold", fill: stroke)[#name]
    #v(0.35em)
    #text(size: 13pt)[
      *장점* #pros \
      *단점* #cons \
      #desc
    ]
  ]
}

// Core Feature × DS&A 1페이지 — 초록(사용) vs 붉은(대안) 비교 레이아웃
#let dsa-slide(
  feature: "",
  heading: "",
  chosen-name: "",
  chosen-pros: "",
  chosen-cons: "",
  chosen-desc: "",
  alt-name: "",
  alt-pros: "",
  alt-cons: "",
  alt-desc: "",
  why: "",
  code: "",
) = {
  slide[
    #slide-heading[#heading]
    #text(size: 13pt, fill: gray)[Core Feature · #feature]

    #v(0.45em)
    #cols(columns: (1fr, 1fr), gutter: 1em)[
      #dsa-block("chosen", chosen-name, chosen-pros, chosen-cons, chosen-desc)
    ][
      #dsa-block("alt", alt-name, alt-pros, alt-cons, alt-desc)
    ]

    #v(0.5em)
    #block(
      fill: rgb("EEF3FB"),
      stroke: 0.5pt + rgb("3059AB"),
      radius: 6pt,
      inset: 10pt,
      width: 100%,
    )[
      #text(size: 14pt, weight: "bold", fill: rgb("3059AB"))[선택 이유] \
      #text(size: 13pt)[#why]
    ]

    #v(0.4em)
    #text(size: 13pt)[
      *코드 위치* #raw(code, lang: "text")
    ]
  ]
}

#show: typslides.with(
  ratio: "16-9",
  theme: "bluey",
  font: "Sarasa Gothic K",
  font-size: 18pt,
  link-style: "color",
  show-progress: true,
)

// ── Title ──────────────────────────────────────────────────────────────────
#front-slide(
  title: [Python DS&A Team Project],
  subtitle: [턴 기반 TUI 로그라이크 — _Dungeon Crawler_],
  authors: "Team 25 · Jinwoo Park",
  info: [AI2000 · Data Structures and Algorithms],
)

#table-of-contents()

// ── Project overview ───────────────────────────────────────────────────────
#title-slide[프로젝트 개요]

#slide[
  #slide-heading[개요]
  #cols(columns: (1fr, 1fr), gutter: 1.5em)[
    *장르:* 턴 기반 TUI 로그라이크 (룸 템플릿 던전 크롤러)
  ][
    *기술 스택*
    - Python 3.9+
    - rich (TUI)
    - stdlib + rich only
  ]
]

#slide[
  #slide-heading[6 Core Features]
  #cols(columns: (1fr, 1fr), gutter: 1.2em)[
    #framed[
      📡 *Dungeon Map* \
      2D · Graph · A\*
    ]
    #v(0.35em)
    #framed[
      📚 *Undo System* \
      Stack · Command Pattern
    ]
    #v(0.35em)
    #framed[
      🎯 *Turn Management* \
      Batch resolve · Turn counter
    ]
  ][
    #framed[
      🌳 *Item Inventory* \
      List · Hash Map
    ]
    #v(0.35em)
    #framed[
      🔺 *Enemy AI* \
      A\* · min-heap
    ]
    #v(0.35em)
    #framed[
      📊 *Leaderboard* \
      Array · Insertion Sort
    ]
  ]
]

#slide[
  #slide-heading[게임플레이]
  #cols(columns: (1fr, 1fr), gutter: 1.5em)[
    *이동·전투*
    - `w/a/s/d` — 한 칸 이동 (적 칸 → 근접 공격)
    - `c` + 방향 — 근접 공격 모드
    - `v` + 방향 — 원거리 발사 (화살 3개 시작)
    - `1`~`0` — 인벤토리 슬롯 아이템 사용

    *기타*
    - `i` — 인벤토리 표시 토글
    - `u` / `r` — Undo / Redo (턴 단위)
    - `q` / `esc` — 메인 메뉴 포기
  ][
    *성장·승패*
    - EXP → 레벨업 (HP/ATK/DEF 증가, 풀회복)
    - 이동 시 바닥 아이템 자동 루팅
    - 계단 타일 위 → 자동 하강
    - 3층 계단 = #stress[승리]
  ]
]

// ── Feature 1: Dungeon Map ─────────────────────────────────────────────────
#title-slide[Dungeon Map]

#dsa-slide(
  feature: "Dungeon Map",
  heading: "타일 이동 · 충돌 검사",
  chosen-name: "2D Map (`set`)",
  chosen-pros: [타일 조회 O(1), 이동·렌더 좌표 1:1],
  chosen-cons: [좌표 범위 검사 필요],
  chosen-desc: [`floor_tiles` / `_blocked` set으로 53×30 월드 상태 관리],
  alt-name: "2D 배열",
  alt-pros: [인덱스 접근 O(1), 구현 직관적],
  alt-cons: [전체 1,590칸 항상 할당],
  alt-desc: [바닥이 없는 빈 공간까지 메모리 점유],
  why: [실제 바닥 타일만 저장하는 sparse 구조가 메모리·로직 모두 효율적],
  code: "models/dungeon.py — Dungeon.is_walkable()",
)

#dsa-slide(
  feature: "Dungeon Map",
  heading: "방 연결 구조",
  chosen-name: "Graph (간선 set)",
  chosen-pros: [방 R≤12에 경량, 연결 관계 명시적],
  chosen-cons: [노드 수 증가 시 edge 관리 필요],
  chosen-desc: [`room_nodes` + `edges`로 복도 캐빙 대상 결정],
  alt-name: "인접 행렬",
  alt-pros: [두 방 연결 O(1) 조회],
  alt-cons: [12×12도 대부분 0, 메모리 낭비],
  alt-desc: [희소 그래프에 과한 표현],
  why: [층당 12방 규모에서 간선 set이 단순하고 충분],
  code: "generation/room_graph.py — build_room_graph()",
)

#dsa-slide(
  feature: "Dungeon Map",
  heading: "맵 생성 — 방 연결",
  chosen-name: "Greedy Spanning Tree",
  chosen-pros: [모든 방 최소 연결 보장, R≤12에 단순],
  chosen-cons: [최적 트리만으로는 루프 없음 → extra edge 보완],
  chosen-desc: [맨해튼 최소 쌍 연결 + `extra_cycles=2` 순환 간선],
  alt-name: "BFS / DFS 연결",
  alt-pros: [연결성 검사·탐색에 적합],
  alt-cons: [생성 시 최소 연결 보장 로직이 분리됨],
  alt-desc: [연결 확인용으로는 OK, 생성 파이프라인엔 ST가 직접적],
  why: [생성 단계에서 한 번에 전 방 연결 + 루프 다양화],
  code: "generation/room_graph.py — build_spanning_tree()",
)

#dsa-slide(
  feature: "Dungeon Map",
  heading: "맵 생성 — 통로 캐빙",
  chosen-name: "A\* (맨해튼)",
  chosen-pros: [`protected`로 타 방 관통 방지, 최단 경로],
  chosen-cons: [WH log WH — 맵 크기에 비례],
  chosen-desc: [방 외곽 타일 연결 → A\* → `floor_tiles`에 복도 추가],
  alt-name: "L자 직선 복도",
  alt-pros: [구현 매우 단순],
  alt-cons: [중간에 다른 방 벽·내부 관통],
  alt-desc: [앵커만 잇는 직선/꺾은선은 충돌 빈번],
  why: [템플릿 기반 배치에서 방 침범 없이 통로를 보장해야 함],
  code: "generation/corridor_carver.py — find_corridor_path()",
)

// ── Feature 2: Undo System ─────────────────────────────────────────────────
#title-slide[Undo System]

#dsa-slide(
  feature: "Undo System",
  heading: "행동 되돌리기",
  chosen-name: "Two-Stack (LIFO)",
  chosen-pros: [push/pop O(1), Undo 순서 자연스러움],
  chosen-cons: [히스토리 길이에 비례 메모리],
  chosen-desc: [`undo_stack` / `redo_stack`, `EndTurnAction`으로 턴 경계],
  alt-name: "Queue (FIFO)",
  alt-pros: [순서 보존, 스트림 처리에 적합],
  alt-cons: [Undo는 LIFO인데 FIFO는 순서 역전],
  alt-desc: [되돌리기 UX와 접근 패턴 불일치],
  why: [마지막 행동부터 되돌리는 게임 규칙과 Stack이 정확히 맞음],
  code: "engine/undo_manager.py — UndoManager.undo_turn()",
)

#dsa-slide(
  feature: "Undo System",
  heading: "Action 기록",
  chosen-name: "Command Pattern",
  chosen-pros: [execute/undo 응집, delta만 저장],
  chosen-cons: [Action 클래스 수 증가],
  chosen-desc: [Move · Combat · Loot · Consume — 각각 역연산 내장],
  alt-name: "전체 스냅샷 (Memento)",
  alt-pros: [구현 단순, 복원 한 번에],
  alt-cons: [O(맵×턴) 메모리],
  alt-desc: [맵·엔티티 전체 복사 부담],
  why: [변경분만 Action에 담아 메모리 절약 + 로직 분산 방지],
  code: "actions/move_action.py · combat_action.py · loot_action.py",
)

// ── Feature 3: Turn Management ─────────────────────────────────────────────
#title-slide[Turn Management]

#dsa-slide(
  feature: "Turn Management",
  heading: "적 턴 일괄 처리",
  chosen-name: "Batch Action List",
  chosen-pros: [플레이어→적 단계 명확, 로그·Undo 경계 깔끔],
  chosen-cons: [공정 순환(라운드 로빈) 미지원],
  chosen-desc: [propose → validate → fallback(≤8) → 순차 execute],
  alt-name: "FIFO per-entity Queue",
  alt-pros: [다수 액터 공정 순환],
  alt-cons: [플레이어 항상 선행 UX와 충돌],
  alt-desc: [TUI 턴제에서 매 턴 플레이어 먼저가 자연스러움],
  why: [본 게임은 플레이어 1액션 후 적 전원 — 배치 모델이 UX에 맞음],
  code: "engine/turn_resolver.py — TurnResolver.collect_actions()",
)

#dsa-slide(
  feature: "Turn Management",
  heading: "턴 경계 · RNG 동기화",
  chosen-name: "Turn Counter",
  chosen-pros: [turn_id O(1), Undo 마커·RNG 시드 통합],
  chosen-cons: [속도(AGI) 차등 미표현],
  chosen-desc: [`random.seed(base_seed + turn_id)` per turn],
  alt-name: "Priority Queue",
  alt-pros: [속도 빠른 액터 우선 행동],
  alt-cons: [현재 스탯 모델에 속도 없음, 과잉],
  alt-desc: [턴 순서가 고정된 TUI에 불필요한 복잡도],
  why: [턴 ID 하나로 RNG 재현 + `EndTurnAction` 경계를 동시에 해결],
  code: "engine/turn_manager.py — TurnManager.prepare_turn_rng()",
)

// ── Feature 4: Item Inventory ──────────────────────────────────────────────
#title-slide[Item Inventory]

#dsa-slide(
  feature: "Item Inventory",
  heading: "슬롯 UI 매핑",
  chosen-name: "List (10 slots)",
  chosen-pros: [키 `1`~`0` ↔ index 1:1, 직관적],
  chosen-cons: [빈 슬롯 탐색 O(10)],
  chosen-desc: [`list[Item | None]` 고정 10칸],
  alt-name: "Dict only",
  alt-pros: [이름→아이템 O(1)],
  alt-cons: [슬롯 번호·순서 UI 매핑 어려움],
  alt-desc: [Status `1:❤️ 2:-` 표시가 불편],
  why: [인벤토리 UI가 슬롯 번호 기반이라 List가 직접 대응],
  code: "models/inventory.py — Inventory.slots",
)

#dsa-slide(
  feature: "Item Inventory",
  heading: "아이템 개수 집계",
  chosen-name: "Hash Map",
  chosen-pros: [이름별 개수 O(1), 표시·검색 빠름],
  chosen-cons: [슬롯 순서 정보 없음 → List와 병행],
  chosen-desc: [`defaultdict[str, int]` counts],
  alt-name: "List only",
  alt-pros: [구조 단일, 추가 DS 불필요],
  alt-cons: [개수 집계마다 O(n) 순회],
  alt-desc: [10칸이어도 매 조회 선형 탐색],
  why: [슬롯(List) + 개수(Dict) 역할 분리가 각각 O(1) 강점 활용],
  code: "models/inventory.py — Inventory.counts",
)

// ── Feature 5: Enemy AI ─────────────────────────────────────────────────────
#title-slide[Enemy AI]

#dsa-slide(
  feature: "Enemy AI",
  heading: "적 추적 경로",
  chosen-name: "A\* (맨해튼)",
  chosen-pros: [최단 경로 보장, 휴리스틱으로 탐색 축소],
  chosen-cons: [blocker·fallback 처리 필요],
  chosen-desc: [시야 6 이내 플레이어 추적, 4방향 2D],
  alt-name: "BFS",
  alt-pros: [비가중 2D에서 동일 최단 경로],
  alt-cons: [목표 방향 무시, 탐색 노드 더 많을 수 있음],
  alt-desc: [휴리스틱 없이 전방위 확장],
  why: [가중치 없는 맵에서 A\*+맨해튼은 BFS와 동급이면서 탐색 범위 축소],
  code: "utils/pathfinding.py — find_path()",
)

#dsa-slide(
  feature: "Enemy AI",
  heading: "경로 탐색 우선순위",
  chosen-name: "min-heap (`heapq`)",
  chosen-pros: [open set push/pop O(log n)],
  chosen-cons: [heap 자료구조 이해 필요],
  chosen-desc: [A\* f=g+h 최소 노드부터 확장],
  alt-name: "정렬 리스트",
  alt-pros: [구현 단순],
  alt-cons: [삽입마다 O(n) 정렬/삽입],
  alt-desc: [맵이 클수록 open set 비용 증가],
  why: [우선순위 큐가 A\*의 핵심 — stdlib heapq로 충분],
  code: "utils/pathfinding.py — _astar()",
)

// ── Feature 6: Leaderboard ─────────────────────────────────────────────────
#title-slide[Leaderboard]

#dsa-slide(
  feature: "Leaderboard",
  heading: "기록 저장",
  chosen-name: "Array (list)",
  chosen-pros: [인덱스 O(1), capacity 10 고정],
  chosen-cons: [삽입 시 정렬 별도 필요],
  chosen-desc: [`ScoreEntry` list → `leaderboard.json`],
  alt-name: "Linked List",
  alt-pros: [삽입 O(1) (위치 알 때)],
  alt-cons: [i번째 접근 O(n), Top-10에 이점 없음],
  alt-desc: [10개 고정 순위표에 과한 구조],
  why: [소규모 고정 배열이 저장·표시 모두 단순],
  code: "utils/leaderboard.py — Leaderboard",
)

#dsa-slide(
  feature: "Leaderboard",
  heading: "점수 순위 정렬",
  chosen-name: "Insertion Sort",
  chosen-pros: [n≤10에서 충분·단순, Top-K 자연스러움],
  chosen-cons: [일반적으로 O(n²)],
  chosen-desc: [삽입 시 score 내림차순, 초과분 truncate],
  alt-name: "Min-Heap top-K",
  alt-pros: [대규모 n에서 O(n log k)],
  alt-cons: [n=10이면 오버엔지니어링],
  alt-desc: [구현·테스트 복잡도만 증가],
  why: [기록 10개 제한 — Insertion Sort로 코드·성능 모두 충분],
  code: "utils/leaderboard.py — _insertion_sort_desc()",
)

// ── Summary ────────────────────────────────────────────────────────────────
#title-slide[정리]

#slide[
  #slide-heading[DS/알고리즘 한눈에 보기]
  #table(
    columns: (1.1fr, 2fr),
    inset: 8pt,
    stroke: 0.5pt + gray,
    [*Core Feature*], [*DS&A (각 1슬라이드)*],
    [Dungeon Map], [2D Map · Graph · Spanning Tree · A\*],
    [Undo System], [Two-Stack · Command Pattern],
    [Turn Management], [Batch List · Turn Counter],
    [Item Inventory], [List · Hash Map],
    [Enemy AI], [A\* · min-heap],
    [Leaderboard], [Array · Insertion Sort],
  )
]

#slide[
  #slide-heading[실행 방법]
  ```bash
  docker build -f dungeon_crawler/Dockerfile -t dungeon-crawler .
  docker run -it --rm dungeon-crawler
  ```
]

#focus-slide[
  #text(size: 32pt)[Q&A]

  #v(0.8em)
  #text(size: 20pt)[감사합니다]
]
