# **📜 TUI 로그라이크 게임 기술 명세서 (Tech Spec) \- DS\&A Project 최상위 상세본 v2.0**

## **1\. 프로젝트 개요 및 환경**

* **장르:** 턴 기반 TUI 로그라이크 (Enter the Gungeon 스타일 룸 기반 맵)  
* **목적:** 자료구조 및 알고리즘(DS\&A) 과제 제출용 (6 Core Features 완벽 대응)  
* **개발 언어:** Python 3.9 이상 (정적 타입 힌팅 typing 적극 활용)  
* **UI 프레임워크:** rich 라이브러리를 활용한 모던 터미널 분할 레이아웃(좌측 맵 / 우측 정보창).  
* **실행 환경:** Docker 컨테이너 (-it 플래그를 통한 TTY 키보드 제어 환경)

## **2\. 6대 핵심 기능 및 자료구조 설계 (DS\&A 평가 기준)**

### **2.1. Dungeon Map (2D Grid & Graph)**

* **개념:** 방(Room)을 Node로, 통로(Corridor)를 Edge로 취급.  
* **알고리즘:**  
  * 1x1, 1x2, 'ㄴ'자 형태의 프리셋 방을 2D Grid에 겹치지 않게 무작위 배치.  
  * Spanning Tree 알고리즘을 응용해 모든 방을 연결하는 그래프 생성.  
  * 유저의 탐험 다양성을 위해 일부 순환(Cycle) 간선을 추가하거나 남김.  
  * 템플릿 방의 내부는 고정하되, 문(Door)은 통로 연결 방향에 따라 벽면 중 빈 공간에 동적 생성 (벽과 내부 구조물이 닿지 않게 설계).

### **2.2. Undo System (Stack \- Command Pattern) & 난수 동기화**

* **개념:** LIFO(Last-In-First-Out) 접근 방식의 하이브리드 Two-Stack 시스템 (UndoStack, RedoStack).  
* **동작 원리 (원자적 액션 & Turn ID):**  
  * 모든 행동은 쪼개진 원자적(Atomic) 단위로 생성되며 각각 execute(), undo()를 가짐.  
  * 액션 객체는 생성 시 현재 턴을 의미하는 turn\_id를 가짐. 턴 종료 시 EndTurnAction(turn\_id)라는 빈 마커를 스택에 삽입.  
  * Undo 호출 시, 최상단 EndTurnAction을 Pop하여 ID를 확인하고, 해당 ID와 일치하는 모든 액션을 Pop하며 역으로 undo()를 실행 후 RedoStack으로 이동.  
  * Undo 이후 플레이어가 Redo가 아닌 새로운 조작을 하면 RedoStack 초기화.  
* **난수(RNG) 동기화 전략 (매우 중요):**  
  * Undo/Redo 시 몬스터의 랜덤 이동이나 난수 판정이 어긋나는 것을 방지하기 위해 턴마다 시드를 고정함.  
  * 액션 실행 직전 random.seed(base\_seed \+ turn\_id)를 호출하여, 특정 턴으로 복귀 시 항상 동일한 난수 결과를 보장.

#### **📌 요구되는 Atomic Action 클래스 명세**

| Action 클래스 | execute() 동작 | undo() 동작 (역연산) | 필수 저장 데이터 (상태 기억) |
| :---- | :---- | :---- | :---- |
| **MoveAction** | 엔티티의 좌표를 dx, dy 만큼 이동. | 엔티티의 좌표를 \-dx, \-dy 만큼 이동. | 대상 엔티티, 이동 방향 |
| **CombatAction** | 데미지 계산, 사망 시 맵/큐에서 제거 및 EXP 부여. | HP 원복, 사망 시 부활(맵/큐 복구), 획득 EXP 차감. | 가해자, 피해자, 입힌 데미지, 사망 여부 |
| **LootAction** | 맵에서 아이템 제거, 인벤토리에 추가. | 인벤토리에서 제거, 원래 맵 좌표에 복구. | 대상 엔티티, 아이템 객체, 원래 좌표 |
| **ConsumeAction** | 인벤토리에서 아이템 소모, HP 회복. | 소모된 아이템 인벤토리 복구, 회복된 HP 차감. | 대상 엔티티, 아이템 종류, 회복량 |
| **EndTurnAction** | (로직 없음) 스택의 턴 구분선 역할. | (로직 없음) Pop 시 이 마커가 나올 때까지 반복. | 턴 ID (turn\_id) |

### **2.3. Turn Management (Queue)**

* **개념:** FIFO Queue 기반의 턴 스케줄러.  
* **로직:**  
  * 큐에는 맵에 존재하는 모든 엔티티(Player, Enemies)가 등록됨.  
  * 큐를 순회하며 턴을 부여. 딜레이 스킬의 경우, DelayedAction 객체 내부의 카운트다운을 사용하여 단순한 스케줄링 구현.

### **2.4. Item Inventory (List & Hash Map)**

* **자료구조:** UI 표시용 10칸 슬롯 관리는 List 활용, 아이템별 누적 개수 처리는 collections.defaultdict (Hash Map) 사용.  
* **아이템 종류 (이모지 기반):**  
  * 🏹 화살 (Arrow): 원거리 공격 탄약. (플레이어는 루팅, 적은 랜덤/무한 보유)  
  * ❤️ \~ 💜 하트 (회복 아이템): 색상별로 HP 회복량이 다름 (3, 5, 10, 15, 20, 30).  
* **로직:** \* 플레이어가 아이템 좌표로 이동하면 LootAction 발생.  
  * 적(Enemy)의 A\* 길찾기 알고리즘에서는 아이템을 벽과 동일한 장애물로 취급 (적은 아이템을 밟거나 먹지 못함).

### **2.5. Enemy AI (A\* Pathfinding Algorithm) & 우회 로직**

* **기본 알고리즘:**  
  * 시야(거리 반경) 내에 플레이어가 없으면 랜덤 배회.  
  * 포착 시 A\* 알고리즘을 사용해 최단 경로 계산. (벽과 아이템을 장애물로 판단)  
* *A 길막힘(Deadlock) 우회 로직:*\*  
  * 도착 예정 타일에 다른 몬스터가 있어 이동이 불가능할 경우, **현재 맵의 다른 몬스터들을 일시적인 벽(Wall)으로 간주**하고 A\* 탐색을 재시도(우회 경로 탐색)함.  
  * 우회 경로조차 완전히 막혀 있다면 (Fallback), 해당 턴의 MoveAction을 스킵(대기)하여 데드락을 방지함.

### **2.6. Leaderboard (Sort / Array)**

* **개념:** 누적된 게임의 결과(최종 점수/도달 레벨 등)를 관리.  
* **알고리즘:** 데이터 삽입 시 삽입 정렬(Insertion Sort)을 수행하여 상위 N개의 랭킹 유지.
* **메인화면:** 리더보드 화면은 메인화면과 같은 역할 수행. 아무키나 누르면 게임이 시작. 화면 크기를 조정할 수 있는 단계.

## **3\. 게임플레이 및 엔티티 상세 명세**

### **3.1. Entity 스탯 및 성장**

* **공통 속성:** HP, DEF(방어력), ATK(공격력), Level.  
* **전용 속성:** EXP(경험치 \- 플레이어 전용).  
* **데미지 계산 공식:** \* 최종 데미지 \= max(1, ATK \- DEF)  
  * 방어력이 아무리 높아도 최소 1의 피해는 보장됨.  
* **레벨업 로직:** 몬스터 처치 시 EXP 획득. 일정 경험치 도달 시 레벨 증가. 최대 HP, DEF, ATK 상승 및 현재 HP 완전 회복.

### **3.2. 조작 및 State Machine 제어**

* **기본 조작:** W, A, S, D (이동), I (인벤토리 토글).  
* **아이템 사용:** 1 \~ 0 숫자 키 눌러 인벤토리 슬롯 아이템 즉시 사용 (ConsumeAction 발생).  
* **특수 조작:** U (Undo), R (Redo).  
* **전투 조작 체계:**  
  * C (근접 공격 모드 전환) / V (원거리 공격 모드 전환, 화살 소모 대기).  
  * 시스템 메시지: "\[WASD를 통해 공격 방향을 정하세요\]" 출력 후 대기 상태 진입.  
  * WASD 입력 시 해당 방향으로 CombatAction 발생. 타깃이 없거나 탄약 부족 시 턴 소모 없이 재입력 요구.
  * **v3 보완:** 원거리(V) 공격의 발사 궤적·턴 소모 규칙은 **7.4 원거리 공격: 발사 궤적** 절을 따름 (적이 없어도 발사 가능, 벽/아이템 충돌 시 miss 처리).
* **게임 종료:**
  * esc시 메인 화면으로 이동 

## **4\. 로깅 및 UI 렌더링 아키텍처 (Dynamic Viewport)**

* **Layout 구조:** 화면을 좌우 분할 (rich.layout.Layout 활용).  
* **좌측 (Map & Dynamic Viewport):**  
  * 던전 맵 전체 크기는 터미널 화면보다 클 수 있음.  
  * rich.console.Console().size를 호출하여 실행 시점 및 창 크기 조절 시의 **동적 터미널 크기를 인식**.  
  * 플레이어의 좌표 (x, y)를 중앙에 두고 터미널 좌측 영역 크기에 맞춰 2D Grid 배열을 잘라내어(Slicing) 렌더링하는 **카메라 스크롤 뷰포트** 시스템 적용.  
  * 이모지 활용 (⬛: 벽, 🟫: 바닥, 👾/👹: 몬스터, 🧙‍♂️: 플레이어 등).  
* **우측 (Status & Log):**  
  * 상단: 턴 수, HP/ATK/DEF/화살 개수/인벤토리 패널.  
  * 하단: 로그 패널 (Append-Only).  
* **로그 렌더링 규칙:**  
  * 원자적 연산 종료 후 최종 결과를 로그에 append.  
  * Undo 시 기존 로그를 삭제하지 않고 "\[System\] 턴 N의 행동을 되돌렸습니다." 추가 기록.

## **5\. 📂 프로젝트 디렉토리 구조 (Directory Architecture)**

dungeon\_crawler/  
├── Dockerfile                  \# Python 3.9+ 기반 환경 구축 및 \`rich\` 설치  
├── requirements.txt            \# rich, pynput(키보드 캡처)  
├── main.py                     \# 게임 실행 엔트리 포인트 (Game Loop, Layout)  
│  
├── engine/                     \# 게임 핵심 제어 시스템  
│   ├── \_\_init\_\_.py  
│   ├── game\_manager.py         \# 전체 게임 상태 관리  
│   ├── turn\_manager.py         \# FIFO 큐 및 엔티티 행동 턴 스케줄링 (RNG Seed 제어 포함)  
│   ├── undo\_manager.py         \# Two-Stack 상태 복원 로직  
│   └── input\_handler.py        \# OS 독립적 키보드 입력 제어  
│  
├── models/                     \# 도메인 모델  
│   ├── \_\_init\_\_.py  
│   ├── dungeon.py              \# Grid 2D 배열, 그래프 노드/간선 관리  
│   ├── entity.py               \# Entity (추상 클래스), Player, Enemy  
│   ├── inventory.py            \# Hash Map 아이템 누적 및 List 슬롯 관리  
│   └── item.py                 \# 무기 및 소비 아이템 클래스  
│  
├── actions/                    \# 커맨드 패턴 기반 액션 (execute, undo)  
│   ├── \_\_init\_\_.py  
│   ├── base\_action.py          \# 추상 클래스  
│   ├── move\_action.py          \# 이동 및 역이동  
│   ├── combat\_action.py        \# 데미지, 사망 역연산  
│   ├── loot\_action.py          \# 아이템 획득 및 드랍 역연산  
│   ├── consume\_action.py       \# 아이템 사용 및 스탯 복구 역연산  
│   └── marker\_action.py        \# EndTurnAction 등 논리 마커  
│  
├── utils/                      \# 유틸리티  
│   ├── \_\_init\_\_.py  
│   ├── pathfinding.py          \# A\* 길찾기 (장애물 동적 우회 기능 포함)  
│   ├── decorators.py           \# @validate\_action 행동 유효성 검사  
│   └── leaderboard.py          \# 삽입 정렬 기반 랭킹  
│  
└── ui/                         \# TUI 렌더링  
    ├── \_\_init\_\_.py  
    └── renderer.py             \# Viewport 카메라 시스템 및 화면 분할/출력

## **6\. 개발 지침 (가이드)**

* **의존성 최소화:** UI 구성용 rich 및 키 입력을 위한 라이브러리 외에는 파이썬 표준 라이브러리 활용을 극대화하여 Docker 컨테이너 환경의 이식성과 안정성을 높임.  
* **Decorator 패턴 (v3.1 보완):** Move/Combat 등 **액션 클래스는 역할(의도)만 선언**하고, **논리적 검증은 `@validate_action` 데코레이터·Validator 계층**에서 수행한다. 상세는 **7.6 Action 의도·검증·일괄 Resolve** 참조.  
* **Data Flow (v3.1):** 입력 ➔ Entity가 Action 의도 제안 ➔ Validation ➔ (실패 시 대체 행동) ➔ 턴 내 Action 큐 적재 ➔ **일괄 Resolve** ➔ UndoStack Push ➔ 로그 저장 ➔ Turn 마커 ➔ Render.

## **7\. UX 개선 명세 (v3.0)**

v2.0 DS&A 핵심 기능 명세는 유지한다. 본 절은 UX·입력·전투 동작 개선만 정의한다.

### **7.1. 뷰포트 스케일링 (Terminal-Aware Viewport)**

#### **문제 (As-Is)**

* 던전 월드 크기와 카메라 뷰포트가 분리되지 않아, 큰 터미널에서도 맵이 작게 보임.

#### **요구사항**

* **던전 월드 그리드 크기는 7.5에 따라 `80×45` 고정** (층마다 동일 규격).
* 터미널이 커지면 **카메라 뷰포트(화면에 보이는 타일 수)** 만 커져야 함.
* 창 크기 조절 시 매 프레임 렌더 직전 터미널 크기를 재측정한다.

#### **명세 규칙**

* 게임 시작 시 `rich.console.Console().size`로 `(cols, rows)` 측정.
* 뷰포트 크기 산출 (좌우 layout ratio 2:1 반영):
  * `map_panel_width = max(20, (cols * 2) // 3 - 4)`
  * `viewport_width  = max(20, map_panel_width - 2)` (패널 border 여유)
  * `viewport_height = max(8,  rows - 4)`
* 메인(리더보드) 화면에서도 터미널 크기(`cols`) 표시를 유지한다.

#### **구현 대상**

* `dungeon_crawler/ui/renderer.py` — `compute_viewport_size(cols, rows)`
* `dungeon_crawler/main.py` — 렌더 직전 터미널 크기 재측정

```
FixedWorld80x45 → ViewportCalc(terminal) → RenderFrame
```

### **7.2. Debug Mode (이동 로그 필터)**

#### **문제 (As-Is)**

* 플레이어·적 이동 로그가 항상 출력되어 로그 패널이 이동 메시지로 과도하게 채워짐.

#### **요구사항**

* Debug 모드 ON일 때만 **이동 관련 로그**를 출력한다.
* Debug OFF일 때는 이동 로그를 남기지 않는다. (전투/아이템/시스템 로그는 유지)

#### **활성화 방법**

* CLI: `python -m dungeon_crawler.main --debug`
* 환경변수: `DUNGEON_DEBUG=1`
* 인게임 토글(선택): `F1` 또는 `` ` `` (실시간 입력 도입 후)

#### **로그 분류**

| 분류 | Debug OFF | Debug ON |
| :---- | :---- | :---- |
| 플레이어 이동 (`플레이어 이동: (x1,y1) -> (x2,y2)`) | 숨김 | 출력 |
| 적 이동 (`{enemy} 이동: ...`) | 숨김 | 출력 |
| 적 배회/대기 (`배회 실패`, `대기`) | 숨김 | 출력 |
| 전투 결과, EXP/레벨업 | 출력 | 출력 |
| 아이템 획득/사용 | 출력 | 출력 |
| Undo/Redo 시스템 메시지 | 출력 | 출력 |
| 승리/패배/점수 | 출력 | 출력 |

#### **구현 대상**

* `GameManager.debug: bool` 필드
* `_log_move(message: str)` 헬퍼: `if self.debug: self.logs.append(message)`
* Status 패널에 `Debug: ON/OFF` 표시

### **7.3. 실시간 키 입력 (Enter-less Input)**

#### **문제 (As-Is)**

* `input()` + Enter 방식으로 키를 한 글자씩 입력해야 하여 실제 게임 같은 즉각 반응이 불가능함.

#### **요구사항**

* Enter 없이 키를 누르는 즉시 게임이 반응해야 함.

#### **명세 규칙**

* `pynput.keyboard.Listener` 기반 non-blocking 입력 루프로 전환.
* 지원 키: 기존 `input_handler.py` 매핑 유지 (`w/a/s/d`, `c/v`, `u/r`, `i`, `1~0`, `esc`).
* 동작 흐름:
  1. 키 다운 이벤트 수신
  2. `InputHandler.parse_key()` 변환
  3. 기존 `run_game_loop` 분기와 동일하게 처리
  4. 턴 소모 시 즉시 적 턴 + 렌더
* 폴백: `pynput` 불가 환경(Docker TTY 미연결 등)에서는 기존 `input()` 방식 유지. Docker 실행 시 `-it` 플래그 필수.
* 메인 메뉴/게임오버 화면: 단발 키 입력으로 처리 (Enter 또는 아무 키).

```
User keyDown → KeyListener → InputHandler.parse_key
→ GameManager.execute_command → Renderer.render_frame
```

#### **구현 대상**

* `dungeon_crawler/engine/realtime_input.py` 신규 (또는 `input_handler.py` 확장)
* `dungeon_crawler/main.py` — `run_game_loop`의 `input()` 제거, 실시간 리스너 연동

### **7.4. 원거리 공격: 발사 궤적 (Ray Projectile)**

#### **문제 (As-Is)**

* 원거리(V) 공격 시 사선에 적이 없으면 발사 실패, 턴 미소모.
* v2.0 Spec 3.2의 "타깃 없으면 턴 소모 없이 재입력" 규칙은 **근접 공격에만** 적용한다.

#### **요구사항**

* 원거리(`v` + 방향) 시 **적이 없어도 발사 가능**.
* 화살은 직선으로 진행하며, **벽 또는 아이템**에 닿으면 소멸.
* 경로상 **첫 번째 적**에 맞으면 `CombatAction` 발생.

#### **턴 소모 규칙**

| 조건 | 동작 | 턴 소모 |
| :---- | :---- | :---- |
| 화살 없음 | "화살이 부족" 로그, 발사 불가 | X |
| 발사 성공 (적 hit) | 화살 1개 소모 + CombatAction | O |
| 발사 miss (벽/아이템 충돌) | 화살 1개 소모 + miss 로그 | O |
| 발사 방향이 맵 밖 | 마지막 유효 타일까지 진행 후 소멸 | O |
| 근접(C), 인접 적 없음 | "공격 대상이 없습니다" | X |

#### **궤적 알고리즘**

* 시작: 플레이어 위치에서 `(dx, dy)` 방향으로 타일 단위 전진.
* 각 타일 검사 순서:
  1. 맵 경계 밖 → 종료 (miss)
  2. `not dungeon.is_walkable(x, y)` (벽) → 종료 (miss)
  3. `ground_items` 존재 → 종료 (miss, 아이템=장애물)
  4. 적 존재 → `CombatAction` 실행 후 종료 (hit)
* 화살 소모는 발사 시점에 1개 차감 (hit/miss 공통).

#### **로그 예시**

* Hit: `player 원거리 공격 -> enemy1 HP 8->3`
* Miss (벽): `화살이 (5,2)에서 벽에 막혔습니다.`
* Miss (아이템): `화살이 (7,4) 아이템에 막혔습니다.`

#### **구현 대상**

* `GameManager._resolve_ranged_shot(dx, dy) -> bool`
* `_first_enemy_in_ray`를 `_trace_projectile(dx, dy) -> ProjectileResult`로 대체
* `ProjectileResult`: `hit_enemy`, `blocked_at`, `block_reason` (wall/item/boundary)

### **7.5. 던전 맵·층·방 템플릿 명세 (v3.1)**

본 절은 던전 월드 구조의 **확정 설계**이다. 방 템플릿 `.txt` 파일은 사용자가 직접 작성하며, 엔진은 로더만 제공한다.

#### **7.5.1. 월드 그리드 및 층 구조**

| 항목 | 값 |
| :---- | :---- |
| 층당 맵 크기 | **80 × 45** (가로 80, 세로 45) 고정 |
| 층 수 | **3층** (Floor 1 → Floor 2 → Floor 3) |
| 층 이동 | 템플릿 타일 `2`(계단) 위에서 상호작용 시 다음 층으로 이동 |
| 최종 층 | Floor 3은 **최종 방** 템플릿이 배치된 층 |

* 각 층은 독립된 `80×45` 그리드를 가진다.
* 층 전환 시 플레이어는 다음 층 **시작 방** 또는 해당 층 진입 계단 연결 지점에 스폰한다 (구현 시 세부 규칙 확정).

#### **7.5.2. 방 템플릿 파일 형식 (TXT)**

* **경로:** `dungeon_crawler/templates/rooms/{room_type}/{name}.txt`
* **room_type:** `start` (시작방), `normal` (일반 방), `boss` (최종 방)
* **인코딩:** UTF-8, 한 줄 = 그리드의 한 행, 문자는 `0` `1` `2` `3` 만 사용

| 문자 | 의미 |
| :---- | :---- |
| `0` | 빈 공간 (바닥, 이동 가능) |
| `1` | 벽 (이동 불가) |
| `2` | 계단 (다음 층 이동 트리거) |
| `3` | 적 스폰 마커 (위치만 표시, 스탯은 맵에서 정의하지 않음) |

**예시 (`normal/cross.txt`, 5×5):**

```
01010
11111
02020
11111
01010
```

#### **7.5.3. 템플릿 작성 규칙**

* **가장 바깥 벽은 템플릿에 포함하지 않는다.** 방과 방 사이·맵 경계의 외곽 벽은 **배치 엔진**이 별도로 생성한다.
* 템플릿 최소 단위는 **5×5 한 칸(cell)** 이다.
* 템플릿 파일의 가로·세로는 5의 배수여야 한다 (5×5, 10×5, 10×10 등).

#### **7.5.4. 5×5 그리드 배치 (모듈러 방 조립)**

던전 한 층은 **5×5 타일 단위의 메타 그리드** 위에 방 템플릿을 배치한다.

* 메타 그리드 1칸 = 월드 좌표 5×5 타일 블록.
* `80×45` 월드 → 메타 그리드 **16 × 9** 칸 (80/5 × 45/5).
* 각 메타 칸에는 다음 중 하나가 배치된다:
  * **비어 있음** (미사용)
  * **단일 5×5 방 템플릿** (독립 방)
  * **여러 메타 칸에 걸친 합성 방** (인접 메타 칸에 같은 `room_group_id`를 부여하여 하나의 큰 방으로 병합)

```
메타 그리드 (개념):

  [A:5x5] [B:5x5] [  empty  ]
  [A cont] [B cont] [C: 10x5 ]
  
  → A+B 인접 병합 시 10×5 또는 10×10 등 합성 방
  → C는 단독 또는 다른 그룹과 병합
```

**배치 파이프라인:**

1. 층 타입에 맞는 템플릿 풀 로드 (`start` 1개, `normal` N개, `boss`는 Floor 3)
2. 메타 그리드에 `start` 방 1개 배치 (Floor 1)
3. Spanning Tree 등으로 `normal` 방 메타 칸 배치·연결
4. 선택된 메타 칸 그룹에 TXT 템플릿 스탬핑 (월드 좌표로 변환)
5. 방 내부 `1` → 벽, `0` → 바닥, `2` → 계단 엔티티/타일, `3` → 스폰 마커 등록
6. 외곽 벽 자동 생성 (템플릿 바깥 경계·미사용 메타 칸)

#### **7.5.5. 적 스폰 및 층별 스탯 (맵과 분리)**

* TXT의 `3`은 **스폰 위치만** 정의한다. HP/ATK/DEF/EXP 등 스탯은 템플릿·맵 파일에 넣지 않는다.
* 층별 난이도 테이블에서 **시드 기반 랜덤**으로 스탯을 결정한다.

| 층 | HP 범위 | ATK 범위 | DEF 범위 | EXP 보상 범위 |
| :---- | :---- | :---- | :---- | :---- |
| Floor 1 | 6–10 | 2–4 | 0–1 | 4–8 |
| Floor 2 | 10–16 | 3–6 | 0–2 | 8–14 |
| Floor 3 | 14–22 | 5–8 | 1–3 | 12–20 |

* RNG: `random.seed(base_seed + floor_id + spawn_index)` — Undo/Redo 난수 동기화(2.2)와 정합.
* Floor 3 **최종 방**의 보스는 동일 테이블에 `boss` 프로필 배율(예: HP×1.5)을 적용할 수 있다.

#### **7.5.6. As-Is vs To-Be**

| 항목 | As-Is (현재 코드) | To-Be (v3.1) |
| :---- | :---- | :---- |
| 맵 크기 | 30×20 | **80×45** |
| 층 | 없음 | **3층 + 계단** |
| 방 템플릿 | 코드 내 3종 좌표 집합 | **TXT 파일** |
| 방 종류 | 없음 | **start / normal / boss** |
| 배치 | 랜덤 앵커 | **5×5 메타 그리드 + 병합** |
| 적 위치 | `floor[8]` 등 인덱스 | **템플릿 `3` 마커** |
| 적 스탯 | 고정 공식 | **층별 랜덤 범위** |

#### **7.5.7. 구현 대상 (후속)**

* `dungeon_crawler/templates/rooms/` — 사용자 작성 TXT (레포에 샘플만 포함 가능)
* `dungeon_crawler/models/room_template.py` — `RoomTemplateLoader`
* `dungeon_crawler/models/dungeon.py` — 메타 그리드 배치·병합·외곽 벽·통로
* `dungeon_crawler/engine/floor_manager.py` — 3층 전환, 계단 상호작용
* `dungeon_crawler/engine/spawn_resolver.py` — `3` 마커 → Entity + 층별 스탯 롤

### **7.6. Action 의도·검증·일괄 Resolve (v3.1)**

#### **7.6.1. 문제 (As-Is)**

* `@validate_action`이 **메서드 내부 try/except → False** 로 동작하여, “의도 선언”과 “논리 검증”이 한곳에 섞여 있음.
* 플레이어 입력 즉시 `execute()` 되고, 적 턴도 순차 즉시 실행되어 **의도 큐 → 일괄 resolve → render** 흐름이 아님.

#### **7.6.2. 설계 원칙**

1. **Action 클래스 / Entity 행동 메서드:** “무엇을 하려는지(의도)”만 기술. `MoveAction`은 dx/dy 이동 의도, `CombatAction`은 대상·가해자 의도만 보유.
2. **Validator (`@validate_action` 및 전용 Validator):** 이동 가능 여부, 타깃 존재, 탄약, 층/계단 조건 등 **모든 논리 검증**을 담당. 실패 시 `ValidationResult(ok=False, reason=...)` 반환.
3. **턴 루프:** 각 Entity가 유효한 Action을 **선택할 때까지** 의도 제안 → 검증 반복. 실패 시 **다른 행동**(대기, 우회 이동 등)을 선택.

#### **7.6.3. 턴 Resolve 파이프라인**

```
[Turn Start]
  For each Entity in turn_queue (FIFO):
    loop:
      proposed = entity.propose_action()   # AI/입력 기반 의도
      result   = validate(proposed)          # @validate_action / ActionValidator
      if result.ok:
         action_queue.append(proposed)
         break
      else:
         entity.pick_fallback()             # 다른 행동 재선택
  resolve_all(action_queue)                # execute() 순차 적용, 로그·Undo 기록
  end_turn_marker()
  render()
```

* **플레이어:** 입력 → 의도 Action 생성 → 검증 → 실패 시 재입력 (턴 미소모).
* **적:** `propose_action()` (A\*, 배회, 공격) → 검증 실패 시 fallback (대기, 다른 방향).
* **일괄 Resolve:** 턴 내 확정된 Action 리스트를 **한 번에** `resolve_all()` 실행 후 **한 번** 렌더링.

#### **7.6.4. `@validate_action` 재정의 (To-Be)**

* **적용 위치:** `propose_action()` 직후, `execute()` **이전**.
* **역할:**
  * 맵 경계·벽·점유·아이템·계단·층 조건 검사
  * 통과 시 `Action` 그대로 반환 (또는 `ValidationResult(ok=True, action=...)`)
  * 실패 시 `ValidationResult(ok=False, reason=...)` — **execute 호출 금지**
* **금지:** Action `execute()` / `undo()` 내부에서 검증 로직 중복 구현.

#### **7.6.5. Undo/Redo 정합**

* `resolve_all()` 완료 후에만 `UndoStack`에 Action push + `EndTurnAction` 마커.
* Resolve 이전 검증 실패 Action은 스택에 넣지 않는다.

#### **7.6.6. 구현 대상 (후속)**

* `dungeon_crawler/utils/decorators.py` — `ValidationResult`, 검증 전용 `validate_action`
* `dungeon_crawler/utils/action_validator.py` — Move/Combat/Loot/Stairs 규칙
* `dungeon_crawler/engine/turn_resolver.py` — `propose → validate → queue → resolve_all`
* `dungeon_crawler/engine/game_manager.py` — 즉시 execute 제거, Resolver 위임

## **8\. v3 테스트 및 수용 기준 (Acceptance Criteria)**

### **8.1. 수용 기준**

| # | 항목 | 검증 방법 | 기대 결과 |
| :---- | :---- | :---- | :---- |
| 1 | 월드 크기 | Floor 1 로드 | 그리드 80×45 |
| 2 | 3층·계단 | Floor 1 계단(2) 상호작용 | Floor 2로 전환 |
| 3 | TXT 템플릿 | `templates/rooms/normal/*.txt` 로드 | 0/1/2/3 파싱, 외곽 벽 미포함 |
| 4 | 5×5 메타 그리드 | 10×10 템플릿 2칸 병합 배치 | 합성 방 1개로 스탬핑 |
| 5 | 적 스폰 | 템플릿 `3` 2칸 + Floor 2 | 위치는 템플릿, 스탯은 Floor 2 범위 내 랜덤 |
| 6 | Validation 분리 | 벽 방향 Move propose | execute 전 Validator 거부, fallback |
| 7 | 일괄 Resolve | 플레이어+적 1턴 | action_queue 확정 후 1회 resolve + 1회 render |
| 8 | 뷰포트 | 80x24 vs 200x50 터미널 | 월드 80×45 동일, `viewport` 크기만 변화 |
| 9 | Debug OFF/ON | 이동 5회 | OFF: 이동 로그 0 / ON: 이동 로그 있음 |
| 10 | 실시간 입력 | `w` 단일 키 | Enter 없이 이동 |
| 11 | 원거리 miss/hit | V+WASD | miss 시 화살 소모·턴 진행 / hit 시 Combat |

### **8.2. 단위 테스트 파일 (후속 구현)**

* `tests/test_room_template_loader.py` — TXT 0/1/2/3 파싱, 5 배수 검증
* `tests/test_meta_grid_placement.py` — 5×5 메타 칸 배치·병합
* `tests/test_floor_manager.py` — 3층 전환, 계단 트리거
* `tests/test_spawn_resolver.py` — `3` 마커 + 층별 스탯 RNG
* `tests/test_action_validator.py` — propose 후 검증, execute 미호출
* `tests/test_turn_resolver.py` — queue → resolve_all → 단일 render
* `tests/test_viewport_size.py` — 80×45 월드 + 터미널별 뷰포트
* `tests/test_debug_logging.py` — debug ON/OFF 이동 로그 필터
* `tests/test_ranged_projectile.py` — hit / wall_miss / item_miss / no_arrow
* `tests/test_realtime_input.py` — `parse_key` + 리스너 폴백 (mock)

### **8.3. 디렉토리 구조 추가 (v3 / v3.1)**

```
dungeon_crawler/
├── templates/
│   └── rooms/
│       ├── start/          # 시작방 TXT (사용자 작성)
│       ├── normal/         # 일반 방 TXT
│       └── boss/           # 최종 방 TXT (Floor 3)
├── models/
│   └── room_template.py    # TXT 로더, RoomTemplate
├── engine/
│   ├── floor_manager.py    # 3층·계단
│   ├── spawn_resolver.py   # 스폰 마커 + 층별 스탯
│   ├── turn_resolver.py    # propose → validate → resolve_all
│   └── realtime_input.py   # pynput 실시간 입력
├── utils/
│   ├── action_validator.py # 논리 검증 (데코레이터 연동)
│   └── decorators.py       # ValidationResult, @validate_action
└── ui/
    └── renderer.py         # compute_viewport_size
```