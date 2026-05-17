"""
slept.py
Run with: \slept

Marks "I just slept" in the state file so phantom risk tracking resets.
Run this right after you sleep in a bed. (Detecting it automatically is
finicky in Minescript, so manual is more reliable.)

Place in: minescript/slept.py
"""

from minescript import world_info
from assistant_core import say, get_state, save_state


def main():
    info = world_info()
    current_day = info.get("day_ticks", 0) // 24000

    state = get_state()
    state["last_rest_day"] = current_day
    save_state(state)

    say(f"Sleep recorded. Phantom timer reset (day {current_day}).", color="green")


if __name__ == "__main__":
    main()
