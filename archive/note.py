"""
note.py
Run with:
  \note <text>           - append to session log (shown on next \greet)
  \note todo <text>      - add a todo item
  \note done <number>    - remove a todo by its number from \greet
  \note clear            - clear the session log (keeps todos)

Place in: minescript/note.py
"""

import sys
from assistant_core import say, say_dim, get_notes, save_notes, timestamp


def main():
    args = sys.argv[1:]
    notes = get_notes()

    if not args:
        say("Usage: \\note <text> | \\note todo <text> | \\note done <#> | \\note clear", color="red")
        return

    sub = args[0].lower()

    if sub == "todo" and len(args) > 1:
        item = " ".join(args[1:])
        notes.setdefault("todo", []).append(item)
        save_notes(notes)
        say(f"Todo added: {item}", color="yellow")

    elif sub == "done" and len(args) > 1:
        try:
            idx = int(args[1]) - 1
            todos = notes.get("todo", [])
            if 0 <= idx < len(todos):
                removed = todos.pop(idx)
                save_notes(notes)
                say(f"Done: {removed}", color="green")
            else:
                say(f"No todo #{idx + 1}", color="red")
        except ValueError:
            say("Usage: \\note done <number>", color="red")

    elif sub == "clear":
        notes["log"] = []
        save_notes(notes)
        say_dim("Session log cleared.")

    else:
        # Plain note - append to log
        text = " ".join(args)
        notes.setdefault("log", []).append({"time": timestamp(), "text": text})
        # Keep last 10 entries to prevent runaway growth
        notes["log"] = notes["log"][-10:]
        save_notes(notes)
        say(f"Logged: {text}", color="green")


if __name__ == "__main__":
    main()
