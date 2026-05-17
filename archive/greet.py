"""
greet.py
Run with: \greet

Shows a session summary: where you are, nearest base, last session's notes,
phantom risk, and any todos. This is your "what was I doing?" command.

Place in: minescript/greet.py
"""

from minescript import player_position, world_info
from assistant_core import (
    say, say_header, say_dim,
    get_bases, get_notes, get_state,
    nearest_base, distance_2d,
)


def format_pos(pos):
    return f"{int(pos[0])}, {int(pos[1])}, {int(pos[2])}"


def phantom_risk(state, current_day):
    """Returns a string describing phantom risk based on time since last sleep."""
    last_rest_day = state.get("last_rest_day")
    if last_rest_day is None:
        return ("unknown — sleep once to start tracking", "gray")
    days_awake = current_day - last_rest_day
    if days_awake < 3:
        return (f"safe ({days_awake} days awake)", "green")
    elif days_awake < 5:
        return (f"phantoms incoming ({days_awake} days awake)", "yellow")
    else:
        return (f"PHANTOMS ACTIVE ({days_awake} days awake)", "red")


def main():
    pos = player_position()
    info = world_info()
    # world_info() returns a dict; day_ticks gives us in-game day count
    current_day = info.get("day_ticks", 0) // 24000

    bases = get_bases()
    notes = get_notes()
    state = get_state()

    say_header("Welcome back")

    # Position + nearest base
    say(f"Position: {format_pos(pos)}", color="aqua")
    name, dist = nearest_base(pos, bases)
    if name:
        say(f"Nearest base: {name} ({int(dist)}m away)", color="aqua")
    else:
        say_dim("No bases saved yet. Use \\setbase <name> to add one.")

    # Phantom risk
    risk_msg, risk_color = phantom_risk(state, current_day)
    say(f"Phantom risk: {risk_msg}", color=risk_color)

    # Last session log
    log = notes.get("log", [])
    if log:
        last = log[-1]
        say_header("Last session")
        say_dim(f"({last['time']})")
        say(last["text"], color="white")
    else:
        say_dim("No session notes yet. Use \\note <text> to log activity.")

    # Todos
    todos = notes.get("todo", [])
    if todos:
        say_header("Todo")
        for i, item in enumerate(todos, 1):
            say(f"  {i}. {item}", color="yellow")


if __name__ == "__main__":
    main()
