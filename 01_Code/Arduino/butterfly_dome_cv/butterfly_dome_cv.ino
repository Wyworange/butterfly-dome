// ---------------------------------------------------------------------------------------------
// Project : Kinetic Butterfly Dome (hemisphere with flapping butterflies, single servo)
// Author  : Yuwen Wang
// Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed,
//           tested and adjusted by the author. Uses the standard Arduino "Servo" library
//           (https://docs.arduino.cc/libraries/servo/).
// ---------------------------------------------------------------------------------------------
// Butterfly dome - gesture controlled.
// Waits at 0 deg. When the computer sends 'G' over USB serial, it plays one cycle 0 -> 180 -> 0
// and replies "DONE". Wiring: servo orange -> D9, red -> 5V, brown -> GND.

#include <Servo.h>

// ---------- settings ----------
const unsigned long SWEEP_MS = 4000;   // time for 0->180 (and again for 180->0); bigger = slower
const unsigned long HOLD_MS  = 600;    // pause at 180 before coming back
int US_MIN = 500;                      // pulse at "0 deg"   (if the drum turns the wrong way, swap these two:
int US_MAX = 2400;                     // pulse at "180 deg"  US_MIN = 2400; US_MAX = 500;)
const int SERVO_PIN = 9;
// ------------------------------

Servo s;
bool busy = false;

void writeAngle(float a) {
  s.writeMicroseconds(US_MIN + (US_MAX - US_MIN) * a / 180.0);
}

void sweep(float a0, float a1) {
  const int steps = 360;
  for (int i = 0; i <= steps; i++) {
    float t = (float)i / steps;
    float e = 0.5 - 0.5 * cos(PI * t);         // ease in / ease out
    writeAngle(a0 + (a1 - a0) * e);
    delay(SWEEP_MS / steps);
  }
}

void setup() {
  Serial.begin(115200);
  s.attach(SERVO_PIN);
  writeAngle(0);                                // rest: all butterflies flat
  Serial.println("READY");
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == 'G' && !busy) {                    // one full cycle
      busy = true;
      Serial.println("START");
      sweep(0, 180);
      delay(HOLD_MS);
      sweep(180, 0);
      while (Serial.available()) Serial.read(); // ignore gestures that arrived while moving
      busy = false;
      Serial.println("DONE");
    } else if (c == 'Z') {                      // park at 0
      writeAngle(0);
    }
  }
}
