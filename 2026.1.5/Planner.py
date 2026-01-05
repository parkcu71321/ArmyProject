# Planner.py
import json
import re
from typing import Dict
from langchain.prompts import PromptTemplate


class Planner:
    """
    LLM 기반 판단 모듈 (두뇌)
    - 실제 이동 ❌
    - 좌표 직접 수정 ❌
    - 다음 '한 번의 이동 방향'만 결정
    """

    def __init__(self, llm):
        self.llm = llm

        self.prompt = PromptTemplate.from_template("""
너는 3차원 격자 공간에서 이동하는 자율 에이전트의 판단 AI이다.

[좌표계 기준 - 절대 변경 금지]
- x축: 오른쪽 +x / 왼쪽 -x
- y축: 뒤 +y / 앞 -y
- z축: 위 +z / 아래 -z

[이동 규칙]
- 한 번에 오직 하나의 이동만 선택할 수 있다
- 한 번 이동 시 좌표는 정확히 1만 변한다
- 선택 가능한 행동은 아래 6개뿐이다

가능한 행동 목록:
- move_right   (+x)
- move_left    (-x)
- move_back    (+y)
- move_forward (-y)
- move_up      (+z)
- move_down    (-z)

[축 이동 판단 절대 규칙 - 매우 중요]
각 축에 대해 반드시 아래의 "수학적 부호 규칙"만 사용하라.

- delta_x = target_x - current_x
  - delta_x > 0 → move_right
  - delta_x < 0 → move_left

- delta_y = target_y - current_y
  - delta_y > 0 → move_back
  - delta_y < 0 → move_forward

- delta_z = target_z - current_z
  - delta_z > 0 → move_up
  - delta_z < 0 → move_down

중요 제한 사항:
- "크다 / 작다 / 앞 / 뒤" 같은 자연어 직관으로 판단하지 마라
- 반드시 delta 값의 부호(+, -)로만 판단하라
- delta == 0 인 축은 절대로 선택하지 마라
- 한 번에 하나의 축만 선택하라

[너의 역할]
1. current_position 과 target_position 을 비교하라
2. 값이 다른 축 중 하나만 선택하라
3. 위의 delta 부호 규칙에 맞는 행동 하나만 고르라
4. 절대로 두 개 이상의 행동을 선택하지 마라
5. 좌표를 직접 계산하거나 출력하지 마라

[출력 규칙 - 매우 중요]
- 반드시 JSON 하나만 출력하라
- JSON 외의 어떤 문자도 출력하지 마라
- 설명은 reason 필드에만 작성하라

[출력 형식]
{{
  "action": "<이동 행동 하나>",
  "reason": "<delta 부호 규칙에 따라 왜 이 행동을 선택했는지>"
}}

[현재 상태]
current_position: {current_position}
target_position: {target_position}
""")

        self.chain = self.prompt | self.llm

    # =========================
    # JSON 안전 추출
    # =========================
    def _extract_json(self, text: str) -> Dict:
        try:
            text = text.replace("```json", "").replace("```", "").strip()
            match = re.search(r"\{.*\}", text, re.S)
            if not match:
                raise ValueError("JSON not found")
            return json.loads(match.group())
        except Exception:
            return {
                "action": None,
                "reason": "LLM 출력에서 유효한 JSON을 추출하지 못함"
            }

    # =========================
    # 다음 행동 결정
    # =========================
    def decide(self, state: Dict) -> Dict:
        response = self.chain.invoke({
            "current_position": state["current_position"],
            "target_position": state["target_position"]
        })
        return self._extract_json(response.content)
