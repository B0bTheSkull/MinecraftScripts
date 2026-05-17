"""
bases.py
Run with: \bases

Lists all saved bases with their coordinates and current distance.

Place in: minescript/bases.py
"""

from minescript import player_position
from assistant_core import say, say_header, say_dim, get_bases, distance_2d


def main():
    bases = get_bases()
    if not bases:
        say_dim("No bases saved. Use \\setbase <name> to add one.")
        return

    pos = player_position()
    say_header(f"Bases ({len(bases)})")

    # Sort by distance, closest first
    items = sorted(bases.items(), key=lambda kv: distance_2d(pos, kv[1]))
    for name, coords in items:
        d = int(distance_2d(pos, coords))
        say(f"  {name}: {coords[0]}, {coords[1]}, {coords[2]} ({d}m)", color="aqua")


if __name__ == "__main__":
    main()
