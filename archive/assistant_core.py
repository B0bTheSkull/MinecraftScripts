"""
assistant_core.py
Shared utilities for the Minecraft assistant bot.
Place in: minescript/assistant_core.py (alongside your other scripts)

All other assistant scripts import from this. Handles persistent JSON state,
coordinate math, and consistent chat formatting.
"""

import json
import os
from datetime import datetime
from minescript import echo, player_position

# ---- Paths ----
# Minescript scripts run with cwd at the minescript folder, so relative paths work.
DATA_DIR = "assistant_data"
BASES_FILE = os.path.join(DATA_DIR, "bases.json")
FARMS_FILE = os.path.join(DATA_DIR, "farms.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.json")
STATE_FILE = os.path.join(DATA_DIR, "state.json")  # rolling state (last_rest_tick, etc)


def _ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)


def load_json(path, default):
    """Load a JSON file, returning `default` if missing or corrupt."""
    _ensure_data_dir()
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    _ensure_data_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ---- Convenience accessors ----
def get_bases():
    return load_json(BASES_FILE, {})

def save_bases(bases):
    save_json(BASES_FILE, bases)

def get_farms():
    return load_json(FARMS_FILE, [])

def save_farms(farms):
    save_json(FARMS_FILE, farms)

def get_notes():
    return load_json(NOTES_FILE, {"log": [], "todo": []})

def save_notes(notes):
    save_json(NOTES_FILE, notes)

def get_state():
    return load_json(STATE_FILE, {})

def save_state(state):
    save_json(STATE_FILE, state)


# ---- Coordinate helpers ----
def distance_2d(a, b):
    """Horizontal distance between two (x, y, z) points. Ignores Y."""
    return ((a[0] - b[0]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5

def distance_3d(a, b):
    return sum((a[i] - b[i]) ** 2 for i in range(3)) ** 0.5

def nearest_base(pos, bases):
    """Returns (name, distance) of the nearest known base, or (None, None)."""
    if not bases:
        return None, None
    best_name, best_dist = None, float("inf")
    for name, coords in bases.items():
        d = distance_2d(pos, coords)
        if d < best_dist:
            best_name, best_dist = name, d
    return best_name, best_dist


# ---- Chat formatting ----
# Minescript's echo() supports JSON text components for colors. Keep it simple.
def say(msg, color=None):
    """Print to chat. Optionally colored ('gold', 'aqua', 'red', 'green', 'gray', 'yellow')."""
    if color:
        echo(json.dumps({"text": msg, "color": color}))
    else:
        echo(msg)

def say_header(title):
    say(f"━━━ {title} ━━━", color="gold")

def say_dim(msg):
    say(msg, color="gray")

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M")
