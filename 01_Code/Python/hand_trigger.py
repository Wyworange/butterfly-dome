# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome
# Author  : Yuwen Wang
# Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed and
#           tested by the author. Hand tracking: Google MediaPipe Hands
#           (https://developers.google.com/mediapipe/solutions/vision/hand_landmarker),
#           camera: OpenCV (https://opencv.org), USB serial: pySerial (https://pyserial.readthedocs.io).
# ---------------------------------------------------------------------------------------------
"""
Butterfly dome - hand gesture trigger.

Close your hand into a fist, then open it: the butterflies play one cycle.
Webcam + MediaPipe Hands on the computer, Arduino UNO over USB.

Install (Python 3.9 - 3.12):
    pip install mediapipe==0.10.14 opencv-python pyserial
Run:
    python hand_trigger.py              (finds the Arduino by itself)
    python hand_trigger.py /dev/cu.usbmodem1101   (or give the port)
Quit: press q in the camera window.
Close the Arduino IDE Serial Monitor first, otherwise the port is busy.
"""
import sys, time, glob
import cv2
import mediapipe as mp
import serial

# ---------------- settings ----------------
CAMERA_INDEX = 0        # try 1 if the wrong camera opens
STABLE_FRAMES = 4       # a pose must hold this many frames before it counts (filters flicker)
OPEN_FINGERS = 4        # >= this many straight fingers = open hand
FIST_FINGERS = 1        # <= this many straight fingers = fist
MAX_GAP_S = 2.0         # the fist -> open must happen within this many seconds
# ------------------------------------------


def find_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    cands = (glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/cu.usbserial*') +
             glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
    if not cands:
        try:
            from serial.tools import list_ports
            cands = [p.device for p in list_ports.comports() if 'Arduino' in (p.description or '') or 'CH340' in (p.description or '')]
        except Exception:
            pass
    if not cands:
        sys.exit('Arduino not found. Plug it in, close the Serial Monitor, or pass the port: python hand_trigger.py COM3')
    return cands[0]


def count_fingers(lm, handedness):
    """number of straight fingers from 21 MediaPipe landmarks"""
    n = 0
    # index, middle, ring, pinky: tip above the middle joint (further from the wrist)
    wrist = lm[0]
    def d(a, b): return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
        if d(lm[tip], wrist) > d(lm[pip], wrist) * 1.15:
            n += 1
    # thumb: tip far from the index knuckle
    if d(lm[4], lm[5]) > d(lm[3], lm[5]) * 1.2:
        n += 1
    return n


def main():
    port = find_port()
    print('Arduino on', port)
    ser = serial.Serial(port, 115200, timeout=0)
    time.sleep(2.0)                     # the UNO resets when the port opens
    ser.reset_input_buffer()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        sys.exit('Camera not found. On a Mac allow Terminal / your editor in System Settings > Privacy > Camera.')

    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5)
    draw = mp.solutions.drawing_utils

    pose, pose_count, stable = None, 0, None
    fist_time = None
    busy = False
    status = 'make a fist, then open your hand'

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame = cv2.flip(frame, 1)
        res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        now_pose = None
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]
            draw.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)
            f = count_fingers(lm.landmark, res.multi_handedness[0])
            now_pose = 'open' if f >= OPEN_FINGERS else ('fist' if f <= FIST_FINGERS else None)
            cv2.putText(frame, f'fingers: {f}', (20, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        # debounce
        if now_pose == pose:
            pose_count += 1
        else:
            pose, pose_count = now_pose, 1
        if pose is not None and pose_count == STABLE_FRAMES and pose != stable:
            stable = pose
            if stable == 'fist':
                fist_time = time.time()
                status = 'fist - now open your hand'
            elif stable == 'open' and fist_time and time.time() - fist_time <= MAX_GAP_S and not busy:
                ser.write(b'G')
                busy = True
                fist_time = None
                status = 'butterflies moving...'

        # messages from the Arduino
        line = ser.readline().decode(errors='ignore').strip()
        if line == 'DONE':
            busy = False
            status = 'make a fist, then open your hand'

        color = (0, 200, 255) if busy else (0, 255, 0)
        cv2.putText(frame, status, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        cv2.imshow('butterfly dome - q to quit', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    ser.write(b'Z')
    cap.release()
    cv2.destroyAllWindows()
    ser.close()


if __name__ == '__main__':
    main()
