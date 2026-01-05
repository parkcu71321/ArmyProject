# ArmyProject Changelog

## Week 1: 자료 조사
- 프로젝트 관련 기초 자료조사 내용 공유

## Week 2: 사용자 요청 기반 손동작 감지 및 분석 기능

목표
- AI 에이전트가 객체 감지 -> 상황 판단 -> 계획 수립 -> 로봇팔 동작까지 수행할 수 있도록, 사용자 요청이 올 때 손동작을 정확히 인식하고 분석하는 기능을 구현.

구현 내용
1. Test_gemma:
   - 사용 모델 불러오기 테스트
2. Test_env:
   - 가상환경 테스트
3. Vision Tool: 
   - 화면에 사용자의 손동작을 보여주고, 각 손가락의 백터 값 추출
   - 예: 가위를 내면 해당 손동작 벡터값 확인

4. Analysis Tool: 
   - Vision Tool에서 얻은 벡터 데이터를 분석
   - gesture.db에 저장된 기준 데이터와 비교하여 해당 손동작이 무엇인지 판단
   - 초기에는 가위/바위/보 각 동작당 하나의 데이터를 기준으로 비교
   - 이후 사용자 요청 시마다 handdata.json에 해당 동작 저장 -> 누적 데이터로 비교 가능

5. 워크플로우
   - 사용자 요청  Vision Tool 실행 -> 손동작 시각화, 백터 추출
   - 추출된 데이터 -> Analysis Tool로 전달 -> 동작 분석 및 판단
   - AI 에이전트가 판단 결과를 기반으로 로봇팔 동작 계획에 반영

특징
- 사용자 요청마다 실시간 손동작 분석 가능
- 본 프로젝트의 손동작 판별은 학습 기반이 아닌, 누적된 경험 데이터와의 유사도 비교를 통해 최소 오차 클래스를 선택하는 방식으로 구현되었다.

## Week 3: AI Agent–로봇팔 하드웨어 제어 연동

목표
- AI 에이전트가 판단한 결과를 실제 로봇팔 동작으로 실행하여 판단->행동단계까지 연결되는 구조를 구현한다.

구현 내용
1. 로봇팔 제어 모듈 (robot_arm.py)
- 하드웨어 담당에게 정보 가져옴

2. AI Agent용 로봇 제어 Tool (robot_tool.py)
- 로봇팔 제어 기능을 LangChain Tool 형태로 분리
- AI 에이전트가 자연어 판단 결과를 바로 로봇팔 동작으로 실행 가능
- 허용된 명령만 실행하도록 안전한 입력 검증 수행
- 지원 명령: 잡기, 풀기
- 로봇 동작 수행 결과를 Agent에게 다시 전달

동작 흐름
1. 사용자 명령 입력  
   예) `잡아줘`

2. AI 에이전트가 로봇 제어 요청으로 판단

3. perform_robot_gesture Tool 호출

4. 시리얼 통신을 통해 로봇팔 실제 동작 수행

5. 수행 결과를 사용자에게 출력

특징
- AI 에이전트의 판단 결과가 실제 물리 로봇 동작으로 연결됨
- 로봇 제어 로직을 Tool로 분리하여 확장 가능한 구조 설계
- Vision 기반 인식(Week 2) 결과와 결합 가능한 기반 마련
- AI Agent의 지각 -> 판단 -> 행동 파이프라인 완성

##  Week 4: 자율 플래닝 AI Agent 파이프라인 구축

목표
AI Agent가 단순 명령 수행을 넘어 상황을 판단 -> 계획 수립 -> 실행 -> 결과 평가 -> 재계획까지 수행하는 자율 플래닝 구조를 구현한다.

가상 환경에서의 좌표 기반 판단을 통해 향후 실제 로봇팔 제어로 확장 가능한 Agent 아키텍처를 설계한다.

구현 내용
1. Planner (계획 수립 모듈) – planner.py
- LLM 기반 자율 플래닝 모듈
- 사용자 입력을 해석하여 수행 목표(goal)와 단계적 행동 계획(steps) 생성
- 작업 난이도에 따라 서로 다른 행동 선택
  - 단순 명령 → `perform_robot_gesture`
  - 정밀 작업(예: 상자 잡기) → `grasp_box` + 좌표 계산
- 환경 정보 및 제약 조건을 프롬프트에 명시
  - 상자 위치, 크기
  - 금지 영역(y ≥ 4)
  JSON만 출력하도록 강제하여 안정적인 파이프라인 유지

2. Executor (실행 모듈) – executor.py
- Planner가 생성한 계획을 실제로 수행
- 각 Step을 순차적으로 실행하며 성공/실패 여부 기록
- 가상 환경 내 제약 조건 검사
  - 상자 내부 좌표 여부
  - 금지 영역 침범 여부
- 실행 결과를 구조화된 형태로 반환
  - step 단위 성공 여부
  - 전체 success 플래그

3. State Manager (상태 기록) – state.py
- Executor의 실행 결과를 FeedbackLoop가 평가하기 쉬운 형태로 변환
- 목표, 성공 여부, 각 단계 결과를 하나의 State Snapshot으로 관리
- Agent의 행동 이력을 명시적으로 기록

 4. Feedback Loop (자율 판단 모듈) – feedback.py
- 실행 결과(State)를 바탕으로 다음 행동을 판단하는 감독자
- LLM을 사용하여 결과를 해석하고 다음 중 하나를 결정
  - DONE : 목표 성공
  - REPLAN : 좌표 문제 등으로 계획 수정 필요
  - RETRY : 일시적 오류로 동일 계획 재시도
- REPLAN 시 실패 원인을 자연어로 제공하여 Planner가 참고하도록 설계

5. Main Loop (Agent Orchestration) – main.py
- Planner -> Executor -> State -> FeedbackLoop를 하나의 루프로 통합
- 실패 시 피드백을 반영하여 재계획을 수행하는 반복 구조
- 최대 루프 횟수를 제한하여 무한 루프 방지

동작 흐름
1. 사용자 명령 입력  
   예) 상자를 잡아줘

2. Planner가 환경 정보와 제약 조건을 고려하여 계획 수립

3. Executor가 계획에 따라 단계별 실행

4. StateManager가 실행 결과를 상태(State)로 저장

5. FeedbackLoop가 결과를 평가
   - 성공 -> 종료
   - 실패 -> 원인을 Planner에게 전달하여 재계획

6. 목표 달성 또는 최대 루프 도달 시 종료

특징
- 단순 반응형 Agent가 아닌 자율 플래닝 구조 구현
- 실패를 인지하고 스스로 수정하는 Feedback 기반 Agent
- 환경 제약을 고려한 좌표 판단 로직 포함
- Planner / Executor / Feedback의 역할 분리로 높은 확장성 확보
- Week 3의 로봇팔 제어 Tool과 결합 가능한 구조
- 향후 Vision 기반 객체 인식 결과를 Planner 입력으로 확장 가능

## Week 5: LLM 기반 자율 좌표 이동 AI Agent 구현

목표
- 사용자의 자연어 입력에서 목표 좌표(x, y, z)를 추출하고
- AI Agent가 현재 좌표와 목표 좌표를 비교하여
- 판단 → 이동 → 결과 평가 → 재계획을 반복 수행하는
  자율 좌표 이동 Agent 파이프라인을 구현한다.

본 구조는 가상 환경에서의 좌표 판단을 기반으로 하며,
향후 실제 로봇팔 제어 및 Vision 기반 위치 인식과 결합 가능한 Agent 아키텍처를 목표로 한다.

구현 내용

1. Planner (LLM 기반 판단 모듈) – Planner.py
- LLM을 사용하여 **다음 한 번의 이동 방향(action)만 결정
- 실제 이동 수행 x
- 좌표 직접 수정 x

구현 특징
- 현재 좌표(current_position)와 목표 좌표(target_position)를 비교하여 판단
- delta = target - current의 부호(sign)만을 기준으로 이동 방향 결정
- 자연어 직관(앞/뒤/가까움 등)을 전면 배제하여 LLM 판단 통제
- 한 번에 하나의 축만 이동하도록 제한
- JSON 형식 출력 강제 및 안전한 파싱 로직 구현


2. Executor (행동 실행 모듈) – Executor.py
- Planner가 결정한 단일 이동 명령을 실제 좌표 변화로 변환
- 3차원 격자 공간에서 한 번에 ±1 이동만 허용

지원 행동
- move_right / move_left  (x축)
- move_back / move_forward (y축)
- move_up / move_down (z축)

구현 특징
- 이동 결과를 직접 상태에 반영하지 않고 실행 결과 객체로 반환
- Executor는 “어떻게 움직일지”만 담당하며,
  상태 관리 책임은 StateManager에 위임

3. State Manager (상태 관리 모듈) – StateManager.py
- Agent의 상태를 단일 객체로 관리
  - current_position
  - target_position
  - action history
- Executor의 실행 결과를 반영하여 좌표 업데이트
- 모든 이동 이력을 timestamp와 함께 누적 저장

구현 특징
- 상태 변경 책임을 한 곳으로 집중
- Agent의 행동 이력을 명시적으로 기록
- 디버깅 및 시각화, 추후 학습 데이터로 확장 가능

4. Feedback Loop (결과 평가 모듈) – FeedbackLoop.py
- 현재 좌표와 목표 좌표를 비교하여 다음 행동을 판단

판단 결과
- DONE : 목표 좌표 도달
- REPLAN : 목표 좌표에 아직 도달하지 않음

구현 특징
- FeedbackLoop는 실행 주체가 아닌 감독자(Supervisor) 역할
- 실행 결과를 단순 성공/실패가 아닌
  다음 행동 결정 신호로 추상화

5. Main Loop (Agent Orchestration) – main.py
- Planner -> Executor -> StateManager -> FeedbackLoop를 하나의 루프로 통합
- 사용자 입력에서 목표 좌표를 추출
- Feedback 판단에 따라 재계획을 반복 수행

구현 특징
- main은 판단 로직을 가지지 않고 전체 흐름만 제어
- LLM은 Planner에만 사용되어 책임이 명확히 분리됨
- while-loop 자체가 곧 자율 Agent Loop

동작 흐름
1. 사용자 자연어 명령 입력  
   예) `3,5,4에 있는 거 잡아줘`
   
3. main에서 목표 좌표 추출 및 초기 상태 설정

4. Planner가 현재 좌표와 목표 좌표를 비교하여 다음 이동 방향 결정

5. Executor가 이동 수행

6. StateManager가 좌표 및 이력 업데이트

7. FeedbackLoop가 결과 평가
   - DONE → Agent 종료
   - REPLAN → 다음 루프 진행

특징
- LLM을 전능한 제어자가 아닌 계획자(Planner)로만 사용
- 판단 / 실행 / 상태 / 평가 책임이 명확히 분리된 구조
- 실패를 인지하고 스스로 수정하는 자율 Agent 구현
- 단순 반응형 시스템이 아닌 목표 지향적 AI Agent
- Week 2 Vision 인식, Week 3 로봇팔 제어와 결합 가능한 구조
- 실제 물리 환경으로 확장 가능한 좌표 기반 Agent 아키텍처 완성
