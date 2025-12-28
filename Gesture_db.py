#gesture_db
import json
import os
import numpy as np

DB_FILE = "hand_data.json"

# [사용자 맞춤 초기 데이터]
# 순서: [엄지, 검지, 중지, 약지, 새끼]

INITIAL_SEEDS = {
    "바위": [
        # 사용자 제공 주먹 값 (엄지가 펴진 형태의 주먹으로 추정)
        [145, 55, 42, 28, 29]
    ],
    
    "가위": [
        # 1. 총 모양 가위 (엄지, 검지 펴짐)
        [177, 170, 68, 53, 31],
        
        # 2. 검지중지 가위 (엄지 반쯤 굽힘, 검지/중지 펴짐)
        [105, 172, 174, 60, 66]
    ],
    
    "보": [
        # 사용자 제공 보 값 (완벽하게 펴짐)
        [178, 172, 173, 177, 172]
    ]
}

class GestureDB:
    def __init__(self):
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        
        # 파일 없으면 사용자 초기값으로 생성
        print("[DB] 사용자 맞춤 초기 데이터(Seed)를 생성합니다.")
        self.save_data(INITIAL_SEEDS)
        return INITIAL_SEEDS

    def save_data(self, new_data=None):
        if new_data: self.data = new_data
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_sample(self, label, angles):
        """성공한 데이터만 추가 학습"""
        if label not in self.data: self.data[label] = []
        self.data[label].append(angles)
        self.save_data()

    def get_all_data(self):
        return self.data

db = GestureDB()