"""
radar.py
Run with: \radar [radius]

One-shot scan for hostile mobs around you. Default radius 32 blocks.
Useful before AFK farming or when you hear something nearby.

Place in: minescript/radar.py
"""

import sys
from minescript import player_position, entities
from assistant_core import say, say_header, say_dim, distance_3d


HOSTILE_TYPES = {
    "zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman",
    "witch", "pillager", "vindicator", "evoker", "ravager", "vex",
    "phantom", "drowned", "husk", "stray", "wither_skeleton", "blaze",
    "ghast", "magma_cube", "slime", "piglin", "piglin_brute", "hoglin",
    "zoglin", "zombified_piglin", "guardian", "elder_guardian", "shulker",
    "warden", "breeze", "bogged",
}


def is_hostile(entity):
    name = entity.get("name", "") or entity.get("type", "")
    # Minescript entity names are usually like "minecraft:zombie" or just "zombie"
    short = name.split(":")[-1].lower()
    return short in HOSTILE_TYPES


def main():
    radius = 32
    if len(sys.argv) > 1:
        try:
            radius = int(sys.argv[1])
        except ValueError:
            pass

    pos = player_position()
    all_entities = entities()

    threats = []
    for e in all_entities:
        if not is_hostile(e):
            continue
        epos = e.get("position") or [e.get("x", 0), e.get("y", 0), e.get("z", 0)]
        d = distance_3d(pos, epos)
        if d <= radius:
            short = (e.get("name") or e.get("type", "?")).split(":")[-1]
            threats.append((short, d, epos))

    if not threats:
        say(f"All clear within {radius} blocks.", color="green")
        return

    threats.sort(key=lambda t: t[1])
    say_header(f"Threats within {radius}m ({len(threats)})")
    for name, d, epos in threats[:10]:
        say(f"  {name} — {int(d)}m at {int(epos[0])}, {int(epos[1])}, {int(epos[2])}", color="red")
    if len(threats) > 10:
        say_dim(f"  ...and {len(threats) - 10} more")


if __name__ == "__main__":
    main()
