// ---------------------------------------------------------------------------------------------
// Project : Kinetic Butterfly Dome (hemisphere with flapping butterflies, single servo)
// Author  : Yuwen Wang
// Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed,
//           tested and adjusted by the author. Uses the standard Arduino "Servo" library
//           (https://docs.arduino.cc/libraries/servo/).
// ---------------------------------------------------------------------------------------------
// servo_sweep_test - checks the drive without the eased motion of the main sketch.
// Sweeps 0 -> 180 -> 0 deg in small steps and pauses at both ends. Watch the rocker tips:
// they should dip one after another. If none of them move, the drum turns the wrong way
// (swap US_MIN / US_MAX in butterfly_dome.ino and re-seat the drum at the other end).

#include <Servo.h>
Servo s;

const int US_0   = 500;    // 0 deg
const int US_180 = 2400;   // 180 deg (lower to ~2300 if the servo buzzes at the end)
const int STEP_MS = 10;    // delay per 5 us step: bigger = slower (10 -> about 4 s per sweep)

void setup() {
  s.attach(9);
  s.writeMicroseconds(US_0);
  delay(1500);
}

void loop() {
  for (int us = US_0; us <= US_180; us += 5) { s.writeMicroseconds(us); delay(STEP_MS); }  // 0 -> 180
  delay(1500);
  for (int us = US_180; us >= US_0; us -= 5) { s.writeMicroseconds(us); delay(STEP_MS); }  // 180 -> 0
  delay(1500);
}
