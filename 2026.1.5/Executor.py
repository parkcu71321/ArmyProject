from typing import Tuple, Dict

class Executor:
    MOVE_TABLE = {
        "move_right":   ( 1,  0,  0),  # +x
        "move_left":    (-1,  0,  0),  # -x
        "move_back":    ( 0,  1,  0),  # +y
        "move_forward": ( 0, -1,  0),  # -y
        "move_up":      ( 0,  0,  1),  # +z
        "move_down":    ( 0,  0, -1),  # -z
    }

    def execute(self, current_position: Tuple[int,int,int], action: str) -> Dict:
        if action not in self.MOVE_TABLE:
            return {
                "success": False,
                "error": f"Unknown action: {action}",
                "from": current_position,
                "to": current_position,
                "action": action
            }

        dx, dy, dz = self.MOVE_TABLE[action]
        new_position = (
            current_position[0] + dx,
            current_position[1] + dy,
            current_position[2] + dz
        )

        return {
            "success": True,
            "from": current_position,
            "to": new_position,
            "action": action
        }
