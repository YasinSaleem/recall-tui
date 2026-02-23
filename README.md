# Recall - LeetCode Practice TUI

A terminal-based spaced repetition system for LeetCode problems.

## Features

- **Spaced Repetition**: Automatically schedules problem reviews based on performance
- **Timer**: Track solve times for each problem
- **Test Mode**: Practice with 3 random encrypted problems and track total time
- **Stats**: View progress and mastery status
- **Search**: Filter problems by title or topic

## Setup

```bash
# Install dependencies and create virtual environment
uv sync

# Run
uv run main.py
```

## Usage

| Key | Action |
|-----|--------|
| `a` | Add new problem |
| `o` | Open URL & start timer |
| `r` | Mark problem as reviewed |
| `l` | Toggle Due / All view |
| `s` | Toggle stats panel |
| `t` | Enter Test Mode |
| `h` | Show help |
| `q` | Quit |

## Project Structure

```
recall-tui/
├── main.py           # Entry point
├── recall/           # Package
│   ├── app.py        # Main application
│   ├── screens.py    # UI screens & modals
│   ├── database.py   # Data persistence
│   ├── constants.py  # Configuration
│   └── crypto.py     # Encryption utilities
├── tui.css           # Styles
└── pyproject.toml    # Project config
```
