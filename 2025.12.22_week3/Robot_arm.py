# robot_arm.py
import serial
import time

STX = 0x02
ETX = 0x03

_ser = None

def get_serial():
    global _ser
    if _ser is None:
        _ser = serial.Serial(
            port="COM5",
            baudrate=9600,
            timeout=1
        )
        time.sleep(2)  # ⭐ 아두이노 리셋 대기 (필수)
    return _ser

def send_packet(cmd, value):
    ser = get_serial()
    packet = bytes([STX, cmd, value, ETX])
    ser.write(packet)

def send_servo1(val): send_packet(0x01, int(val))
def send_servo2(val): send_packet(0x02, int(val))
def send_servo3(val): send_packet(0x03, int(val))
def send_servo4(val): send_packet(0x04, int(val))
def send_servo5(val): send_packet(0x05, int(val))

GESTURE_SERVO_MAP = {
    "잡기": [180, 90, 30, 50, 90],
    "풀기": [90, 90, 30, 50, 90]
}

def perform_gesture(gesture: str):
    if gesture not in GESTURE_SERVO_MAP:
        raise ValueError("Unknown gesture")

    vals = GESTURE_SERVO_MAP[gesture]
    send_servo1(vals[0])
    send_servo2(vals[1])
    send_servo3(vals[2])
    send_servo4(vals[3])
    send_servo5(vals[4])

    print(f"🤖 로봇팔 '{gesture}' 동작 완료")
