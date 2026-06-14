# minescript

Personal [Minescript](https://minescript.net/) Python scripts for Minecraft.
These run inside Minecraft via the Minescript mod, automating in-game tasks
through the Minescript API.

## Scripts

- **quarry.py** — Vanilla-survival quarry. Mines the rectangular box defined by
  two opposite corners, picking the best tool per block, placing stand-on
  blocks over caves, and warning when the inventory is nearly full.
  Run in-game with `\quarry <x1> <y1> <z1> <x2> <y2> <z2>`.
- **visual.py** — Local matplotlib helper for visualizing block grids
  (not run in-game).
- **test.py** — Scratch/test script.
- **archive/** — Older scripts kept for reference.
- **system/** — Minescript runtime and library files.

## Configuration

`config.txt` points Minescript at the Python interpreter to use.
