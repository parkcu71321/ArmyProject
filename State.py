import json
from datetime import datetime

class StateManager:
    def snapshot(self, goal: str, exec_result: dict) -> dict:
        """
        Executor의 실행 결과를 FeedbackLoop가 읽기 좋은 형태로 변환
        """
        state = {
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "success": exec_result.get("success", False),
            "steps": exec_result.get("results", [])
        }

        # 디버깅을 위해 출력 (선택 사항)
        # print(f"\n[StateManager] State Snapshot Created (Success: {state['success']})")
        
        return state