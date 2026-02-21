from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Header,
    Footer,
    DataTable,
    Static,
    Button,
    Input,
    Label,
    Select,
)
from textual.screen import ModalScreen
from textual.coordinate import Coordinate
from textual.widgets.data_table import CellDoesNotExist
from textual.reactive import reactive
import database
import time

# --- Configuration Lists ---
DIFFICULTY_OPTIONS = [("Easy", "Easy"), ("Medium", "Medium"), ("Hard", "Hard")]

TOPIC_OPTIONS = [
    ("Arrays & Hashing", "Arrays & Hashing"),
    ("Two Pointers", "Two Pointers"),
    ("Linked List", "Linked List"),
    ("Sliding Window", "Sliding Window"),
    ("Stack", "Stack"),
    ("Binary Search", "Binary Search"),
    ("Trees", "Trees"),
    ("Heap / Priority Queue", "Heap / Priority Queue"),
    ("Backtracking", "Backtracking"),
    ("Graphs", "Graphs"),
    ("Dynamic Programming", "Dynamic Programming"),
]

SHORT_TOPICS = {
    "Arrays & Hashing": "Arr & Hash",
    "Two Pointers": "2 Ptr",
    "Linked List": "Linked List",
    "Sliding Window": "Sliding Win",
    "Stack": "Stack",
    "Binary Search": "Bin Search",
    "Trees": "Trees",
    "Heap / Priority Queue": "Heap",
    "Backtracking": "Backtrack",
    "Graphs": "Graphs",
    "Dynamic Programming": "DP",
}

SHORT_DIFF = {"Easy": "E", "Medium": "M", "Hard": "H"}


class SearchInput(Input):
    """Custom Input that bubbles ctrl+f or handles it."""

    BINDINGS = [
        ("ctrl+f", "app.focus_search", "Focus Table"),
    ]


class AddModal(ModalScreen):
    """The Pop-up to log a new problem."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="modal-dialog"):
            yield Label("Problem Title:")
            yield Input(placeholder="e.g. Valid Anagram", id="title")
            yield Label("Difficulty:")
            yield Select(
                DIFFICULTY_OPTIONS, prompt="Select Difficulty", id="difficulty"
            )
            yield Label("Topic:")
            yield Select(TOPIC_OPTIONS, prompt="Select Topic", id="topic")
            yield Label("URL (Optional):")
            yield Input(placeholder="e.g. https://leetcode.com/...", id="url")
            with Horizontal(classes="modal-buttons"):
                yield Button("Log It", variant="primary", id="save_btn")
                yield Button("Cancel", variant="error", id="cancel_btn")

    def action_cancel(self) -> None:
        self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_btn":
            title = self.query_one("#title", Input).value
            diff = self.query_one("#difficulty", Select).value
            topic = self.query_one("#topic", Select).value
            url = self.query_one("#url", Input).value

            if title and diff != Select.BLANK and topic != Select.BLANK:
                database.add_problem(title, diff, topic, url)
                self.dismiss(True)
            else:
                self.notify("Please fill all fields!", severity="error")
        elif event.button.id == "cancel_btn":
            self.dismiss(False)


class TimerModal(ModalScreen):
    """Modal timer for tracking solve time."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    problem_title = ""
    countdown = reactive(2)
    elapsed_seconds = reactive(0)
    phase = reactive("countdown")  # "countdown" or "timer"

    def __init__(self, problem_title: str):
        super().__init__()
        self.problem_title = problem_title

    def compose(self) -> ComposeResult:
        with Container(id="timer-dialog"):
            yield Label(f"[b]{self.problem_title}[/b]", id="timer-title")
            yield Static("", id="timer-display")
            with Horizontal(classes="modal-buttons"):
                yield Button("Stop", variant="success", id="stop_btn", disabled=True)
                yield Button("Cancel", variant="error", id="cancel_btn")

    def on_mount(self) -> None:
        self._update_display()
        self.countdown_timer = self.set_interval(1, self._tick_countdown)

    def _tick_countdown(self) -> None:
        self.countdown -= 1
        self._update_display()

        if self.countdown <= 0:
            self.countdown_timer.stop()
            self.phase = "timer"
            self.start_time = time.time()
            self.query_one("#stop_btn", Button).disabled = False
            self._update_display()
            self.timer = self.set_interval(0.1, self._tick_timer)

    def _tick_timer(self) -> None:
        self.elapsed_seconds = int(time.time() - self.start_time)
        self._update_display()

    def _update_display(self) -> None:
        display = self.query_one("#timer-display", Static)
        if self.phase == "countdown":
            display.update(f"Starting in {self.countdown}...")
        else:
            mins, secs = divmod(self.elapsed_seconds, 60)
            display.update(f"{mins:02d}:{secs:02d}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "stop_btn":
            if self.phase == "timer":
                self.timer.stop()
                is_new_best, time_val = database.update_best_time(
                    self.problem_title, self.elapsed_seconds
                )
                self.dismiss(("stopped", self.elapsed_seconds, is_new_best))
        elif event.button.id == "cancel_btn":
            if self.phase == "timer":
                self.timer.stop()
            self.dismiss(("cancelled", None, None))

    def action_cancel(self) -> None:
        if self.phase == "timer" and hasattr(self, "timer"):
            self.timer.stop()
        self.dismiss(("cancelled", None, None))


class HelpModal(ModalScreen):
    """Translucent modal that displays all keybindings."""

    BINDINGS = [("escape", "cancel", "Cancel"), ("h", "cancel", "Close")]

    def compose(self) -> ComposeResult:
        with Container(id="help-overlay"):
            with Container(id="help-dialog"):
                yield Static("Keyboard Shortcuts", id="help-title")
                with Horizontal(classes="help-row"):
                    yield Static("h", classes="help-key")
                    yield Static("Toggle this help", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("a", classes="help-key")
                    yield Static("Add new problem", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("r", classes="help-key")
                    yield Static("Mark reviewed", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("x", classes="help-key")
                    yield Static("Reset progress", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("l", classes="help-key")
                    yield Static("Toggle Due / All view", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("o / enter", classes="help-key")
                    yield Static("Open URL & start timer", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("ctrl+f", classes="help-key")
                    yield Static("Focus search box", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("s", classes="help-key")
                    yield Static("Toggle stats panel", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("q", classes="help-key")
                    yield Static("Quit", classes="help-desc")
                yield Static(
                    "Press h or esc to close",
                    id="help-footer",
                )

    def action_cancel(self) -> None:
        self.dismiss(True)


class RecallApp(App):
    CSS_PATH = "tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "toggle_help", "Help"),
        ("a", "add_problem", "Log Problem"),
        ("r", "review_problem", "Review (Done)"),
        ("x", "reset_problem", "Reset Progress"),  # NEW BINDING
        ("l", "toggle_view", "Toggle Due/All"),
        ("o", "open_url", "Open URL"),
        ("enter", "open_url", "Open URL"),
        ("ctrl+f", "focus_search", "Focus Search"),
        ("s", "toggle_stats", "Toggle Stats"),
    ]

    view_mode = "due"
    search_filter = ""
    show_stats = False

    def __init__(self):
        super().__init__()
        # Load persisted theme on startup
        saved_theme = database.get_theme()
        if saved_theme and saved_theme in self.available_themes:
            self.theme = saved_theme

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        """Called when theme changes; persist to config."""
        database.set_theme(new_theme)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            # LEFT PANE
            with Vertical(id="left-pane"):
                yield Label("Due for Review", id="list_title", classes="section-title")
                yield SearchInput(
                    placeholder="Search problems...",
                    id="search_box",
                    classes="search-box",
                )
                yield DataTable(id="problem_table", cursor_type="row")

            # RIGHT PANE
            with Vertical(id="right-pane"):
                yield Static("Stats", classes="section-title")
                yield Static(id="stats_box", classes="stat-box")
                yield Static(id="view_indicator", classes="stat-box")
        yield Footer()

    def on_mount(self) -> None:
        # Populate UI data then set initial focus to the problems table
        # (default used to focus the search box; inverse by default now)
        self.refresh_data()
        try:
            table = self.query_one("#problem_table", DataTable)
            table.focus()
        except Exception:
            # If focus can't be set (no table yet), ignore silently
            pass

    def refresh_data(self) -> None:
        table = self.query_one("#problem_table", DataTable)
        title_label = self.query_one("#list_title", Label)
        view_label = self.query_one("#view_indicator", Static)

        table.clear(columns=True)

        # 1. Update Labels
        if self.view_mode == "due":
            title_label.update("Due for Review")
            view_label.update("Current View: [b]DUE[/b]")
            table.add_columns(
                "Title", "Diff", "Topic", "Progress", "Best", "Next Review"
            )
            problems = database.get_due_problems()
        else:
            title_label.update("All Logged Problems")
            view_label.update("Current View: [b]ALL[/b]")
            table.add_columns("Title", "Diff", "Topic", "Progress", "Best", "Status")
            problems = database.get_all_problems()

        # 2. Populate Table
        if not problems and self.view_mode == "due":
            title_label.update("Due for Review [green](All Caught Up!)[/green]")

        # Filter problems
        filtered_problems = [
            p
            for p in problems
            if self.search_filter.lower() in p["title"].lower()
            or self.search_filter.lower() in p.get("topic", "").lower()
        ]

        def get_progress_bar(stage):
            max_stages = len(database.INTERVALS) - 1
            filled = "■" * stage
            empty = "□" * (max_stages - stage)
            return f"[{filled}{empty}]"

        for p in filtered_problems:
            topic = p.get("topic", p.get("topics", "Unknown"))

            if self.show_stats:
                # Use Short Forms when Stats are visible (Space is tight)
                topic_display = SHORT_TOPICS.get(topic, topic)
                diff_display = SHORT_DIFF.get(
                    p["difficulty"], p["difficulty"][0] if p["difficulty"] else "?"
                )
            else:
                # Use Full text when Stats are hidden (More space)
                topic_display = topic
                diff_display = p["difficulty"]

            progress = get_progress_bar(p.get("review_stage", 0))
            last_col = p["next_review"] if self.view_mode == "due" else p["status"]

            best_seconds = p.get("best_time_seconds")
            if best_seconds is not None:
                mins, secs = divmod(best_seconds, 60)
                best_display = f"{mins:02d}:{secs:02d}"
            else:
                best_display = "--:--"

            table.add_row(
                p["title"],
                diff_display,
                topic_display,
                progress,
                best_display,
                last_col,
            )

        # 3. Update Stats
        stats = database.get_stats()
        stat_text = (
            f"Total Solved: {stats['total']}\n"
            f"Due Today:    {stats['due']}\n"
            f"Mastered:     {stats['mastered']}"
        )
        self.query_one("#stats_box", Static).update(stat_text)

        self.query_one("#stats_box", Static).update(stat_text)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "search_box":
            self.search_filter = event.value
            self.refresh_data()

    def action_add_problem(self) -> None:
        def check_submit(submitted: bool):
            if submitted:
                self.refresh_data()

        self.push_screen(AddModal(), check_submit)

    def action_toggle_view(self) -> None:
        self.view_mode = "all" if self.view_mode == "due" else "due"
        self.refresh_data()

    def _get_selected_title(self):
        """Helper to safely get the selected title."""
        table = self.query_one("#problem_table", DataTable)
        if table.row_count == 0 or table.cursor_row is None:
            return None
        try:
            return table.get_cell_at(Coordinate(table.cursor_row, 0))
        except:
            return None

    def action_review_problem(self) -> None:
        title = self._get_selected_title()
        if not title:
            self.notify("Select a problem first!", severity="warning")
            return

        # Call DB Review with strict logic
        success, msg = database.mark_reviewed(title)

        if success:
            self.notify(msg)  # Green/Standard notification
            self.refresh_data()
        else:
            self.notify(msg, severity="error")  # Red error notification

    def action_reset_problem(self) -> None:
        title = self._get_selected_title()
        if not title:
            self.notify("Select a problem first!", severity="warning")
            return

        # Call DB Reset
        success, msg = database.reset_problem(title)
        if success:
            self.notify(msg)
            self.refresh_data()
        else:
            self.notify(msg, severity="error")

    def action_open_url(self) -> None:
        title = self._get_selected_title()
        if not title:
            return

        import webbrowser

        problems = database.get_all_problems()
        problem = next((p for p in problems if p["title"] == title), None)

        if problem and problem.get("url"):
            webbrowser.open(problem["url"])

            def handle_timer_result(result):
                if result and result[0] == "stopped":
                    _, elapsed, is_new_best = result
                    mins, secs = divmod(elapsed, 60)
                    time_str = f"{mins:02d}:{secs:02d}"
                    if is_new_best:
                        self.notify(f"New best time: {time_str}!")
                    else:
                        self.notify(f"Time: {time_str} (not a new best)")
                    self.refresh_data()

            self.push_screen(TimerModal(title), handle_timer_result)
        else:
            self.notify("No URL found for this problem.", severity="warning")

    def action_toggle_help(self) -> None:
        """Show the help popup overlay listing all keybindings."""
        self.push_screen(HelpModal())

    def action_focus_search(self) -> None:
        """Toggles focus between search box and table."""
        search_box = self.query_one("#search_box", Input)
        table = self.query_one("#problem_table", DataTable)

        if self.focused == search_box:
            table.focus()
        else:
            search_box.focus()

    def action_toggle_stats(self) -> None:
        self.show_stats = not self.show_stats

        # Toggle class on the main container or app to trigger CSS changes
        container = self.query_one("#main-container")
        if self.show_stats:
            container.add_class("show-stats")
        else:
            container.remove_class("show-stats")

        self.refresh_data()


if __name__ == "__main__":
    app = RecallApp()
    app.run()
