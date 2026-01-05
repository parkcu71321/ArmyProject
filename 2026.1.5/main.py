import os
import re
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

from StateManager import StateManager
from Planner import Planner
from Executor import Executor
from FeedbackLoop import FeedbackLoop

def extract_target_from_text(text: str):
    numbers = re.findall(r"-?\d+", text)
    if len(numbers) != 3:
        raise ValueError(" 좌표는 반드시 3개(x,y,z)여야 합니다.")
    return tuple(map(int, numbers))

def main():
    print("===  자율 좌표 이동 에이전트 시작 ===")

    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model="gemma-3-4b-it",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0
    )

    state_manager = StateManager()
    planner = Planner(llm)
    executor = Executor()
    feedback = FeedbackLoop()

    user_input = input("🗣️ 명령 입력 (예: 3,5,4에 있는 거 잡아줘): ")

    try:
        target = extract_target_from_text(user_input)
    except ValueError as e:
        print(e)
        return

    state_manager.set_target_position(target)
    print(f"🎯 목표 좌표 설정 완료: {target}")

    step = 0
    while True:
        step += 1
        print(f"\n--- STEP {step} ---")
        state = state_manager.get_state()
        print(f"📍 현재 좌표: {state['current_position']}")

        if state_manager.is_goal_reached():
            print("✅ 목표 좌표 도달 완료!")
            break

        # Planner 판단
        plan = planner.decide(state)
        print(f"🧠 Planner 판단: {plan}")

        # Executor 실행
        current_pos = tuple(state["current_position"])
        exec_result = executor.execute(current_pos, plan["action"])
        print(f"⚙️ Executor 실행 결과: {exec_result}")

        # 상태 업데이트
        state_manager.update_position(exec_result["action"])

        # Feedback 판단
        feedback_result = feedback.judge({
            "success": state_manager.is_goal_reached(),
            "current_position": state_manager.get_state()["current_position"],
            "target_position": state_manager.get_state()["target_position"],
            "last_action": exec_result["action"]
        })
        print(f"🔍 Feedback 판단: {feedback_result}")

        if feedback_result["decision"] == "DONE":
            final_pos = state_manager.get_state()["current_position"]
            target_pos = state_manager.get_state()["target_position"]

            print("🏁 에이전트 종료\n")
            print(f"📌 최종 도달 좌표: {final_pos}")
            print(f"🎯 목표 좌표: {target_pos}")
            break
        elif feedback_result["decision"] == "REPLAN":
            print("🔄 재계획 진행")
        elif feedback_result["decision"] == "RETRY":
            print("🔁 동일 단계 재시도")

if __name__ == "__main__":
    main()
