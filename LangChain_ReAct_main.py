import os
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# 작성하신 모듈들 import
from planner import Planner
from executor import Executor
from state import StateManager
from feedback import FeedbackLoop

def main():
    print("=== 🤖 Box Grasping Agent (Virtual Env) ===")
    
    # 1. 설정 로드
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        print("❌ GOOGLE_API_KEY가 없습니다. .env 파일을 확인하세요.")
        return

    # 2. LLM 초기화 (Planner와 Feedback이 같이 씀)
    llm = ChatGoogleGenerativeAI(
        model="gemma-3-4b-it", 
        google_api_key=api_key,
        temperature=0.1 
    )

    # 3. 모듈 인스턴스 생성
    planner = Planner(llm)
    executor = Executor()
    state_manager = StateManager()
    feedback_loop = FeedbackLoop(llm)

    # 4. 사용자 목표 입력
    user_goal = input("\n🎯 명령을 입력하세요 (예: 상자를 잡아줘) >> ").strip()
    if not user_goal: return

    max_loops = 5
    loop_count = 0
    
    # 재계획을 위한 피드백 저장 변수
    current_feedback = "" 
    plan = None

    while loop_count < max_loops:
        loop_count += 1
        print(f"\n{'='*10} LOOP {loop_count} {'='*10}")

        # [STEP 1] Plan 생성
        if plan is None:
            print("🧠 Planner: 생각 중...")

            # 재계획 시 이전 실패 이유를 입력에 포함
            if current_feedback:
                query_with_context = f"{user_goal}\n(중요: 이전 시도 실패 원인 -> {current_feedback}. 이를 반영해서 좌표를 수정해라.)"
            else:
                query_with_context = user_goal
            
            plan = planner.make_plan(query_with_context)
            print(f"📋 Plan 목표: {plan.get('goal')}")

            # 좌표 출력: grasp_box인 경우에만
            if plan.get("steps"):
                step_input = plan["steps"][0]["input"]
                if isinstance(step_input, dict) and "grasp_point" in step_input:
                    gp = step_input["grasp_point"]
                    print(f"   → 목표 좌표: ({gp.get('x')}, {gp.get('y')}, {gp.get('z')})")

        # [STEP 2] Execute 실행
        print("⚙️ Executor: 실행 중...")
        exec_result = executor.run(plan)

        # [STEP 3] State 저장
        state = state_manager.snapshot(plan["goal"], exec_result)

        # [STEP 4] Feedback 판단
        print("🔍 Feedback: 결과 분석 중...")
        judgment = feedback_loop.judge(state)
        
        decision = judgment.get("decision")
        reason = judgment.get("reason", "")
        
        print(f"🧭 판단 결과: {decision} (이유: {reason})")

        # [STEP 5] 루프 제어
        if decision == "DONE":
            print("\n✅ 미션 성공! 에이전트를 종료합니다.")
            break
            
        elif decision == "REPLAN":
            print(f"♻️ 실패하여 재계획합니다. (피드백 반영)")
            plan = None          # 계획 초기화 (새로 짜기 위해)
            current_feedback = reason  # 실패 이유 저장 -> 다음 루프 Planner에게 전달
            time.sleep(1)        # 잠시 대기
            
        elif decision == "RETRY":
            print("🔁 일시적 오류로 재시도합니다.")
            # plan = None을 하지 않음 -> 같은 계획으로 다시 실행
            
        else:
            print(f"⚠️ 알 수 없는 결정({decision})으로 종료합니다.")
            break

    if loop_count >= max_loops:
        print("\n⏹️ 최대 루프 횟수를 초과하여 종료합니다.")

if __name__ == "__main__":
    main()
