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
* **Decorator 패턴:** 이동/공격 메서드 호출 전 @validate\_action 데코레이터를 거쳐 예외 발생 시 False 리턴 및 메인 루프 재입력 처리.  
* **Data Flow:** 입력 ➔ 유효성 검사 ➔ Action 인스턴스화 ➔ UndoStack Push ➔ 로그 버퍼 저장 ➔ 게임 상태 업데이트 ➔ Turn 마커 삽입 ➔ 화면(UI) 렌더링 (Viewport 적용) 순서 보장.