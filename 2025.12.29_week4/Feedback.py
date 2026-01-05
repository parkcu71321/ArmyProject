#Feedback
import json
import re
from langchain.prompts import PromptTemplate

class FeedbackLoop:
    def __init__(self, llm):
        self.llm = llm

        self.prompt = PromptTemplate.from_template("""
너는 자율 에이전트의 감독관(Supervisor)이다.
아래 실행 결과(State)를 보고 에이전트의 행동을 평가하라.

[판단 기준]
1. "success": true 이면 → "DONE"
2. "success": false 이고, 에러 메시지가 좌표 문제(금지 영역, 상자 외부 등)라면 → "REPLAN"
3. 그 외 단순 오류 → "RETRY"

[State]
{state}

⚠️ 출력 규칙:
- 반드시 JSON 포맷으로만 출력하라.
- REPLAN일 경우, reason 필드에 실패 원인을 구체적으로 적어라 (Planner가 참고할 수 있게).

출력 예시:
{{ "decision": "DONE", "reason": "성공적으로 잡음" }}
{{ "decision": "REPLAN", "reason": "선택한 좌표가 금지 영역(y ≥ 4)에 포함됨" }}
""")
        self.chain = self.prompt | self.llm

    def judge(self, state: dict) -> dict:
        response = self.chain.invoke({
            "state": json.dumps(state, ensure_ascii=False)
        })
        
        return self._extract_json(response.content)

    def _extract_json(self, text: str) -> dict:
        try:
            # 마크다운 코드블록 제거
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
        except json.JSONDecodeError:
            # 파싱 실패 시 안전 장치
            return {"decision": "REPLAN", "reason": "JSON 파싱 실패, 재시도 필요"}
        
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
        temperature=0.2
    )

    feedback = FeedbackLoop(llm)

    # 성공 케이스
    success_state = {
        "success": True,
        "results": [
            {
                "step": 1,
                "action": "grasp_box",
                "output": " 상자 grasp 성공 @ (4.5, 3.5, 4.0)"
            }
        ]
    }

    # 금지 영역 실패 케이스
    forbidden_state = {
        "success": False,
        "results": [
            {
                "step": 1,
                "action": "grasp_box",
                "output": " 금지 영역(y >= 4) 침범 → grasp 실패"
            }
        ]
    }

    print("\n=== SUCCESS STATE TEST ===")
    print(feedback.judge(success_state))

    print("\n=== FORBIDDEN STATE TEST ===")
    print(feedback.judge(forbidden_state))
