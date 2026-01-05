import os
import sys
import re
import serial
from typing import Union
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import PromptTemplate

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    sys.exit("GOOGLE_API_KEY 환경변수가 없습니다.")

# ===========================
# Serial 설정
# ===========================
STX = 0x02
ETX = 0x03

def send_packet(cmd, value):
    packet = bytes([STX, cmd, value, ETX])
    ser.write(packet)

def send_servo1(val): send_packet(0x01, int(val))
def send_servo2(val): send_packet(0x02, int(val))
def send_servo3(val): send_packet(0x03, int(val))
def send_servo4(val): send_packet(0x04, int(val))
def send_servo5(val): send_packet(0x05, int(val))

# ===========================
# 잡기 / 풀기 서보 값
# ===========================
GESTURE_SERVO_MAP = {
    "잡기": [180, 90, 30, 50, 90],
    "풀기": [90, 90, 30, 50, 90]
}

def perform_gesture(gesture: str):
    """서보 제어"""
    if gesture not in GESTURE_SERVO_MAP:
        print(f"❌ 알 수 없는 명령: {gesture}")
        return
    vals = GESTURE_SERVO_MAP[gesture]
    send_servo1(vals[0])
    send_servo2(vals[1])
    send_servo3(vals[2])
    send_servo4(vals[3])
    send_servo5(vals[4])
    print(f"✅ '{gesture}' 동작 완료")

# ===========================
# AI 에이전트 설정
# ===========================
llm = ChatGoogleGenerativeAI(model="gemma-3-4b-it", google_api_key=api_key, temperature=0.0)

# 단일 도구: 사용자 입력 판단
class GestureTool:
    name = "gesture_tool"
    description = "사용자 입력을 분석하여 '잡기' 또는 '풀기'를 반환합니다."
    
    def invoke(self, text: str):
        text = text.lower()
        if "잡" in text: return "잡기"
        elif "풀" in text: return "풀기"
        else: return "알 수 없는 명령"

gesture_tool = GestureTool()

# 프롬프트 템플릿
template = """
당신은 로봇 제어 에이전트입니다.
사용자가 입력한 문장을 분석하여 '잡기' 또는 '풀기' 동작을 판단하세요.

가용 도구: {tools}

출력 형식:
Action: tool_name
Action Input: input
Observation: result
Final Answer: result_message

Question: {input}
Thought:{agent_scratchpad}
"""

prompt = PromptTemplate.from_template(template)

def parse_output(text: str) -> Union[AgentAction, AgentFinish]:
    if "Final Answer:" in text:
        return AgentFinish({"output": text.split("Final Answer:")[-1].strip()}, text)
    match = re.search(r"Action:\s*(.*?)\nAction Input:\s*(.*)", text, re.DOTALL)
    if match:
        return AgentAction(match.group(1).strip(), match.group(2).strip().strip('"'), text)
    return AgentFinish({"output": text}, text)

# ===========================
# 사용자 입력 처리
# ===========================
def process_input(user_input: str):
    # AI 판단
    action_input = user_input
    tool_result = gesture_tool.invoke(action_input)
    
    if tool_result in ["잡기", "풀기"]:
        perform_gesture(tool_result)
        return f"동작 '{tool_result}' 수행 완료"
    else:
        return "❌ 알 수 없는 명령입니다. '잡아줘' 또는 '풀어줘'를 사용하세요."

# ===========================
# 메인 루프
# ===========================
if __name__ == "__main__":
    try:
        ser = serial.Serial('COM5', baudrate=9600)
    except Exception as e:
        print(f"🔴 시리얼 연결 실패: {e}")
        sys.exit(1)

    print("=== 🤖 Hand Gesture Robot ===")
    print("명령어 예시: '잡아줘', '풀어줘' (종료: q)")

    while True:
        user_input = input(">> ").strip()
        if user_input.lower() in ["q", "quit"]:
            print("프로그램 종료")
            break
        if not user_input:
            continue

        result_msg = process_input(user_input)
        print(result_msg)
