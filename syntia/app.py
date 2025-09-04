from os import PathLike

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer

from syntia.components import (
    HorizontalSplitter,
    SyntiaTerminal,
    TabbedTextArea,
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
        width: 1fr;       /* fill remaining horizontal space */
        height: 1fr;      /* fill remaining vertical space */
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
        horizontal_splitter = HorizontalSplitter()
        terminal_widget = SyntiaTerminal(command="bash", id="terminal")

        yield Horizontal(
            tree,
            VerticalSplitter(),
            Vertical(
                tabbed_editor,
                horizontal_splitter,
                terminal_widget,
            ),
        )
        yield Footer()

    def on_ready(self) -> None:
        # Terminal is hidden by default and will be started when first shown
        pass

    def on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        if not event.path.is_file():
            return
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        tabbed_editor.add_file_tab(event.path)

    def action_save_file(self):
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        if tabbed_editor.save_active_file():
            file_path = tabbed_editor.get_active_file_path()
            if file_path:
                self.notify(f"File {file_path.name} saved!", timeout=3)
        else:
            self.notify("No file to save or save failed!", timeout=3)

    def action_close_tab(self):
        tabbed_editor: TabbedTextArea = self.query_one("#editor", TabbedTextArea)
        file_path = tabbed_editor.get_active_file_path()
        if tabbed_editor.close_tab():
            if file_path:
                self.notify(f"Closed {file_path.name}", timeout=2)
        else:
            self.notify("No tab to close!", timeout=2)

    def action_toggle_terminal(self):
        terminal: SyntiaTerminal = self.query_one("#terminal")
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
