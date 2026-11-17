# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome
# Author  : Yuwen Wang
# Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed and
#           tested by the author. Hand tracking: Google MediaPipe Hands
#           (https://developers.google.com/mediapipe/solutions/vision/hand_landmarker),
#           camera: OpenCV (https://opencv.org), USB serial: pySerial (https://pyserial.readthedocs.io).
# ---------------------------------------------------------------------------------------------
"""
Butterfly dome v2 - hand control.

Two modes (press m in the window to switch):
  FOLLOW  : the wings copy your hand. Open hand = wings open, fist = wings closed, in between = in between.
  TRIGGER : make a fist, then open your hand -> the butterflies flap 3 times.

Install (Python 3.9 - 3.12):  pip install mediapipe==0.10.14 opencv-python pyserial
Run:                          python hand_v2.py            (or: python hand_v2.py /dev/cu.usbmodem1101)
Close the Arduino Serial Monitor first. Press q to quit.
"""
import sys, time, glob
import cv2, mediapipe as mp, serial

CAMERA_INDEX = 0
SEND_EVERY_S = 0.06      # follow mode: how often to send the wing position


def find_port():
    if len(sys.argv) > 1: return sys.argv[1]
    c = glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/cu.usbserial*') + glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*')
    if not c:
        from serial.tools import list_ports
        c = [p.device for p in list_ports.comports()]
    if not c: sys.exit('Arduino not found - plug it in or pass the port name.')
    return c[0]


def openness(lm):
    """0 = fist, 1 = fully open: mean fingertip distance from the wrist, scaled by palm size"""
    def d(a, b): return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    palm = d(lm[0], lm[9]) + 1e-6
    tips = [d(lm[t], lm[0]) / palm for t in (8, 12, 16, 20)]
    v = (sum(tips) / 4 - 0.9) / (1.9 - 0.9)       # ~0.9 for a fist, ~1.9 for an open hand
    return max(0.0, min(1.0, v))


def main():
    ser = serial.Serial(find_port(), 115200, timeout=0); time.sleep(2); ser.reset_input_buffer()
    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened(): sys.exit('Camera not found (Mac: System Settings > Privacy > Camera).')
    hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.6, min_tracking_confidence=0.5)
    draw = mp.solutions.drawing_utils
    mode, smooth, last_send = 'FOLLOW', 1.0, 0
    stable, cnt, prev, fist_t, busy = None, 0, None, None, False

    while True:
        ok, frame = cap.read()
        if not ok: break
        frame = cv2.flip(frame, 1)
        res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        o = None
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0]; draw.draw_landmarks(frame, lm, mp.solutions.hands.HAND_CONNECTIONS)
            o = openness(lm.landmark)

        if mode == 'FOLLOW':
            target = 1.0 if o is None else o                 # no hand -> wings open
            smooth = 0.7 * smooth + 0.3 * target
            if time.time() - last_send > SEND_EVERY_S:
                ser.write(f'A{int(round((1 - smooth) * 100))}\n'.encode()); last_send = time.time()
            msg = f'FOLLOW  hand open {int(smooth*100)}%'
        else:
            pose = None if o is None else ('open' if o > 0.75 else 'fist' if o < 0.25 else None)
            cnt = cnt + 1 if pose == prev else 1; prev = pose
            if pose and cnt == 4 and pose != stable:
                stable = pose
                if pose == 'fist': fist_t = time.time()
                elif fist_t and time.time() - fist_t < 2 and not busy:
                    ser.write(b'G'); busy = True; fist_t = None
            if ser.readline().decode(errors='ignore').strip() == 'DONE': busy = False
            msg = 'TRIGGER  ' + ('flapping...' if busy else 'fist, then open')

        cv2.putText(frame, msg + '   (m: switch mode, q: quit)', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        cv2.imshow('butterfly dome v2', frame)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'): break
        if k == ord('m'): mode = 'TRIGGER' if mode == 'FOLLOW' else 'FOLLOW'; ser.write(b'Z')

    ser.write(b'Z'); cap.release(); cv2.destroyAllWindows(); ser.close()


if __name__ == '__main__':
    main()
