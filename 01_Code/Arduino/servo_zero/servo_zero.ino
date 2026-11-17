// ---------------------------------------------------------------------------------------------
// Project : Kinetic Butterfly Dome (hemisphere with flapping butterflies, single servo)
// Author  : Yuwen Wang
// Credits : Written with the help of Claude (Anthropic, AI assistant), Nov 2026; reviewed,
//           tested and adjusted by the author. Uses the standard Arduino "Servo" library
//           (https://docs.arduino.cc/libraries/servo/).
// ---------------------------------------------------------------------------------------------
// servo_zero - assembly helper.
// Moves the servo to about 90 deg (so you can see it move), then back to 0 deg and HOLDS it there.
// Use it while fitting the horn to the cam drum and while tying the lines: at 0 deg every cam
// shows its smooth base circle to the rockers, i.e. all butterflies are at rest.
// Wiring: servo orange -> D9, red -> 5V, brown -> GND.

#include <Servo.h>
Servo s;

const int US_0  = 500;    // pulse width for 0 deg (raise to ~600 if the servo buzzes at this end)
const int US_90 = 1450;   // roughly 90 deg, only used for the visible "check" move

void setup() {
  s.attach(9);
  s.writeMicroseconds(US_90);   // visible move first, so you know the servo responds
  delay(1000);
  s.writeMicroseconds(US_0);    // then rest position
}

void loop() {
  s.writeMicroseconds(US_0);    // keep holding 0 deg while USB power is connected
  delay(100);
}
