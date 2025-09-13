from os import PathLike

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, Footer

from syntia_term.components import (
    TabbedRightPanel,
    TabbedTextArea,
    Terminal,
    VerticalSplitter,
)


class Syntia(App):
    BINDINGS = [
        ("ctrl+s", "save_file", "Save file"),
        ("ctrl+w", "close_tab", "Close tab"),
        ("ctrl+t", "toggle_terminal", "Toggle right panel"),
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
    
    /* When right panel is hidden, editor should expand */
    #editor_container {
        height: 1fr;
    }
    """

    def __init__(self, root_directory: PathLike, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_directory = root_directory
        self.terminal_initialized = False
        self.right_panel_collapsed = False

    def compose(self) -> ComposeResult:
        tree = DirectoryTree(path=self.root_directory, id="tree")
        tree.ICON_NODE = "\u25b6 "
        tree.ICON_NODE_EXPANDED = "\u25bc "

        tabbed_editor = TabbedTextArea(id="editor")
        terminal_widget = Terminal(command="bash", id="terminal")
        tabbed_right_panel = TabbedRightPanel(
            terminal=terminal_widget, id="right_panel"
        )

        vertical_splitter_1 = VerticalSplitter()
        vertical_splitter_2 = VerticalSplitter()

        yield Horizontal(
            tree,
            vertical_splitter_1,
            Horizontal(
                tabbed_editor,
                vertical_splitter_2,
                tabbed_right_panel,
                id="editor_container",
            ),
        )
        yield Footer()

    def on_ready(self) -> None:
        # Initialize terminal since it's now part of the right panel by default
        tabbed_right_panel: TabbedRightPanel = self.query_one(
            "#right_panel", TabbedRightPanel
        )
        terminal = tabbed_right_panel.get_terminal()

        if terminal and not self.terminal_initialized:
            terminal.start()
            self.terminal_initialized = True

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

        if tabbed_editor.close_tab():
            # TabbedTextArea now handles notifications and markdown synchronization
            pass
        else:
            self.notify("No tab to close!", timeout=2)

    def action_toggle_terminal(self):
        """Toggle the visibility of the right panel and vertical splitter."""
        tabbed_right_panel: TabbedRightPanel = self.query_one(
            "#right_panel", TabbedRightPanel
        )
        vertical_splitter_2 = self.query("#editor_container VerticalSplitter").last()

        if self.right_panel_collapsed:
            # Show the right panel and splitter
            self._show_right_panel(tabbed_right_panel, vertical_splitter_2)
        else:
            # Hide the right panel and splitter
            self._hide_right_panel(tabbed_right_panel, vertical_splitter_2)

    def _show_right_panel(
        self, tabbed_right_panel: TabbedRightPanel, vertical_splitter_2
    ) -> None:
        """Show the right panel and vertical splitter."""
        tabbed_right_panel.display = True
        if vertical_splitter_2:
            vertical_splitter_2.display = True
        self.right_panel_collapsed = False

        # Switch to terminal tab and initialize if needed
        terminal = tabbed_right_panel.get_terminal()
        if terminal:
            tabbed_right_panel.switch_to_terminal_tab()
            if not self.terminal_initialized:
                terminal.start()
                self.terminal_initialized = True

    def _hide_right_panel(
        self, tabbed_right_panel: TabbedRightPanel, vertical_splitter_2
    ) -> None:
        """Hide the right panel and vertical splitter."""
        tabbed_right_panel.display = False
        if vertical_splitter_2:
            vertical_splitter_2.display = False
        self.right_panel_collapsed = True
