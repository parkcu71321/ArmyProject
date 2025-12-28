# planner.py
import json
import re
from langchain.prompts import PromptTemplate


class Planner:
    def __init__(self, llm):
        self.llm = llm

        self.prompt = PromptTemplate.from_template("""
너는 로봇팔을 제어하는 "자율 플래닝 AI"이다.

현재 가상 환경 정보:
- 상자 중심 좌표: (4, 4, 4)
- 상자 한 변 길이: 2
- 상자 범위:
  - x: 3 ~ 5
  - y: 3 ~ 5
  - z: 3 ~ 5

금지 영역 규칙:
- y >= 4 인 영역은 접근 금지이다
- 금지 영역을 포함하는 위치를 선택하면 실패한다

목표:
- 사용자가 "상자를 잡아줘"라고 하면
  → 상자 내부에서 grasp 가능한 지점을 하나 선택하라
  → 단, 금지 영역을 피하도록 시도하라
- 좌표는 스스로 판단해서 선택한다
- 선택한 좌표가 항상 성공할 필요는 없다
- 사용자가 단순히 "잡아줘", "풀어줘", "놓아줘"라고 입력하면
  → 좌표 계산 없이 perform_robot_gesture 사용
- **LLM은 입력에서 '상자'라는 단어가 없으면 절대로 grasp_box를 선택하지 마라**

⚠️ 출력 규칙 (절대 위반하지 마라):
- 반드시 JSON 하나만 출력한다
- 설명, 문장, 코드블록, 주석을 포함하지 마라
- JSON 외의 어떤 문자도 출력하지 마라

사용 가능한 행동:
1. grasp_box
   - 설명: 특정 좌표를 계산해서 정밀하게 잡아야 할 때 사용 (예: "상자 잡아줘")
   - input: {{ "grasp_point": {{ "x": float, "y": float, "z": float }} }}
   
2. perform_robot_gesture
   - 설명: 좌표 계산 없이 단순히 그리퍼를 오므리거나 벌릴 때 사용 (예: "잡아줘", "풀어줘", "놓아줘")
   - input: "잡기" 또는 "풀기"

출력 예시 1 (복잡한 작업):
{{
  "goal": "상자 잡기",
  "steps": [
    {{
      "action": "grasp_box",
      "input": {{
        "grasp_point": {{
          "x": 5.2,
          "y": 4.3,
          "z": 5.5
        }}
      }}
    }}
  ]
}}
                                                   
출력 예시 2 (단순 작업):
{{
  "goal": "로봇팔 제어",
  "steps": [
    {{"action": "perform_robot_gesture", "input": "잡기"}},
    {{"action": "perform_robot_gesture", "input": "풀기"}}
  ]
}}

사용자 입력:
{input}
""")

        self.chain = self.prompt | self.llm

    # =========================
    # JSON 안전 추출
    # =========================
    def _extract_json(self, text: str) -> dict:
        try:
            # ```json ... ``` 형태
            codeblock_match = re.search(
                r"```json\s*(\{.*?\})\s*```",
                text,
                re.S
            )
            if codeblock_match:
                return json.loads(codeblock_match.group(1))

            # 일반 JSON fallback
            match = re.search(r"\{.*\}", text, re.S)
            if match:
                return json.loads(match.group())

            raise ValueError("JSON 없음")

        except Exception:
            return {
                "goal": "planning_failed",
                "steps": []
            }

    # =========================
    # 계획 생성
    # =========================
    def make_plan(self, user_input: str) -> dict:
        response = self.chain.invoke({
            "input": user_input
        })

        return self._extract_json(response.content)


# =========================
# 단독 테스트
# =========================
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    from langchain_google_genai import ChatGoogleGenerativeAI

    load_dotenv()

    llm = ChatGoogleGenerativeAI(
        model="gemma-3-4b-it",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3  # 일부러 약간 랜덤성
    )

    planner = Planner(llm)

    plan = planner.make_plan("상자 잡아줘")
    print(plan)
