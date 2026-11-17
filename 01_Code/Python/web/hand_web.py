# ---------------------------------------------------------------------------------------------
# Project : Kinetic Butterfly Dome
# Author  : Yuwen Wang
# Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed and
#           tested by the author. Reuses the gesture logic of ../hand_trigger.py (Google MediaPipe
#           Hands, OpenCV, pySerial). Web server: Python standard library (http.server).
# ---------------------------------------------------------------------------------------------
"""
Butterfly dome - gesture control in the browser (the version used for the final piece).

A small local web server: Python opens the webcam, runs the same fist -> open-palm detection as
hand_trigger.py, sends 'G' to the Arduino over USB serial, and streams the camera image to a page
at http://localhost:8765. When a gesture triggers, the page also releases a flock of drawn
butterflies from the palm (on screen only; it does not affect the Arduino).

Run (from this folder, with the packages in ../requirements.txt installed):
    python hand_web.py                         (finds the Arduino by itself)
    python hand_web.py /dev/cu.usbmodem1101    (or give the serial port)
Then open http://localhost:8765 and click "Turn on camera".
Close the Arduino IDE Serial Monitor first. Ctrl+C in the terminal stops the server.
The server only listens on 127.0.0.1; the camera image is not sent anywhere else.
"""
import argparse
import glob
import json
from pathlib import Path
import runpy
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parent


class Controller:
    def __init__(self, port=None):
        self.port = port
        self.lock = threading.Lock()
        self.lifecycle = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = None
        self.frame = None
        self.state = dict(running=False, starting=False, connected=False, camera=False,
                          busy=False, port='', fingers=None, trigger=0, palm=None, message='Click "Turn on camera" to start', error='')

    def update(self, **values):
        with self.lock:
            self.state.update(values)

    def snapshot(self):
        with self.lock:
            return dict(self.state)

    def start(self):
        with self.lifecycle:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            with self.lock:
                self.frame = None
            self.update(starting=True, error='', message='Connecting to the Arduino and the camera...')
            self.thread = threading.Thread(target=self.run, daemon=True)
            self.thread.start()

    def stop(self):
        self.stop_event.set()
        if self.thread and self.thread.is_alive():
            self.update(message='Stopping...')

    def close(self):
        self.stop()
        if self.thread:
            self.thread.join(timeout=8)

    def run(self):
        cap = ser = hands = None
        failure = ''
        try:
            # Load hand_trigger.py (settings + count_fingers) without running its desktop main().
            original = runpy.run_path(str(ROOT.parent / 'hand_trigger.py'))
            cv2, mp, serial = original['cv2'], original['mp'], original['serial']
            if self.stop_event.is_set():
                return
            ports = (glob.glob('/dev/cu.usbmodem*') + glob.glob('/dev/cu.usbserial*') +
                     glob.glob('/dev/ttyACM*') + glob.glob('/dev/ttyUSB*'))
            if not self.port and not ports:
                from serial.tools import list_ports
                ports = [p.device for p in list_ports.comports()
                         if 'Arduino' in (p.description or '') or 'CH340' in (p.description or '')]
            port = self.port or (ports[0] if ports else None)
            if not port:
                raise RuntimeError('Arduino not found. Plug in the USB cable, close the Serial Monitor and try again.')
            ser = serial.Serial(port, 115200, timeout=0)
            self.update(connected=True, port=port)
            if self.stop_event.wait(2):
                return
            ser.reset_input_buffer()
            cap = cv2.VideoCapture(original['CAMERA_INDEX'])
            if not cap.isOpened():
                raise RuntimeError('Cannot open the camera. In macOS System Settings > Privacy & Security > Camera, allow your terminal or editor, and close other apps that use the camera.')
            hands = mp.solutions.hands.Hands(max_num_hands=1, min_detection_confidence=0.6,
                                            min_tracking_confidence=0.5)
            self.update(starting=False, running=True, camera=True, message='Make a fist, then open your hand within 2 seconds')
            pose, pose_count, stable, fist_time, busy = None, 0, None, None, False
            incoming = bytearray()
            last_frame = time.monotonic()
            while not self.stop_event.is_set():
                ok, frame = cap.read()
                if not ok or frame is None:
                    # macOS cameras often drop a few frames while warming up or switching apps;
                    # only give up after a sustained outage.
                    if time.monotonic() - last_frame > 3:
                        raise RuntimeError('No camera image for 3 seconds. Close other apps that use the camera (FaceTime, Zoom, Photo Booth), then stop and start again.')
                    self.stop_event.wait(0.05)
                    continue
                last_frame = time.monotonic()
                frame = cv2.flip(frame, 1)
                result = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                now_pose, fingers, palm = None, None, None
                if result.multi_hand_landmarks:
                    landmarks = result.multi_hand_landmarks[0]
                    # Palm centre (wrist + finger bases), normalised to the mirrored frame shown on the page.
                    base = [landmarks.landmark[i] for i in (0, 5, 9, 13, 17)]
                    palm = [round(sum(p.x for p in base) / 5, 4), round(sum(p.y for p in base) / 5, 4)]
                    mp.solutions.drawing_utils.draw_landmarks(frame, landmarks, mp.solutions.hands.HAND_CONNECTIONS)
                    fingers = original['count_fingers'](landmarks.landmark, result.multi_handedness[0])
                    now_pose = 'open' if fingers >= original['OPEN_FINGERS'] else ('fist' if fingers <= original['FIST_FINGERS'] else None)
                if now_pose == pose:
                    pose_count += 1
                else:
                    pose, pose_count = now_pose, 1
                if pose is not None and pose_count == original['STABLE_FRAMES'] and pose != stable:
                    stable = pose
                    if stable == 'fist' and not busy:
                        fist_time = time.monotonic()
                        self.update(message='Fist detected - now open your hand')
                    elif stable == 'open' and fist_time is not None and time.monotonic() - fist_time <= original['MAX_GAP_S'] and not busy:
                        ser.write(b'G')
                        busy, fist_time = True, None
                        # The page plays the fly-away animation whenever this counter changes.
                        with self.lock:
                            self.state['trigger'] += 1
                            self.state.update(palm=palm, message='Butterflies moving, waiting for the Arduino to finish...')
                if fist_time is not None and time.monotonic() - fist_time > original['MAX_GAP_S']:
                    fist_time = None
                    self.update(message='Too slow - make a fist again, then open your hand')
                incoming.extend(ser.read(min(ser.in_waiting, 4096)))
                while b'\n' in incoming:
                    line, _, remainder = incoming.partition(b'\n')
                    incoming = bytearray(remainder)
                    if line.strip() == b'DONE':
                        busy, fist_time = False, None
                        self.update(message='Done. Make a fist, then open your hand')
                if len(incoming) > 8192:
                    incoming.clear()
                ok, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    with self.lock:
                        self.frame = encoded.tobytes()
                self.update(fingers=fingers, busy=busy)
        except (Exception, SystemExit) as exc:
            failure = str(exc) or type(exc).__name__
            self.update(error=failure, message='Could not start or connect. Check and try again')
        finally:
            if hands is not None:
                hands.close()
            if cap is not None:
                cap.release()
            if ser is not None:
                try:
                    ser.write(b'Z')
                except Exception:
                    pass
                finally:
                    ser.close()
            with self.lock:
                self.frame = None
            self.update(starting=False, running=False, connected=False, camera=False,
                        busy=False, fingers=None, message='Could not start or connect. Check and try again' if failure else 'Stopped. The camera is off')


class Server(ThreadingHTTPServer):
    daemon_threads = True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        if self.path != '/api/status':
            super().log_message(format, *args)

    def send_bytes(self, payload, content_type, status=200):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(payload)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        self.wfile.write(payload)

    def allowed_host(self):
        return self.headers.get('Host') in (f'localhost:{self.server.server_port}',
                                           f'127.0.0.1:{self.server.server_port}')

    def do_GET(self):
        if not self.allowed_host():
            self.send_error(403)
            return
        if self.path in ('/', '/index.html'):
            self.send_bytes((ROOT / 'index.html').read_bytes(), 'text/html; charset=utf-8')
        elif self.path == '/api/status':
            self.send_bytes(json.dumps(self.server.controller.snapshot()).encode(), 'application/json')
        elif self.path == '/video':
            controller = self.server.controller
            with controller.lifecycle:
                worker = controller.thread
            if worker is None or not worker.is_alive():
                self.send_error(409, 'Camera is not running')
                return
            # A stalled client must not retain a streaming handler indefinitely.
            self.connection.settimeout(3)
            self.send_response(200)
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            try:
                while worker.is_alive() and not controller.stop_event.is_set():
                    with controller.lock:
                        frame = controller.frame
                    if frame:
                        self.wfile.write(b'--frame\r\nContent-Type: image/jpeg\r\nContent-Length: ' + str(len(frame)).encode() + b'\r\n\r\n' + frame + b'\r\n')
                        self.wfile.flush()
                    time.sleep(0.06)
            except (OSError, TimeoutError):
                pass
            finally:
                self.close_connection = True
        else:
            self.send_error(404)

    def do_POST(self):
        # A custom header blocks cross-origin forms and fetches without CORS permission.
        if self.headers.get('X-Butterfly-Control') != '1' or not self.allowed_host():
            self.send_error(403)
            return
        origin = self.headers.get('Origin')
        if origin and origin not in (f'http://localhost:{self.server.server_port}', f'http://127.0.0.1:{self.server.server_port}'):
            self.send_error(403)
            return
        if self.path == '/api/start':
            self.server.controller.start()
        elif self.path == '/api/stop':
            self.server.controller.stop()
        else:
            self.send_error(404)
            return
        self.send_bytes(json.dumps(self.server.controller.snapshot()).encode(), 'application/json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('serial_port', nargs='?')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    controller = Controller(args.serial_port)
    server = Server(('127.0.0.1', args.port), Handler)
    server.controller = controller
    print(f'Butterfly: http://localhost:{server.server_port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        controller.close()
        server.server_close()


if __name__ == '__main__':
    main()
