# executor.py
from Robot_tool import perform_robot_gesture


# =========================
# 가상 환경 정의
# =========================

BOX_CENTER = (4.0, 4.0, 4.0)
BOX_SIZE = 2.0  # 한 변 길이

BOX_MIN = (
    BOX_CENTER[0] - BOX_SIZE / 2,
    BOX_CENTER[1] - BOX_SIZE / 2,
    BOX_CENTER[2] - BOX_SIZE / 2,
)
BOX_MAX = (
    BOX_CENTER[0] + BOX_SIZE / 2,
    BOX_CENTER[1] + BOX_SIZE / 2,
    BOX_CENTER[2] + BOX_SIZE / 2,
)

# 금지 영역: y >= 4 는 접근 금지
FORBIDDEN_Y = 4.0


class Executor:
    def run(self, plan: dict) -> dict:
        results = []
        success = True

        for idx, step in enumerate(plan.get("steps", []), start=1):
            action = step.get("action")
            action_input = step.get("input")

            print(f"\n[Executor] Step {idx}: {action}({action_input})")

            try:
                # =========================
                # 새 행동: 상자 잡기
                # =========================
                if action == "grasp_box":
                    output, step_success = self._grasp_box(action_input)

                # =========================
                # 기존 행동
                # =========================
                elif action == "perform_robot_gesture":
                    output = perform_robot_gesture(action_input)
                    step_success = True

                else:
                    output = f"Unknown action: {action}"
                    step_success = False

                results.append({
                    "step": idx,
                    "action": action,
                    "input": action_input,
                    "output": output,
                    "success": step_success
                })

                if not step_success:
                    success = False
                    break

            except Exception as e:
                results.append({
                    "step": idx,
                    "action": action,
                    "input": action_input,
                    "output": str(e),
                    "success": False
                })
                success = False
                break

        return {
            "success": success,
            "results": results
        }

    # =========================
    # grasp_box 실제 구현
    # =========================
    def _grasp_box(self, action_input: dict):
        gp = action_input.get("grasp_point")

        if not gp:
            return "❌ grasp_point 없음", False

        x, y, z = gp["x"], gp["y"], gp["z"]

        print(f"[Executor] 선택된 grasp point: ({x}, {y}, {z})")

        # 1️⃣ 상자 내부인지 검사
        if not (
            BOX_MIN[0] <= x <= BOX_MAX[0] and
            BOX_MIN[1] <= y <= BOX_MAX[1] and
            BOX_MIN[2] <= z <= BOX_MAX[2]
        ):
            return "❌ 상자 외부 좌표 → grasp 실패", False

        # 2️⃣ 금지 영역 검사
        if y >= FORBIDDEN_Y:
            return "❌ 금지 영역(y >= 4) 침범 → grasp 실패", False

        # 3️⃣ 성공
        return (
            f"✅ 상자 grasp 성공 @ ({x}, {y}, {z}) "
            f"(검지와 엄지가 해당 지점에서 만남)",
            True
        )


# =========================
# 단독 테스트
# =========================
if __name__ == "__main__":
    executor = Executor()

    test_plan = {
        "goal": "상자 잡기",
        "steps": [
            {
                "action": "grasp_box",
                "input": {
                    "grasp_point": {"x": 4.5, "y": 3.5, "z": 4.0}
                }
            }
        ]
    }

    result = executor.run(test_plan)
    print("\n[Executor Result]")
    print(result)
