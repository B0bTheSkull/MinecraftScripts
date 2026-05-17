# Minecraft Assistant Bot (Minescript)

A modular personal assistant for survival Minecraft. Tracks bases, logs session notes,
warns about phantoms, and scans for nearby threats.

## Install

1. Copy all `.py` files into your Minescript folder (usually
   `.minecraft/minescript/` on Linux).
2. Reload scripts in-game with `\reload` (or just relog).
3. The first run of any command auto-creates the `assistant_data/` folder
   for persistent state.

## Commands

| Command | What it does |
|---|---|
| `\greet` | Session summary: position, nearest base, phantom risk, last note, todos |
| `\setbase <name>` | Save current position as a named base |
| `\bases` | List all bases sorted by distance from you |
| `\note <text>` | Log activity (shown next time you `\greet`) |
| `\note todo <text>` | Add a todo item |
| `\note done <#>` | Remove todo by number |
| `\note clear` | Wipe the session log |
| `\slept` | Reset phantom timer (run after sleeping in a bed) |
| `\radar [radius]` | Scan for hostile mobs (default 32 blocks) |

## Typical workflow

```
[log in]
\greet                                    → "ah right, I was mining diamonds"
\note finishing the branch mine at -250,-58,400
\setbase diamond_mine
[play for an hour]
\radar 50                                 → before going AFK
\slept                                    → after sleeping
\note todo build a rail back from diamond mine
[log out]
[next session]
\greet                                    → reminded of everything
```

## Files

- `assistant_core.py` — shared utilities, JSON state, formatting
- `greet.py` — main session summary
- `setbase.py` / `bases.py` — base management
- `note.py` — log + todos
- `slept.py` — phantom timer reset
- `radar.py` — hostile mob scanner

State is stored in `minescript/assistant_data/`:
- `bases.json`, `farms.json`, `notes.json`, `state.json`

## Coming soon (next iteration)

- **Farm checker** — register chests, get fullness % on `\greet`
- **Auto-radar** — long-running script that pings you when threats appear
- **Nether portal mapper** — overworld ↔ nether coord conversion for portal placement
```
