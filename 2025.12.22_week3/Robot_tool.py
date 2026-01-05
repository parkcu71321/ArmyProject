# robot_tool.py
from langchain_core.tools import tool
from Robot_arm import perform_gesture

@tool
def perform_robot_gesture(command: str) -> str:
    """
    [Robot Arm Tool]
    로봇팔에게 '잡기' 또는 '풀기' 동작을 수행시킵니다.
    """
    command = command.strip().replace("'", "").replace('"', "")

    if command not in ["잡기", "풀기"]:
        return "Error: 지원하지 않는 로봇 명령"

    perform_gesture(command)
    return f"ROBOT: {command} 동작을 수행했습니다."
