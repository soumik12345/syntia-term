from os import PathLike

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer

from syntia.components import (
    HorizontalSplitter,
    TabbedRightPanel,
    TabbedTextArea,
    Terminal,
    VerticalSplitter,
)


class Syntia(App):
    BINDINGS = [
        ("ctrl+s", "save_file", "Save file"),
        ("ctrl+w", "close_tab", "Close tab"),
        ("ctrl+t", "toggle_terminal", "Toggle terminal"),
        ("ctrl+q", "quit", "Quit"),
    ]

    CSS = """
    #tree {
        width: 30;        /* initial sidebar width in cells */
        min-width: 16;
        height: 1fr;
    }
    #editor {
        width: 1fr;       /* take half of remaining space */
        height: 1fr;      /* fill remaining vertical space */
    }
    #right_panel {
        width: 1fr;       /* take half of remaining space */
        height: 1fr;
    }
    #terminal {
        width: 1fr;
        height: 15;       /* initial height for terminal */
        border: solid $primary;
        display: none;    /* hidden by default */
    }
    HorizontalSplitter {
        display: none;    /* hidden by default with terminal */
    }
    """

    def __init__(self, root_directory: PathLike, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_directory = root_directory
        self.terminal_initialized = False

    def compose(self) -> ComposeResult:
        tree = DirectoryTree(path=self.root_directory, id="tree")
        tree.ICON_NODE = "\u25b6 "
        tree.ICON_NODE_EXPANDED = "\u25bc "

        tabbed_editor = TabbedTextArea(id="editor")
        tabbed_right_panel = TabbedRightPanel(id="right_panel")
        horizontal_splitter = HorizontalSplitter()
        terminal_widget = Terminal(command="bash", id="terminal")

        vertical_splitter_1 = VerticalSplitter()
        vertical_splitter_2 = VerticalSplitter()

        yield Horizontal(
            tree,
            vertical_splitter_1,
            Vertical(
                Horizontal(
                    tabbed_editor,
                    vertical_splitter_2,
                    tabbed_right_panel,
                    id="editor_container",
                ),
                horizontal_splitter,
                terminal_widget,
            ),
        )
        yield Footer()

    def on_ready(self) -> None:
        # Terminal is hidden by default and will be started when first shown
        pass

    def sync_markdown_preview(self, file_path) -> None:
        """Sync markdown file content to the right panel preview."""
        try:
            content = file_path.read_text()
            tabbed_right_panel: TabbedRightPanel = self.query_one(
                "#right_panel", TabbedRightPanel
            )
            tabbed_right_panel.add_markdown_tab(file_path, content)
        except Exception:
            # Handle file read errors gracefully
            pass

    def update_markdown_preview_if_active(self, file_path) -> None:
        """Update markdown preview if the file is currently active in editor."""
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        active_file = tabbed_editor.get_active_file_path()

        if active_file == file_path and file_path.suffix.lower() == ".md":
            try:
                content = file_path.read_text()
                tabbed_right_panel: TabbedRightPanel = self.query_one(
                    "#right_panel", TabbedRightPanel
                )
                tabbed_right_panel.update_markdown_tab(file_path, content)
            except Exception:
                pass

    def sync_active_markdown_preview(self) -> None:
        """Sync the currently active markdown file in the editor to the preview panel."""
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        active_file = tabbed_editor.get_active_file_path()

        if active_file and active_file.suffix.lower() == ".md":
            self.sync_markdown_preview(active_file)

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        if not event.path.is_file():
            return
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        tabbed_editor.add_file_tab(event.path)

        # If it's a markdown file, also add it to the right panel
        if event.path.suffix.lower() == ".md":
            self.sync_markdown_preview(event.path)

    def action_save_file(self):
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        file_path = tabbed_editor.get_active_file_path()

        if tabbed_editor.save_active_file():
            if file_path:
                self.notify(f"File {file_path.name} saved!", timeout=3)
                # Update markdown preview if it's a markdown file
                if file_path.suffix.lower() == ".md":
                    self.update_markdown_preview_if_active(file_path)
        else:
            self.notify("No file to save or save failed!", timeout=3)

    def action_close_tab(self):
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        file_path = tabbed_editor.get_active_file_path()

        if tabbed_editor.close_tab():
            if file_path:
                self.notify(f"Closed {file_path.name}", timeout=2)
                # Remove markdown preview tab if it was a markdown file
                if file_path.suffix.lower() == ".md":
                    tabbed_right_panel: TabbedRightPanel = self.query_one(
                        "#right_panel", TabbedRightPanel
                    )
                    tabbed_right_panel.remove_markdown_tab(file_path)
        else:
            self.notify("No tab to close!", timeout=2)

    def action_toggle_terminal(self):
        terminal: Terminal = self.query_one("#terminal")
        horizontal_splitter: HorizontalSplitter = self.query_one(HorizontalSplitter)

        if terminal.display:
            # Hide terminal and splitter
            terminal.display = False
            horizontal_splitter.display = False
        else:
            # Show terminal and splitter
            terminal.display = True
            horizontal_splitter.display = True
            # Initialize and start terminal if not already done
            if not self.terminal_initialized:
                terminal.start()
                self.terminal_initialized = True
