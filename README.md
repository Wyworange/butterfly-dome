# Kinetic Butterfly Dome — Project Files

A Ø150 mm hemisphere covered with laser-cut butterflies whose wings open and close.
One MG90S servo drives every butterfly through a 3D-printed cam drum, rockers and PTFE-sheathed
lines (v1, the version that was built). A webcam gesture (fist, then open hand) starts the motion,
through a small local web page (`01_Code/Python/web`).
Full system description (layers, diagrams, serial protocol, channel map): **`SYSTEM.md`**.
Folder `02_CAD/v2_simplified_redesign` contains a simpler follow-up design (not built).

Author: Yuwen Wang · AI assistance: Claude (Anthropic) — see *Credits* at the end.

---

## Folder map

```
01_Code/
  Arduino/
    butterfly_dome/        main sketch: smooth 0->180->0 sweeps of the cam drum (v1)
    butterfly_dome_cv/     same drive, but waits for a "G" command from the gesture script
    servo_zero/            assembly helper: parks the servo at 0 deg (rest) and holds it
    servo_sweep_test/      simple 0<->180 test to check the drum / rockers
    butterfly_v2/          sketch for the v2 redesign (single servo + line spool)
  Python/
    web/hand_web.py        USED IN THE FINAL PIECE: local web server, webcam gesture -> 'G' to the Arduino
    web/index.html         USED IN THE FINAL PIECE: the gesture control page (http://localhost:8765)
    hand_trigger.py        gesture logic (also runs alone as a desktop camera window) (v1)
    hand_v2.py             webcam for v2: wings follow the hand, or fist->open trigger
    requirements.txt
02_CAD/
  v1_as_built/
    STEP/                  editable solids of every printed part
    STL/                   the same parts as meshes (+ REPAIR_sleeve_1 used to fix the top sleeve)
    print_plates_3MF/      Bambu Studio plates actually printed (Bambu H2D)
    line_table.txt         which rocker / sheath seat drives which butterfly (full design + as-built note)
  v2_simplified_redesign/  STEP + STL + one-plate 3MF for the simplified version
  source_scripts/          the Python (CadQuery) scripts that generate all of the above
03_LaserCut/               wings (0.18 mm polyester film) and wing stiffeners (1/16" clear acrylic):
                           .ai / .pdf / .svg / .dxf, 1:1 in mm. RED hairline = cut, BLUE = engrave
04_Diagrams/               renders, sections, exploded views, maps, wiring diagram (see 04_Diagrams/README.md)
```

---

## How it works (v1, as built)

| Stage | Part | What it does |
|---|---|---|
| 1 | MG90S servo (`P0_floor` saddle) | sweeps 0° → 180° → 0° |
| 2 | Cam drum `C_cam_drum` (12 discs, one piece) | each disc has its own bump at its own angle |
| 3 | 12 rockers `R_rocker` on a Ø2 mm steel axle | a bump lifts the short arm → the long arm pulls its line down |
| 4 | PE line inside a PTFE sheath (1 × 2 mm) | carries the pull from the plinth to the butterfly, around any curve (Bowden cable) |
| 5 | Slider `S01–S12` + body `K_body_*` | the line runs up the slider's Ø1.6 bore to a Y-thread on the two wing arms |
| 6 | Wings + acrylic stiffeners, tape hinge | arms pulled down → wings fold up to 60°; released → gravity / tape hinge reopen them |

The original design also lets every butterfly bob 12 mm on its slider (blue "bob" lines, U-groove,
return spring). In the final build only the wing motion is used: 4 large + 3 medium butterflies on
rockers 2, 4, 6, 8 (large) and 9, 10 (medium). See `04_Diagrams/F3_module_section.png`,
`F5_drive_assembled.png`, `F7_seat_map.png`, `F8_rocker_line.png`, `V1_timing_chart.png`.

Key numbers: dome R75 mm, wall 2.5 mm · plinth Ø150 × 50 mm · line pull 6.3 mm (large) / 3.55 mm
(medium: 3.15 mm needed + 0.4 mm margin) for a 60° wing fold · peak servo load ≈ 97 N·mm (MG90S ≈ 176 N·mm).

---

## Bill of materials (v1)

| Item | Qty |
|---|---|
| Arduino UNO + USB cable | 1 |
| MG90S metal-gear servo | 1 |
| 5 V ≥ 2 A supply (optional; UNO 5 V is enough for flap-only) + 1000 µF capacitor (optional) | 1 |
| PE braided line 0.10–0.26 mm | ~8 m |
| PTFE tube 1 mm ID × 2 mm OD | ~3.2 m |
| Ø2 mm steel rod, 48 mm (rocker axle) | 1 |
| M2 × 8 self-tapping screws / M3 × 6 (UNO) | 8 / 4 |
| Clear 1/16" acrylic sheet, white 0.18 mm polyester film | 1 each |
| Clear tape (wing hinges), thin double-sided tape, CA glue | — |
| PLA filament | ~0.5 kg |

---

## Running the code

**Arduino** (Arduino IDE, board "Arduino Uno"): each sketch sits in a folder of the same name.
Wiring for all sketches: servo **orange → D9, red → 5V, brown → GND** (`04_Diagrams/F9_wiring.png`).

1. Upload `servo_zero` while assembling: the servo holds 0° (all butterflies at rest).
2. Upload `servo_sweep_test` to check that the rocker tips dip one after another.
3. Upload `butterfly_dome` for the installation. Speed: `SWEEP_MS`; pause: `PAUSE_MS`.
   If the drum turns the wrong way, swap `US_MIN` and `US_MAX`.

**Gesture control (as used in the final piece):** upload `butterfly_dome_cv`, close the Serial Monitor, then on the computer

```
pip install -r 01_Code/Python/requirements.txt      # Python 3.9 - 3.12
python 01_Code/Python/web/hand_web.py               # or: python hand_web.py /dev/cu.usbmodem1101
```

Open http://localhost:8765, click **Turn on camera**, make a fist, then open the hand within 2 seconds
→ one full butterfly cycle. `Ctrl+C` in the terminal stops the server.
Without the browser, `python 01_Code/Python/hand_trigger.py` does the same in a desktop window (`q` quits).

---

## Fabrication notes

* **3D printing (Bambu H2D, PLA, 0.2 mm):** use the plates in `print_plates_3MF`.
  The dome needs PLA tree supports inside; set support filament to *Default* (no prime tower).
  Remove supports around the sleeves gently — the top sleeve broke off once and was replaced by
  `REPAIR_sleeve_1.stl` (glued, aligned with a slider and two threads).
* **Laser cutting:** wings from 0.18 mm polyester film, every web ≥ 2.5 mm (pattern derived from the
  author's original butterfly Illustrator artwork); stiffeners from 1/16" clear acrylic, left and right are
  mirror parts. Tie the Y-thread around each stiffener arm on the blue engraved line.
* Full step-by-step assembly guide (with all figures):
  https://claude.ai/artifact/M9ThvzeQb9rukW1wdeao7F

## v2 simplified redesign (not built)

One servo in the middle of a new base turns a two-step line spool (r 8 mm for large, r 4 mm for medium
butterflies; 45° of servo travel closes all wings together). No cam drum, rockers or sheaths; butterflies sit
on short pegs pushed through the dome from inside. Files: `02_CAD/v2_simplified_redesign`,
`01_Code/Arduino/butterfly_v2`, `01_Code/Python/hand_v2.py`, `04_Diagrams/V2_*.png`.

---

## Credits / sources

* Concept, butterfly artwork, fabrication, assembly and testing: Yuwen Wang.
* CAD generation scripts, mechanism calculations, Arduino and Python code, diagrams and the assembly
  guide were developed with the help of **Claude (Anthropic), an AI assistant**, and were reviewed,
  tested and modified by the author.
* Libraries: Arduino Servo library; CadQuery (CAD); trimesh, shapely, manifold3d, ezdxf, matplotlib,
  reportlab (geometry / file export); Google MediaPipe Hands; OpenCV; pySerial.
* Inspiration: Iris van Herpen's kinetic, lace-like butterfly pieces.
