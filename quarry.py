r"""
quarry.py
Run with:  \quarry <x1> <y1> <z1> <x2> <y2> <z2>

Vanilla-survival quarry. Mines the rectangular box defined by two opposite
corners (inclusive on both ends), one 2-layer pass at a time. Picks the most
efficient tool from your hotbar per block, places a stand-on block if it
falls into an open cave, and warns when your inventory is nearly full.

Before running:
  - Stand at or just above one corner of the volume so the script can get
    there safely. The simplest starting spot is on top of the corner (xmin,
    *, zmin) at any Y above ymax.
  - Have at least one pickaxe in the hotbar. Shovels/axes/shears get used
    automatically when relevant blocks are encountered.
  - Have a stack of filler blocks (cobblestone / cobbled_deepslate / dirt /
    netherrack) somewhere in the hotbar for cave handling.

Stop early with  \killjob  (Minescript's job manager).
"""

import json
import math
import random
import re
import sys
import time

from minescript import (
    echo,
    player,
    player_position,
    player_orientation,
    player_set_orientation,
    player_inventory,
    player_inventory_select_slot,
    player_press_attack,
    player_press_forward,
    player_press_jump,
    player_press_sneak,
    player_press_use,
    player_get_targeted_block,
    getblock,
)


# ===================== Tuning =====================
REACH = 4.5
MAX_BREAK_TIME = 8.0            # seconds spent attacking a single block before giving up
LOOK_STEPS = 2                   # frames over which to smoothly rotate to a target
WALK_TIMEOUT = 4.0               # seconds spent walking to an adjacent cell before giving up
INVENTORY_CHECK_EVERY = 8        # blocks
INVENTORY_WARN_AT = 0.85         # fraction of main inventory used
INVENTORY_HARD_STOP_AT = 0.97
CAVE_PILLAR_MAX = 24             # max blocks to pillar back up out of a cave
HUNGER_EAT_AT = 16               # eat when foodLevel <= this (0-20 scale)
HUNGER_HARD_STOP = 6             # below this and no food = stop (sprint disabled, regen off)
LOOK_SKIP_DEG = 2.5              # if already aimed within this many deg, skip rotating
LOOK_SHORT_DEG = 30.0            # below this delta, use only 2 frames not LOOK_STEPS


# ===================== Block taxonomy =====================
PICKAXE_KEYWORDS = (
    "stone", "cobble", "deepslate", "granite", "andesite", "diorite", "tuff",
    "basalt", "blackstone", "obsidian", "netherrack", "end_stone", "calcite",
    "amethyst", "copper", "concrete", "terracotta", "prismarine", "bricks",
    "ore", "raw_iron", "raw_copper", "raw_gold", "iron_block", "gold_block",
    "diamond_block", "redstone_block", "emerald_block", "lapis_block",
    "anvil", "ice", "packed_ice", "blue_ice",
)
SHOVEL_KEYWORDS = (
    "dirt", "grass_block", "sand", "red_sand", "gravel", "clay", "soul_sand",
    "soul_soil", "mycelium", "podzol", "snow", "mud", "rooted_dirt",
    "coarse_dirt", "farmland", "dirt_path",
)
AXE_KEYWORDS = (
    "log", "planks", "_wood", "stem", "stripped", "fence", "door", "trapdoor",
    "stairs", "barrel", "chest", "crafting_table", "bookshelf", "ladder",
    "sign", "pumpkin", "melon",
)
SHEARS_KEYWORDS = ("leaves", "cobweb", "wool", "vine")

EMPTY_NAMES = {"air", "cave_air", "void_air"}
LIQUID_NAMES = {"water", "flowing_water", "lava", "flowing_lava", "bubble_column"}
HAZARD_NAMES = {"lava", "flowing_lava", "fire", "soul_fire", "magma_block"}
UNBREAKABLE = {"bedrock", "barrier", "command_block", "structure_block"}

TIER_RANK = {
    "netherite": 5, "diamond": 4, "iron": 3, "golden": 2, "stone": 1, "wooden": 0,
}

FILLER_KEYWORDS = (
    "cobblestone", "cobbled_deepslate", "dirt", "netherrack", "stone",
    "andesite", "granite", "diorite", "tuff", "blackstone",
)

# Edibles in preference order (most saturation first; cheap/safe last).
# Excludes anything with side-effects (rotten_flesh, raw_chicken, poisonous_potato, pufferfish, spider_eye, chorus_fruit).
FOOD_PRIORITY = (
    "cooked_porkchop", "cooked_beef", "cooked_mutton", "cooked_chicken",
    "cooked_rabbit", "cooked_salmon", "cooked_cod",
    "baked_potato", "bread", "rabbit_stew", "beetroot_soup", "mushroom_stew",
    "carrot", "beetroot", "apple", "melon_slice", "sweet_berries",
    "glow_berries", "honey_bottle", "dried_kelp", "pumpkin_pie", "cookie",
    "golden_carrot", "golden_apple", "enchanted_golden_apple",
)


# ===================== Helpers =====================
def say(msg, color=None):
    if color:
        echo(json.dumps({"text": msg, "color": color}))
    else:
        echo(msg)


def short(block_str):
    if not block_str:
        return "air"
    s = block_str
    if ":" in s:
        s = s.split(":", 1)[1]
    if "[" in s:
        s = s.split("[", 1)[0]
    return s.lower()


def categorize(block_short):
    if any(k in block_short for k in SHEARS_KEYWORDS):
        return "shears"
    if any(k in block_short for k in AXE_KEYWORDS):
        return "axe"
    if any(k in block_short for k in SHOVEL_KEYWORDS):
        return "shovel"
    if any(k in block_short for k in PICKAXE_KEYWORDS):
        return "pickaxe"
    return "any"


def jsleep(base, jit=0.04):
    t = base + random.uniform(-jit, jit)
    if t > 0:
        time.sleep(t)


def normalize_yaw_delta(d):
    return ((d + 180.0) % 360.0) - 180.0


def yaw_pitch_to(target, eye):
    dx = target[0] - eye[0]
    dy = target[1] - eye[1]
    dz = target[2] - eye[2]
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = math.degrees(math.atan2(-dy, math.hypot(dx, dz)))
    return yaw, pitch


def smooth_look(tx, ty, tz, steps=LOOK_STEPS):
    px, py, pz = player_position()
    eye = (px, py + 1.62, pz)
    target_yaw, target_pitch = yaw_pitch_to((tx, ty, tz), eye)
    cur_yaw, cur_pitch = player_orientation()
    dyaw = normalize_yaw_delta(target_yaw - cur_yaw)
    dpit = target_pitch - cur_pitch
    # Already aimed close enough — don't move the head at all.
    if abs(dyaw) < LOOK_SKIP_DEG and abs(dpit) < LOOK_SKIP_DEG:
        return
    # Small adjustments don't need 3 frames of smoothing.
    eff_steps = steps if (abs(dyaw) + abs(dpit)) > LOOK_SHORT_DEG else 2
    for i in range(1, eff_steps + 1):
        f = i / eff_steps
        player_set_orientation(cur_yaw + dyaw * f, cur_pitch + dpit * f)
        jsleep(0.045, 0.015)


# ===================== Tool / filler selection =====================
_last_selected_slot = None


def hotbar_items(inv):
    return [it for it in inv if it.slot is not None and 0 <= it.slot <= 8]


def tier_of(name_short):
    for prefix, rank in TIER_RANK.items():
        if name_short.startswith(prefix):
            return rank
    return -1


def best_tool_slot(inv, category):
    if category == "any":
        return None
    best_slot, best_tier = None, -1
    for it in hotbar_items(inv):
        nm = short(it.item)
        if category not in nm:
            continue
        t = tier_of(nm)
        if t > best_tier:
            best_tier = t
            best_slot = it.slot
    return best_slot


def equip_for(block_full_name):
    global _last_selected_slot
    cat = categorize(short(block_full_name))
    if cat == "any":
        return
    inv = player_inventory()
    slot = best_tool_slot(inv, cat)
    if slot is None:
        return
    if slot != _last_selected_slot:
        player_inventory_select_slot(slot)
        _last_selected_slot = slot
        jsleep(0.07, 0.02)


def filler_slot():
    inv = player_inventory()
    for it in hotbar_items(inv):
        nm = short(it.item)
        if "ore" in nm:
            continue
        for k in FILLER_KEYWORDS:
            if k in nm:
                return it.slot
    return None


# ===================== Inventory monitoring =====================
_inv_alerted = False


def main_inv_fraction():
    inv = player_inventory()
    used = sum(1 for it in inv if it.slot is not None and 9 <= it.slot <= 35)
    return used / 27.0


def check_inventory():
    global _inv_alerted
    frac = main_inv_fraction()
    if frac >= INVENTORY_WARN_AT and not _inv_alerted:
        say(f"⚠ Inventory {int(frac * 100)}% full — come empty it soon", color="red")
        _inv_alerted = True
    elif frac < INVENTORY_WARN_AT - 0.10:
        _inv_alerted = False
    return frac


# ===================== Hunger =====================
_FOOD_LEVEL_RE = re.compile(r"foodLevel\s*:\s*(\d+)")


def player_food_level():
    """Return current foodLevel (0-20) or None if it couldn't be read."""
    try:
        p = player(nbt=True)
    except Exception:
        return None
    if not getattr(p, "nbt", None):
        return None
    m = _FOOD_LEVEL_RE.search(p.nbt)
    return int(m.group(1)) if m else None


def find_food_slot():
    """Return hotbar slot of the highest-priority safe food, or None."""
    inv = player_inventory()
    best = None
    for it in hotbar_items(inv):
        nm = short(it.item)
        for i, food in enumerate(FOOD_PRIORITY):
            if nm == food:
                if best is None or i < best[0]:
                    best = (i, it.slot)
                break
    return best[1] if best else None


def try_eat():
    """Switch to a food item and eat it. Returns True if eating started."""
    global _last_selected_slot
    slot = find_food_slot()
    if slot is None:
        return False
    # Stop any ongoing actions first.
    player_press_attack(False)
    player_press_forward(False)
    player_inventory_select_slot(slot)
    _last_selected_slot = slot
    # Look slightly down so we don't accidentally use a block in front.
    cur_yaw, _ = player_orientation()
    player_set_orientation(cur_yaw, 60.0)
    jsleep(0.20, 0.05)
    say("Eating…", color="yellow")
    player_press_use(True)
    # Vanilla eat animation is ~1.6s; pad slightly.
    jsleep(1.85, 0.10)
    player_press_use(False)
    jsleep(0.15, 0.04)
    return True


def check_hunger():
    """Check food level; eat if low. Returns 'ok', 'ate', or 'stop'."""
    level = player_food_level()
    if level is None:
        return "ok"
    if level > HUNGER_EAT_AT:
        return "ok"
    ate = try_eat()
    if ate:
        return "ate"
    if level <= HUNGER_HARD_STOP:
        say(f"Food at {level}/20 and no edible food in hotbar — stopping.", color="red")
        return "stop"
    return "ok"


# ===================== Block break / place =====================
def block_at(x, y, z):
    return short(getblock(x, y, z))


def place_below():
    """Place a filler block directly under the player. Returns True if placed."""
    global _last_selected_slot
    slot = filler_slot()
    if slot is None:
        say("Out of filler blocks — can't seal cave.", color="red")
        return False
    player_inventory_select_slot(slot)
    _last_selected_slot = slot
    cur_yaw, _ = player_orientation()
    player_set_orientation(cur_yaw, 89.0)
    jsleep(0.12, 0.04)
    player_press_sneak(True)
    jsleep(0.06, 0.02)
    player_press_use(True)
    jsleep(0.18, 0.04)
    player_press_use(False)
    player_press_sneak(False)
    jsleep(0.05, 0.02)
    return True


def aim_at_block(x, y, z):
    """Equip best tool and aim at the block center. Returns 'ok', 'air', 'skip',
    'hazard', or 'fail' (out of reach / wrong target after look)."""
    name = block_at(x, y, z)
    if name in EMPTY_NAMES:
        return "air"
    if name in UNBREAKABLE:
        return "skip"
    if name in HAZARD_NAMES:
        return "hazard"
    px, py, pz = player_position()
    eye = (px, py + 1.62, pz)
    center = (x + 0.5, y + 0.5, z + 0.5)
    if math.sqrt(sum((eye[i] - center[i]) ** 2 for i in range(3))) > REACH:
        return "fail"
    equip_for(getblock(x, y, z))
    smooth_look(*center)
    tb = player_get_targeted_block(max_distance=REACH + 0.5)
    if tb is None or list(tb.position) != [x, y, z]:
        jsleep(0.06, 0.02)
        tb = player_get_targeted_block(max_distance=REACH + 0.5)
        if tb is None or list(tb.position) != [x, y, z]:
            return "fail"
    return "ok"


def wait_for_break(x, y, z, timeout=MAX_BREAK_TIME):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if block_at(x, y, z) in EMPTY_NAMES:
            return True
        jsleep(0.07, 0.02)
    return False


def mine_block(x, y, z, manage_attack=True):
    """Mine a single block. When `manage_attack` is False, the caller is expected
    to hold `player_press_attack(True)` for the duration — used by row sweeps to
    avoid press/release between every block."""
    status = aim_at_block(x, y, z)
    if status != "ok":
        return status if status in ("air", "skip", "hazard") else "fail"
    if manage_attack:
        player_press_attack(True)
    broken = wait_for_break(x, y, z)
    if manage_attack:
        player_press_attack(False)
        jsleep(0.04, 0.02)
    return "ok" if broken else "fail"


# ===================== Movement =====================
def turn_to_yaw(target_yaw, snap_below_deg=8.0):
    """Rotate to `target_yaw`, keeping pitch. Snaps for tiny corrections, smooths for big turns."""
    cur_yaw, cur_pitch = player_orientation()
    dyaw = normalize_yaw_delta(target_yaw - cur_yaw)
    if abs(dyaw) < 2.0:
        return
    if abs(dyaw) < snap_below_deg:
        player_set_orientation(cur_yaw + dyaw, cur_pitch)
        jsleep(0.04, 0.01)
        return
    steps = 2 if abs(dyaw) < 60 else 3
    for i in range(1, steps + 1):
        f = i / steps
        player_set_orientation(cur_yaw + dyaw * f, cur_pitch)
        jsleep(0.045, 0.015)


def step_forward(target_x=None, target_z=None, timeout=0.7):
    """Brief forward press. Releases when the player crosses near (target_x, target_z) or on timeout.
    Yaw is left to the caller — set it before calling so we walk in the intended direction."""
    player_press_forward(True)
    end = time.time() + timeout
    last_remaining = None
    stall = 0
    while time.time() < end:
        if target_x is not None or target_z is not None:
            px, _, pz = player_position()
            rem = 0.0
            if target_x is not None:
                rem += abs(target_x - px)
            if target_z is not None:
                rem += abs(target_z - pz)
            if rem < 0.35:
                break
            if last_remaining is not None and last_remaining - rem < 0.01:
                stall += 1
                if stall > 4:
                    break
            else:
                stall = 0
            last_remaining = rem
        jsleep(0.05, 0.015)
    player_press_forward(False)


def walk_to(tx, tz, timeout=WALK_TIMEOUT):
    """Walk to (tx, tz). Smoothly aim once, then snap-track while walking forward."""
    # Initial smooth aim toward the target so the start of the walk doesn't snap-rotate.
    px, py, pz = player_position()
    dx, dz = tx - px, tz - pz
    if math.hypot(dx, dz) < 0.5:
        return
    target_yaw0 = math.degrees(math.atan2(-dx, dz))
    cur_yaw, cur_pitch = player_orientation()
    dyaw0 = normalize_yaw_delta(target_yaw0 - cur_yaw)
    # 2-frame turn for any non-trivial angle; 1-frame for small corrections.
    aim_steps = 1 if abs(dyaw0) < 20 else 2
    for i in range(1, aim_steps + 1):
        f = i / aim_steps
        player_set_orientation(cur_yaw + dyaw0 * f, cur_pitch)
        jsleep(0.04, 0.01)

    player_press_forward(True)
    end = time.time() + timeout
    last_dist = None
    stall = 0
    while time.time() < end:
        px, py, pz = player_position()
        dx, dz = tx - px, tz - pz
        dist = math.hypot(dx, dz)
        if dist < 0.50:
            break
        if last_dist is not None and last_dist - dist < 0.01:
            stall += 1
            if stall > 6:
                break
        else:
            stall = 0
        last_dist = dist
        # Snap yaw straight at target — small corrections each tick, no orbiting.
        target_yaw = math.degrees(math.atan2(-dx, dz))
        _, cur_pitch = player_orientation()
        player_set_orientation(target_yaw, cur_pitch)
        jsleep(0.10, 0.02)
    player_press_forward(False)
    jsleep(0.05, 0.02)


def climb_out_of_cave(target_foot_y):
    """Pillar up by placing filler under feet and jumping until feet reach target_foot_y."""
    for _ in range(CAVE_PILLAR_MAX):
        px, py, pz = player_position()
        if int(math.floor(py)) >= target_foot_y:
            return True
        cur_yaw, _ = player_orientation()
        player_set_orientation(cur_yaw, 89.0)
        jsleep(0.10, 0.03)
        slot = filler_slot()
        if slot is None:
            return False
        player_inventory_select_slot(slot)
        global _last_selected_slot
        _last_selected_slot = slot
        player_press_jump(True)
        jsleep(0.12, 0.03)
        player_press_sneak(True)
        player_press_use(True)
        jsleep(0.16, 0.03)
        player_press_use(False)
        player_press_sneak(False)
        player_press_jump(False)
        jsleep(0.10, 0.03)
    return False


# ===================== Quarry =====================
def descend_n(n, ymin):
    """Mine straight down `n` times at the player's current column."""
    for _ in range(n):
        px, py, pz = player_position()
        foot_y = int(math.floor(py))
        target_y = foot_y - 1
        if target_y < ymin:
            return False
        result = mine_block(int(math.floor(px)), target_y, int(math.floor(pz)))
        if result == "hazard":
            say(f"Hazard at ({int(math.floor(px))},{target_y},{int(math.floor(pz))}). Stopping.",
                color="red")
            return False
        if result == "fail":
            jsleep(0.25)
    return True


def quarry(x1, y1, z1, x2, y2, z2):
    xmin, xmax = sorted((x1, x2))
    ymin, ymax = sorted((y1, y2))
    zmin, zmax = sorted((z1, z2))
    width = xmax - xmin + 1
    depth = zmax - zmin + 1
    height = ymax - ymin + 1
    total = width * depth * height
    say(f"Quarry: {width}x{height}x{depth} = {total} blocks "
        f"from ({xmin},{ymin},{zmin}) to ({xmax},{ymax},{zmax}).", color="gold")

    px, py, pz = player_position()
    if py < ymax:
        say(f"Stand at Y >= {ymax} (on or above the volume's top layer) before running. "
            f"You're at Y={py:.1f}.", color="red")
        return

    mined = 0
    skipped = 0
    fails = 0

    # 1) Walk over the start corner.
    walk_to(xmin + 0.5, zmin + 0.5)
    jsleep(0.20, 0.05)

    # 2) Mine straight down until feet at ymax - 1 (i.e., we've removed ymax and ymax-1).
    while True:
        px, py, pz = player_position()
        foot_y = int(math.floor(py))
        if foot_y <= ymax - 1:
            break
        target_y = foot_y - 1
        if target_y < ymin:
            break
        r = mine_block(int(math.floor(px)), target_y, int(math.floor(pz)))
        if r == "hazard":
            say("Hazard during initial descent — aborting.", color="red")
            return
        if r == "ok":
            mined += 1
        elif r == "fail":
            fails += 1
            if fails > 5:
                say("Repeated failures in descent. Aborting.", color="red")
                return
            jsleep(0.20)

    # 3) Layer passes. Each pass mines two layers: head=pass_top, foot=pass_top-1.
    pass_top = ymax
    block_counter = 0
    while pass_top >= ymin:
        pass_bottom = max(ymin, pass_top - 1)
        single_layer = (pass_top == pass_bottom)
        label = f"Y={pass_top}" if single_layer else f"Y={pass_top}-{pass_bottom}"
        say(f"Pass {label}", color="aqua")

        x_list = list(range(xmin, xmax + 1))

        def mine_cell(x, z):
            """Mine head+foot of cell (x, *, z) while attack is held. Returns ('continue'|'stop'|'skip', mined_count)."""
            count = 0
            if not single_layer:
                r = mine_block(x, pass_top, z, manage_attack=False)
                if r == "ok":
                    count += 1
                elif r == "hazard":
                    say(f"Hazard at ({x},{pass_top},{z}) — skipping cell.", color="yellow")
                    return ("skip", count)
            r = mine_block(x, pass_bottom, z, manage_attack=False)
            if r == "ok":
                count += 1
            elif r == "hazard":
                say(f"Hazard at ({x},{pass_bottom},{z}) — skipping cell.", color="yellow")
                return ("skip", count)
            return ("continue", count)

        def step_into_cell(x, z):
            """Walk into (x+0.5, z+0.5). Catches cave-falls and pillars back up.
            Returns True to continue, False to stop the whole job."""
            floor_y = pass_bottom - 1
            floor_name = block_at(x, floor_y, z)
            risky = floor_name in EMPTY_NAMES or floor_name in LIQUID_NAMES
            step_forward(target_x=x + 0.5, target_z=z + 0.5,
                         timeout=0.55 if not risky else 0.45)
            if risky:
                new_y = int(math.floor(player_position()[1]))
                if new_y < pass_bottom:
                    say(f"Fell into cave at ({x},?,{z}). Climbing back.", color="yellow")
                    if not climb_out_of_cave(pass_bottom):
                        say("Couldn't climb back — stopping.", color="red")
                        return False
            return True

        for i, x in enumerate(x_list):
            z_list = list(range(zmin, zmax + 1)) if i % 2 == 0 \
                else list(range(zmax, zmin - 1, -1))
            row_dir_positive_z = z_list[-1] > z_list[0]
            row_yaw = 0.0 if row_dir_positive_z else 180.0

            # Column-step from previous row's last cell to this row's first cell (always +x).
            if i > 0:
                first_z = z_list[0]
                turn_to_yaw(-90.0)  # face +x
                player_press_attack(True)
                try:
                    status, c = mine_cell(x, first_z)
                    mined += c
                    if status == "skip":
                        skipped += 1
                        continue
                finally:
                    player_press_attack(False)
                if not step_into_cell(x, first_z):
                    return
                block_counter += 1

            # Sweep along the row, holding attack the whole way.
            turn_to_yaw(row_yaw)
            player_press_attack(True)
            try:
                for z in z_list:
                    px, _, pz = player_position()
                    if int(math.floor(px)) == x and int(math.floor(pz)) == z:
                        continue  # already standing in this cell
                    status, c = mine_cell(x, z)
                    mined += c
                    if status == "skip":
                        skipped += 1
                        continue
                    # Briefly release attack while stepping so the crosshair doesn't
                    # grind on a partially-broken block during forward motion.
                    player_press_attack(False)
                    advanced = step_into_cell(x, z)
                    player_press_attack(True)
                    if not advanced:
                        return
                    block_counter += 1
                    if block_counter % INVENTORY_CHECK_EVERY == 0:
                        # Pause attack while we check / eat.
                        player_press_attack(False)
                        frac = check_inventory()
                        if frac >= INVENTORY_HARD_STOP_AT:
                            say("Inventory full. Pausing quarry — dump items then "
                                "re-run \\quarry with the same args.", color="red")
                            return
                        if check_hunger() == "stop":
                            return
                        player_press_attack(True)
            finally:
                player_press_attack(False)

        if pass_bottom == ymin:
            break

        # Compute next pass and descend exactly the right number of blocks.
        next_top = pass_top - 2
        next_bottom = max(ymin, next_top - 1)
        descent = pass_bottom - next_bottom
        if descent <= 0:
            break
        if not descend_n(descent, ymin):
            break
        pass_top = next_top

    say(f"✓ Done. Mined {mined}, skipped {skipped}, fails {fails}.", color="green")


# ===================== Entry =====================
def _release_all():
    player_press_attack(False)
    player_press_forward(False)
    player_press_jump(False)
    player_press_sneak(False)
    player_press_use(False)


def main():
    # Accept "x y z x y z" or "x, y, z, x, y, z" — strip commas before parsing.
    args = [a.strip(",") for a in sys.argv[1:] if a.strip(",") != ""]
    if len(args) != 6:
        say("Usage: \\quarry <x1> <y1> <z1> <x2> <y2> <z2>", color="red")
        return
    try:
        coords = [int(a) for a in args]
    except ValueError:
        say("All six coordinates must be integers.", color="red")
        return
    try:
        quarry(*coords)
    except KeyboardInterrupt:
        say("Quarry interrupted.", color="yellow")
    finally:
        _release_all()


if __name__ == "__main__":
    main()
