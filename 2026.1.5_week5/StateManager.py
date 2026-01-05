from datetime import datetime

class StateManager:
    def __init__(self):
        self.state = {
            "current_position": [0, 0, 0],
            "target_position": None,
            "history": []
        }

    def set_target_position(self, target):
        self.state["target_position"] = list(target)

    def get_state(self):
        return self.state

    def update_position(self, action):
        x, y, z = self.state["current_position"]

        # Executor와 맞춘 action 이름
        if action == "move_right":
            x += 1
        elif action == "move_left":
            x -= 1
        elif action == "move_back":
            y += 1
        elif action == "move_forward":
            y -= 1
        elif action == "move_up":
            z += 1
        elif action == "move_down":
            z -= 1

        self.state["current_position"] = [x, y, z]

        self.state["history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "position": [x, y, z]
        })

    def is_goal_reached(self):
        return (
            self.state["target_position"] is not None and
            self.state["current_position"] == self.state["target_position"]
        )
