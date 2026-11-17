// ---------------------------------------------------------------------------------------------
// Project : Kinetic Butterfly Dome (hemisphere with flapping butterflies, single servo)
// Author  : Yuwen Wang
// Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed,
//           tested and adjusted by the author. Uses the standard Arduino "Servo" library
//           (https://docs.arduino.cc/libraries/servo/).
// ---------------------------------------------------------------------------------------------
// Butterfly dome v2 - one servo + line spool, all wings flap together.
// Wiring: servo orange -> D9, red -> 5V, brown -> GND.
//
// Works on its own (flaps every few seconds) and also listens to the computer (hand_v2.py):
//   'G'        -> flap FLAPS_PER_GESTURE times
//   'A<0-100>' -> wings follow your hand: 0 = open (flat), 100 = closed   e.g. "A50\n"
//   'Z'        -> open and stay

#include <Servo.h>

// ---------------- settings ----------------
const int  REST_DEG   = 90;     // servo angle with wings flat (tie the lines at this angle)
const int  FLAP_DEG   = 45;     // how far to turn to close the wings (45 = full close)
const int  DIR        = +1;     // if the wings do not close (lines unwind), change to -1
const int  FLAP_MS    = 700;    // time to close (and again to open); bigger = slower, softer
const int  FLAPS_PER_GESTURE = 3;
const bool AUTO_PLAY  = true;   // flap by itself when nothing comes from the computer
const unsigned long AUTO_EVERY_MS = 6000;
// ------------------------------------------

Servo s;
float cur = REST_DEG;
unsigned long lastCmd = 0, lastAuto = 0;

void moveTo(float target, int ms) {           // smooth, eased move
  float a0 = cur; const int steps = 60;
  for (int i = 1; i <= steps; i++) {
    float t = (float)i / steps, e = 0.5 - 0.5 * cos(PI * t);
    cur = a0 + (target - a0) * e;
    s.write((int)(cur + 0.5));
    delay(ms / steps);
  }
}
float closedAngle(float frac) { return REST_DEG + DIR * FLAP_DEG * frac; }   // frac 0..1

void flap(int n) {
  for (int i = 0; i < n; i++) { moveTo(closedAngle(1), FLAP_MS); delay(120); moveTo(REST_DEG, FLAP_MS); delay(200); }
}

void setup() {
  Serial.begin(115200);
  s.attach(9);
  s.write(REST_DEG); cur = REST_DEG;
  delay(800);
  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read(); lastCmd = millis();
    if (c == 'G') { flap(FLAPS_PER_GESTURE); while (Serial.available()) Serial.read(); Serial.println("DONE"); }
    else if (c == 'A') { int v = Serial.parseInt(); v = constrain(v, 0, 100); moveTo(closedAngle(v / 100.0), 120); }
    else if (c == 'Z') { moveTo(REST_DEG, FLAP_MS); }
  }
  if (AUTO_PLAY && millis() - lastCmd > 10000 && millis() - lastAuto > AUTO_EVERY_MS) {
    flap(2); lastAuto = millis();
  }
}
