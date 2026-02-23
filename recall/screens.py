import time

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.coordinate import Coordinate
from textual.reactive import reactive
from textual.screen import ModalScreen, Screen
from textual.widgets import (
    Button,
    DataTable,
    Header,
    Footer,
    Input,
    Label,
    Select,
    Static,
)

from . import constants
from . import crypto
from . import database


class SearchInput(Input):
    BINDINGS = [("ctrl+f", "app.focus_search", "Focus Table")]


class AddModal(ModalScreen):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Container(id="modal-dialog"):
            yield Label("Problem Title:")
            yield Input(placeholder="e.g. Valid Anagram", id="title")
            yield Label("Difficulty:")
            yield Select(
                constants.DIFFICULTY_OPTIONS,
                prompt="Select Difficulty",
                id="difficulty",
            )
            yield Label("Topic:")
            yield Select(constants.TOPIC_OPTIONS, prompt="Select Topic", id="topic")
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
    BINDINGS = [("escape", "cancel", "Cancel")]

    problem_title = ""
    countdown = reactive(2)
    elapsed_seconds = reactive(0)
    phase = reactive("countdown")

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
    BINDINGS = [("escape", "cancel", "Cancel"), ("h", "cancel", "Close")]

    def compose(self) -> ComposeResult:
        with Container(id="help-overlay"):
            with Container(id="help-dialog"):
                yield Static("Keyboard Shortcuts", id="help-title")
                with Horizontal(classes="help-row"):
                    yield Static("h", classes="help-key")
                    yield Static("Toggle this help", classes="help-desc")
                with Horizontal(classes="help-row"):
                    yield Static("t", classes="help-key")
                    yield Static("Enter Test Mode", classes="help-desc")
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
                yield Static("Press h or esc to close", id="help-footer")

    def action_cancel(self) -> None:
        self.dismiss(True)


class TestModeScreen(Screen):
    BINDINGS = [
        ("o", "open_problem", "Open & Time"),
        ("enter", "open_problem", "Open & Time"),
        ("escape", "exit_test_mode", "Exit"),
        ("t", "exit_test_mode", "Exit"),
    ]

    problems = reactive([])
    problem_states = reactive({})
    problem_times = reactive({})
    total_time = reactive(0)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Vertical(id="test-mode-container"):
            yield Static("TEST MODE", id="test-mode-title")
            yield Static("Total: 00:00  |  Solved: 0/3", id="test-mode-header")
            yield DataTable(id="test_mode_table")
        yield Footer()

    def on_mount(self) -> None:
        self.problems = database.get_random_problems(3)
        self.problem_states = {i: "encrypted" for i in range(len(self.problems))}
        self.problem_times = {}
        self.total_time = 0
        self._refresh_table()

    def _refresh_table(self) -> None:
        table = self.query_one("#test_mode_table", DataTable)
        table.clear(columns=True)
        table.add_columns("Title", "Difficulty", "Topic", "Status")

        for i, p in enumerate(self.problems):
            state = self.problem_states.get(i, "encrypted")
            if state == "encrypted":
                title = crypto.encrypt(p["title"])
                diff = crypto.encrypt(p.get("difficulty", ""))
                topic = crypto.encrypt(p.get("topic", ""))
                status = "🔒 Encrypted"
            else:
                title = p["title"]
                diff = p.get("difficulty", "")
                topic = p.get("topic", "")
                elapsed = self.problem_times.get(i, 0)
                mins, secs = divmod(elapsed, 60)
                status = f"✓ {mins:02d}:{secs:02d}"

            table.add_row(title, diff, topic, status)

        solved = len(self.problem_times)
        total_mins, total_secs = divmod(self.total_time, 60)
        header = f"Total: {total_mins:02d}:{total_secs:02d}  |  Solved: {solved}/3"
        self.query_one("#test-mode-header", Static).update(header)

    def action_open_problem(self) -> None:
        table = self.query_one("#test_mode_table", DataTable)
        if table.row_count == 0 or table.cursor_row is None:
            return

        idx = table.cursor_row
        if self.problem_states.get(idx) == "decrypted":
            self.notify("Already solved!", severity="warning")
            return

        problem = self.problems[idx]
        title = problem["title"]

        def handle_timer_result(result):
            if result and result[0] == "stopped":
                _, elapsed, _ = result
                self.problem_states[idx] = "decrypted"
                self.problem_times[idx] = elapsed
                self.total_time = sum(self.problem_times.values())
                self._refresh_table()

                if len(self.problem_times) == 3:
                    mins, secs = divmod(self.total_time, 60)
                    self.notify(
                        f"Test Complete! Total: {mins:02d}:{secs:02d}",
                        severity="success",
                    )

        if problem.get("url"):
            import webbrowser

            webbrowser.open(problem["url"])

        self.push_screen(TimerModal(title), handle_timer_result)

    def action_exit_test_mode(self) -> None:
        self.app.pop_screen()
