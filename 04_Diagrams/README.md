# Diagrams

Engineering figures for the Butterfly Dome. They explain how the piece is built and how the motion travels from the servo to the wings. All dimensions are in mm.

**Line colours used throughout:** red = flap line (closes the wings), blue = bob line (raises the butterfly; part of the full design, not used in the as-built flap-only version), grey tube = PTFE sheath.

## One butterfly

| File | What it shows |
|---|---|
| `F1_butterfly_exploded.png` | Exploded view of the wing root: tape hinge, polyester wing, the two acrylic stiffeners (mirror parts) and the printed body, in assembly order. |
| `F2_body_section.png` | Cross-section through the body, open and closed. Pulling the line drags both stiffener arms down, so the wings fold up about 60° around the tape hinge. |
| `F3_module_section.png` | Section through one complete module (body, slider, guide sleeve, sheaths), at rest and raised + closed. |
| `F3b_module_real.png` | The same module as a CAD render, cut open, with every hole and line numbered ①–⑩. |
| `F10_slider.png` | The slider part: rod, centre hole for the flap line, bottom fitting and sheath seat. |
| `F12_repair_sleeve.png` | The repair part printed to replace the #1 guide sleeve, which broke off the dome. |

## Drive in the plinth

| File | What it shows |
|---|---|
| `F4_drive_exploded.png` | Exploded drive on the floor plate: servo → cam drum → 12 rockers on a Ø2 rod, with the assembly order. |
| `F5_drive_assembled.png` | The same drive assembled at servo 0°, with one line rising from each rocker tip. |
| `F8_rocker_line.png` | Side view of one rocker: cam, Ø2 axle, rocker tip and sheath seat. Large butterflies use 1 line per rocker; small ones use 4 lines through a splitter. |
| `F11_drum_ends.png` | How the cam drum is held: servo horn at one end, a free-turning stub shaft in a low support at the other. |
| `V1_drive_render.png` | Render of the whole drive inside the plinth, with the shell removed. |

## Layout and timing

| File | What it shows |
|---|---|
| `F6_dome_map.png` | Top view of where the 12 butterflies (full design) sit on the dome, and which way each head points. |
| `F7_seat_map.png` | The 24 sheath seats in the plinth top plate, and which rocker and function (B = bob, F = flap) each one belongs to. |
| `V1_cam_profiles.png` | The 12 cam disc profiles. The bump on each disc decides when its rocker pulls. Includes print settings for the drum. |
| `V1_timing_chart.png` | When each cam pulls during a 0→180° sweep. The overlapping flap windows make the travelling wave. |
| `V1_overview_render.png` | Render of the full design: at rest, mid-sweep (servo at 70°), and from above. |

## Electronics

| File | What it shows |
|---|---|
| `F9_wiring.png` | Wiring: servo signal to D9, power and ground, optional external 5 V supply and capacitor. In the final piece the servo runs from the UNO's 5 V pin over USB. |

## v2 redesign (not built)

| File | What it shows |
|---|---|
| `V2_A_inside.png` | The simplified concept: one servo with a two-tier spool reels in all 7 lines at once, with no cams or rockers. |
| `V2_map.png` | Top view of the 7 butterfly positions in v2. |

The laser cut previews are in `../03_LaserCut/` (`preview_*.png`).
