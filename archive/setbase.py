"""
setbase.py
Run with: \setbase <name>

Saves your current position as a named base. Overwrites if name exists.

Place in: minescript/setbase.py
"""

import sys
from minescript import player_position
from assistant_core import say, get_bases, save_bases


def main():
    if len(sys.argv) < 2:
        say("Usage: \\setbase <name>", color="red")
        return

    name = " ".join(sys.argv[1:]).strip()
    pos = player_position()
    coords = [int(pos[0]), int(pos[1]), int(pos[2])]

    bases = get_bases()
    existed = name in bases
    bases[name] = coords
    save_bases(bases)

    verb = "Updated" if existed else "Saved"
    say(f"{verb} base '{name}' at {coords[0]}, {coords[1]}, {coords[2]}", color="green")


if __name__ == "__main__":
    main()
