#analysis_tool
import json
import numpy as np
from langchain_core.tools import tool
from gesture_db import db
@tool
def analyze_hand_data(input_str: str) -> str:
    """
    [Analysis Tool]
    데이터 비교 후, 사용자 요청에 맞는 멘트를 생성합니다.
    성공 시 데이터 학습을 수행합니다.
    """
    try:
        parts = input_str.split("Data:")
        raw_target = parts[0].replace("Target:", "").replace(",", "").strip()
        data_str = parts[1].strip()
        current_vector = json.loads(data_str)
        
        # 동의어 매핑
        target_label = raw_target
        if any(x in raw_target for x in ["가위", "브이", "총"]): target_label = "가위"
        elif any(x in raw_target for x in ["바위", "주먹"]): target_label = "바위"
        elif any(x in raw_target for x in ["보", "보자기"]): target_label = "보"
            
    except: return "Error: 데이터 오류"

    print(f"\n[Tool:Brain] 🧠 분석 중... (목표: {target_label})")

    # KNN 비교
    all_data = db.get_all_data()
    min_dist = float("inf")
    best_match = "Unknown"
    
    for label, samples in all_data.items():
        for sample in samples:
            dist = np.linalg.norm(np.array(current_vector) - np.array(sample))
            if dist < min_dist:
                min_dist = dist
                best_match = label
    
    # 판정 기준 (사용자 데이터가 들어갔으므로 60~70이면 충분)
    THRESHOLD = 70.0 
    
    # [핵심] 결과 멘트 생성 로직
    
    if target_label == "ANY":
        # 식별 모드
        if min_dist < THRESHOLD:
            return f"INFO: 현재 '{best_match}' 입니다."
        else:
            return f"INFO: 알 수 없는 동작입니다."

    else:
        # 타겟 모드
        is_success = (best_match == target_label and min_dist < THRESHOLD)

        if is_success:
            # 성공 -> 학습 -> 멘트 출력
            db.add_sample(target_label, current_vector)
            return f"PASS: {target_label} 냈습니다."
        else:
            # 실패 -> 멘트 출력
            return f"FAIL: {target_label}가 안 내졌습니다."