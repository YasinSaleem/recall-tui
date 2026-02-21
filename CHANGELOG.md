# Changelog

## [Unreleased]

### Added
- **Solve Timer** - Track solve times for problems
  - Press `o` to open a problem URL and start a 2-second countdown
  - After countdown, timer begins in MM:SS format
  - Modal blocks all other TUI functionality while active
  - **Stop** button: Records time if it's a new best
  - **Cancel** button: Discards the time
  - Best times displayed in new "Best" column in problem table
  - Notifications show when a new best time is set

---

## v0.1.0 (2026-02-21)

### Added
- **Problem Management**
  - Add new problems with title, difficulty, topic, and URL
  - Track problem difficulty (Easy, Medium, Hard)
  - Track topics (Arrays & Hashing, Two Pointers, Linked List, Sliding Window, Stack, Binary Search, Trees, Heap / Priority Queue, Backtracking, Graphs, Dynamic Programming)
  - Store problem URLs for quick access

- **Spaced Repetition System**
  - Automatic review scheduling (0, 1, 3, 7, 21, 30 day intervals)
  - Progress tracking with visual progress bar per problem
  - "Mastered" status for problems that complete all intervals
  - Due date tracking for problems

- **TUI Interface**
  - Split-pane layout with problem list and stats
  - DataTable with sortable columns (Title, Diff, Topic, Progress, Best, Next Review/Status)
  - Search/filter problems by title or topic
  - Toggle between "Due" and "All" problem views
  - Header with clock display
  - Help text showing all keyboard controls

- **Keyboard Controls**
  - `a` - Add new problem
  - `r` - Mark problem as reviewed (advance spaced repetition)
  - `x` - Reset problem progress
  - `o` - Open problem URL (with timer)
  - `enter` - Open problem URL (with timer)
  - `l` - Toggle between Due/All view
  - `s` - Toggle stats panel
  - `ctrl+f` - Focus search box
  - `q` - Quit application

- **Data Persistence**
  - JSON-based local database (recall_db.json)
  - Automatic saving of all problem data
