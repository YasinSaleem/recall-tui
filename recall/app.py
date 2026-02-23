from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.coordinate import Coordinate

from . import constants
from . import database
from .screens import (
    AddModal,
    DataTable,
    Footer,
    Header,
    HelpModal,
    Input,
    Label,
    SearchInput,
    Static,
    TestModeScreen,
    TimerModal,
)


class RecallApp(App):
    CSS_PATH = "../tui.css"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("h", "toggle_help", "Help"),
        ("t", "enter_test_mode", "Test Mode"),
        ("a", "add_problem", "Log Problem"),
        ("r", "review_problem", "Review (Done)"),
        ("x", "reset_problem", "Reset Progress"),
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
        saved_theme = database.get_theme()
        if saved_theme and saved_theme in self.available_themes:
            self.theme = saved_theme

    def watch_theme(self, old_theme: str, new_theme: str) -> None:
        database.set_theme(new_theme)

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="main-container"):
            with Vertical(id="left-pane"):
                yield Label("Due for Review", id="list_title", classes="section-title")
                yield SearchInput(
                    placeholder="Search problems...",
                    id="search_box",
                    classes="search-box",
                )
                yield DataTable(id="problem_table", cursor_type="row")

            with Vertical(id="right-pane"):
                yield Static("Stats", classes="section-title")
                yield Static(id="stats_box", classes="stat-box")
                yield Static(id="view_indicator", classes="stat-box")
        yield Footer()

    def on_mount(self) -> None:
        self.refresh_data()
        try:
            table = self.query_one("#problem_table", DataTable)
            table.focus()
        except Exception:
            pass

    def refresh_data(self) -> None:
        table = self.query_one("#problem_table", DataTable)
        title_label = self.query_one("#list_title", Label)
        view_label = self.query_one("#view_indicator", Static)

        table.clear(columns=True)

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

        if not problems and self.view_mode == "due":
            title_label.update("Due for Review [green](All Caught Up!)[/green]")

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
                topic_display = constants.SHORT_TOPICS.get(topic, topic)
                diff_display = constants.SHORT_DIFF.get(
                    p["difficulty"], p["difficulty"][0] if p["difficulty"] else "?"
                )
            else:
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

        success, msg = database.mark_reviewed(title)

        if success:
            self.notify(msg)
            self.refresh_data()
        else:
            self.notify(msg, severity="error")

    def action_reset_problem(self) -> None:
        title = self._get_selected_title()
        if not title:
            self.notify("Select a problem first!", severity="warning")
            return

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
        self.push_screen(HelpModal())

    def action_focus_search(self) -> None:
        search_box = self.query_one("#search_box", Input)
        table = self.query_one("#problem_table", DataTable)

        if self.focused == search_box:
            table.focus()
        else:
            search_box.focus()

    def action_toggle_stats(self) -> None:
        self.show_stats = not self.show_stats

        container = self.query_one("#main-container")
        if self.show_stats:
            container.add_class("show-stats")
        else:
            container.remove_class("show-stats")

        self.refresh_data()

    def action_enter_test_mode(self) -> None:
        all_problems = database.get_all_problems()
        if len(all_problems) < 3:
            self.notify("Need at least 3 problems for Test Mode!", severity="error")
            return
        self.push_screen(TestModeScreen())
