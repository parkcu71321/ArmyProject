#vision_tool
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import cv2
import mediapipe as mp
import time
import numpy as np
from langchain_core.tools import tool

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

def calculate_3d_angle(a, b, c):
    a = np.array([a.x, a.y, a.z])
    b = np.array([b.x, b.y, b.z])
    c = np.array([c.x, c.y, c.z])
    ba = a - b; bc = c - b
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(np.clip(cosine, -1.0, 1.0))
    return int(np.degrees(angle))

@tool
def capture_raw_hand_data(instruction: str = "") -> str:
    """
    [Sensor Tool] 
    카메라로 손가락 각도를 측정합니다. 
    사용자가 자세를 3초간 유지해야 데이터를 반환합니다.
    """
    print(f"\n[Tool:Eye] 👀 측정 시작... (목표: {instruction}, 3초 유지)")
    
    cap = None
    for i in range(2):
        temp = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if temp.isOpened(): cap = temp; break
    if cap is None: return "Error: Camera Fail"
    
    cap.set(3, 640); cap.set(4, 480)
    window_name = 'Robot Eye (Hold 3 Sec)'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    HOLD_TIME = 3.0 
    stable_start = None
    captured_data = None
    
    with mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5) as hands:
        while cap.isOpened():
            ret, img = cap.read()
            if not ret: continue
            img = cv2.flip(img, 1)
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            res = hands.process(img_rgb)
            
            cv2.putText(img, f"Mission: {instruction}", (10,30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0,255,255), 2)
            
            if res.multi_hand_landmarks:
                for lm in res.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(img, lm, mp_hands.HAND_CONNECTIONS)
                    l = lm.landmark
                    joints = [(1,2,3), (5,6,8), (9,10,12), (13,14,16), (17,18,20)]
                    angles = [calculate_3d_angle(l[j[0]], l[j[1]], l[j[2]]) for j in joints]
                    
                    cv2.putText(img, str(angles), (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200,200,200), 1)

                    if stable_start is None: stable_start = time.time()
                    prog = min((time.time()-stable_start)/HOLD_TIME, 1.0)
                    
                    cv2.rectangle(img, (0,460), (int(640*prog), 480), (0,255,0), -1)
                    
                    remain = max(0.0, HOLD_TIME - (time.time()-stable_start))
                    cv2.putText(img, f"Hold: {remain:.1f}s", (320, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2)
                    
                    if prog >= 1.0:
                        captured_data = str(angles)
                        cv2.putText(img, "CAPTURED!", (200,240), cv2.FONT_HERSHEY_SIMPLEX, 2, (0,255,0), 3)
                        cv2.imshow(window_name, img)
                        cv2.waitKey(800)
                        break
            else:
                stable_start = None
                cv2.putText(img, "Show Hand...", (10,400), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200,200,200), 2)

            if captured_data: break
            cv2.imshow(window_name, img)
            if cv2.waitKey(1)==ord('q'): captured_data="Cancelled"; break

    cap.release()
    cv2.destroyAllWindows()
    return captured_data