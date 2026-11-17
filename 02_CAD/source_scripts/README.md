# CAD source scripts

Python (CadQuery) scripts that generate every part from parameters. Developed with the help of
Claude (Anthropic, AI assistant); reviewed by the author.

v1/   dp.py          all parameters (dome, sliders, drive, cam schedule)
      lay.py         butterfly layout on the dome (positions, clearances); layout.json = result
      kin.py         rocker kinematics, line pull and servo torque check
      cams.py        cam profiles and rocker outline
      dome_cad.py    builds dome, plinth, floor, cam drum, rockers, sliders, bodies -> out/*.step/.stl
      plates.py      arranges the parts into Bambu 3MF print plates
      body.py, params.py   butterfly body base geometry (scaled per size)
laser/ wings_ai.py   reads the wing outlines from the original Illustrator file
       minweb.py     keeps every web of the lace pattern >= 2.5 mm
       stiff_acr.py  acrylic stiffener geometry (min feature 2.5 mm), left/right mirror parts
       export_ai.py  writes the .ai/.pdf/.svg/.dxf cut sheets
v2/    cad2.py, dome_mesh.py   simplified redesign (dome, pegs, base, spool)

Paths at the top of the scripts point to the original working folders and need adjusting to rerun.
