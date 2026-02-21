# Feature Roadmap

## High Priority

### [ ] Help Popup (`h`)
Translucent modal showing all keybindings.
- Press `h` to toggle help popup
- Remove keybind definitions from the sidebar (cleaner UI)
- Popup should be semi-transparent overlay

### [ ] Edit Problem
Ability to edit a problem's title, difficulty, topic, and URL after logging.
- Press `e` on selected problem to open edit modal
- Useful for fixing typos or adding a URL later

### [ ] Undo Last Review
Revert the most recent review action in case of accidental `r` press.
- Press `u` to undo last review
- Store last action in memory (session-based, no persistence needed)

### [ ] Review Interval Types
Let users select a review schedule when logging a problem based on perceived difficulty.
- Dropdown in Add Modal with options like: "Standard", "Tricky" (more frequent), "Easy" (less frequent)
- Actual intervals hardcoded in `database.py`, not exposed in UI
- Example schemas:
  - Standard: 1, 3, 7, 21, 30 (current)
  - Tricky: 1, 2, 4, 7, 14, 21, 30 (more reviews early)
  - Easy: 3, 7, 30 (fewer reviews total)

### [ ] Copy Title (`c`)
Copy selected problem's title to clipboard.
- Press `c` to copy title
- Useful for pasting into Obsidian or searching elsewhere

## Medium Priority

### [ ] Topic Filter
Dedicated filter by topic (not just text search).
- Dropdown or keybind to filter table by specific topic
- Helps with focused practice sessions (e.g., "only DP today")

### [ ] Upcoming Reviews
Show preview of reviews coming in next 7 days.
- Display in stats panel: "Next 7 days: 12 problems due"
- Helps anticipate busy review days

## Nice to Have

### [ ] Delete Problem
Remove a problem entirely from the database.
- Press `d` with confirmation
- Currently requires manual JSON editing
