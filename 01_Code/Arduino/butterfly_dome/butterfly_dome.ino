// ---------------------------------------------------------------------------------------------
// Project : Kinetic Butterfly Dome (hemisphere with flapping butterflies, single servo)
// Author  : Yuwen Wang
// Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed,
//           tested and adjusted by the author. Uses the standard Arduino "Servo" library
//           (https://docs.arduino.cc/libraries/servo/).
// ---------------------------------------------------------------------------------------------
// Butterfly dome - one MG90S servo turns the cam drum back and forth.
// Wiring: servo orange -> D9, red -> 5V, brown -> GND (UNO USB powers the board).

#include <Servo.h>

// ---------- settings you can change ----------
const bool HOLD_AT_ZERO = false;    // true = park the servo at 0 deg and stay there (use while tying lines)
const unsigned long SWEEP_MS = 4000; // time for one 0->180 sweep; bigger = slower (3000-6000 looks best)
const unsigned long PAUSE_MS = 1500; // rest between sweeps (butterflies still)
const int US_MIN = 500;             // pulse at 0 deg   - if the servo buzzes at the end, raise to ~600
const int US_MAX = 2400;            // pulse at 180 deg - if it buzzes at the end, lower to ~2300
const int SERVO_PIN = 9;
// ----------------------------------------------

Servo s;

void writeAngle(float a) {
  s.writeMicroseconds(US_MIN + (US_MAX - US_MIN) * a / 180.0);
}

// smooth move from a0 to a1 with ease-in / ease-out
void sweep(float a0, float a1) {
  const int steps = 360;                      // 0.5 deg per step
  for (int i = 0; i <= steps; i++) {
    float t = (float)i / steps;
    float e = 0.5 - 0.5 * cos(PI * t);
    writeAngle(a0 + (a1 - a0) * e);
    delay(SWEEP_MS / steps);
  }
}

void setup() {
  s.attach(SERVO_PIN);
  writeAngle(0);                              // start at rest: every cam on its base circle
  delay(1500);
}

void loop() {
  if (HOLD_AT_ZERO) {                         // assembly mode: stay at 0 deg
    writeAngle(0);
    delay(100);
    return;
  }
  sweep(0, 180);
  delay(PAUSE_MS);
  sweep(180, 0);
  delay(PAUSE_MS);
}
