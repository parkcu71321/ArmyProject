import os
import sys
import re
import operator
import serial
from typing import Annotated, TypedDict, Union, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.prompts import PromptTemplate
from langgraph.graph import END, StateGraph

from vision_tool import capture_raw_hand_data
from analysis_tool import analyze_hand_data
from robot_tool import perform_robot_gesture            #-------------------추가

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key: sys.exit(1)

llm = ChatGoogleGenerativeAI(model="gemma-3-4b-it", google_api_key=api_key, temperature=0.0)

tools = [capture_raw_hand_data, analyze_hand_data,perform_robot_gesture]            #------------------- perform_robot_gesture 추가
tool_names = [t.name for t in tools]
tool_descriptions = "\n".join([f"{t.name}: {t.description}" for t in tools])

template = """
당신은 로봇 제어 에이전트입니다.
사용자 요청을 이해하고 적절한 Tool을 선택하세요.

[기본 동작 규칙]
- 손 제스처 인식 요청은 반드시 [측정] -> [분석] 순서로 처리합니다.
- 로봇팔 제어 요청은 즉시 해당 Tool을 호출합니다.

[손 제스처 인식 규칙]
1. `capture_raw_hand_data` 호출
   - Input 예: '가위 보여주세요'
2. `analyze_hand_data` 호출
   - Input 형식: "Target:가위, Data:[...]"
3. 분석 툴이 주는 결과 메시지
   (예: "가위 냈습니다", "가위가 안 내졌습니다", "현재 가위 입니다")
   를 **그대로 Final Answer로 출력**하고 종료하세요.
   ❗ 말을 바꾸거나 추가 설명을 하지 마세요.

[로봇팔 제어 규칙]
- 아래 요청은 **카메라를 사용하지 않습니다.**

1. '잡아줘', '잡아', '집어', '쥐어'
   → `perform_robot_gesture` 호출
   → Action Input: '잡기'

2. '풀어줘', '풀어', '놓아', '놔줘'
   → `perform_robot_gesture` 호출
   → Action Input: '풀기'

- 로봇팔 Tool의 결과 메시지를
  **그대로 Final Answer로 출력**하고 종료하세요.

[키워드 매핑]
- 주먹 / 바위 → '바위'
- 가위 / 브이 / 총 → '가위'
- 보 / 보자기 → '보'
- 확인해줘 / 뭐야 / 판단해줘 → 'ANY'

가용 도구:
{tools}

[출력 형식]
Question: input
Thought: reasoning
Action: tool_name
Action Input: input
Observation: result
...
Final Answer: result_message

Begin!

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

class AgentState(TypedDict):
    input: str
    intermediate_steps: Annotated[List[tuple], operator.add]
    agent_outcome: Union[AgentAction, AgentFinish, None]

def run_agent_node(state):
    steps = state.get("intermediate_steps", [])
    
    if steps:
        last_result = steps[-1][1]
        if (
            "PASS:" in last_result
            or "FAIL:" in last_result
            or "INFO:" in last_result
            or last_result.startswith("ROBOT:")
        ):
            clean_msg = (
                last_result
                .replace("PASS:", "")
                .replace("FAIL:", "")
                .replace("INFO:", "")
                .replace("ROBOT:", "")
                .strip()
            )
            return {
                "agent_outcome": AgentFinish(
                    {"output": clean_msg},
                    "Done"
                )
            }

        
        if "Cancelled" in last_result or "Error" in last_result:
             return {"agent_outcome": AgentFinish({"output": "작업이 취소되었습니다."}, "Error")}

    scratchpad = ""
    for action, obs in steps:
        scratchpad += f"\nAction: {action.tool}\nAction Input: {action.tool_input}\nObservation: {obs}\nThought:"
    
    chain = prompt | llm.bind(stop=["\nObservation"])
    res = chain.invoke({
        "input": state["input"], "tools": tool_descriptions, 
        "tool_names": ", ".join(tool_names), "agent_scratchpad": scratchpad
    })
    return {"agent_outcome": parse_output(res.content)}

def run_tool_node(state):
    action = state["agent_outcome"]
    print(f"  ⚙️ [System] 툴 실행: {action.tool} (입력: {action.tool_input})")
    if action.tool == capture_raw_hand_data.name:
        result = capture_raw_hand_data.invoke(action.tool_input)
    elif action.tool == analyze_hand_data.name:
        result = analyze_hand_data.invoke(action.tool_input)
    elif action.tool == perform_robot_gesture.name:   # -------------- 추가
        result = perform_robot_gesture.invoke(action.tool_input)
    else:
        result = "Error: Unknown Tool"
    
    print(f"      -> 결과: {result}")
    return {"intermediate_steps": [(action, result)]}

workflow = StateGraph(AgentState)
workflow.add_node("agent", run_agent_node)
workflow.add_node("tool", run_tool_node)
workflow.set_entry_point("agent")
workflow.add_conditional_edges("agent", lambda x: "end" if isinstance(x["agent_outcome"], AgentFinish) else "continue", {"continue": "tool", "end": END})
workflow.add_edge("tool", "agent")
app = workflow.compile()

def main():
    print("=== 🤖 Custom Hand Gesture Robot ===")
    print("사용자 맞춤 데이터로 초기화되었습니다.")
    
    while True:
        try:
            print("\n🔵 명령 입력 (q:종료):")
            user_input = input("User >> ")
            if user_input.lower() in ["q", "quit"]: break
            if not user_input.strip(): continue

            print("🟡 검증 시작...")
            for s in app.stream({"input": user_input, "intermediate_steps": []}):
                if "agent" in s and isinstance(s["agent"]["agent_outcome"], AgentFinish):
                    print("\n" + "┌" + "-"*40 + "┐")
                    print(f"   {s['agent']['agent_outcome'].return_values['output']}")
                    print("└" + "-"*40 + "┘")
        except Exception as e:
            print(f"🔴 오류: {e}")

if __name__ == "__main__":
    main()