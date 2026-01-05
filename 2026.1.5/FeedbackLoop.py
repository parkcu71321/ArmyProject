from typing import Dict

class FeedbackLoop:
    def judge(self, state: Dict) -> Dict:
        current_pos = tuple(state.get("current_position"))
        target_pos = tuple(state.get("target_position"))

        if current_pos == target_pos:
            return {"decision": "DONE", "reason": "목표 좌표에 도달함"}
        return {"decision": "REPLAN", "reason": "목표 좌표에 아직 도달하지 않음"}
