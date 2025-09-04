from os import PathLike
from typing import Union

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import DirectoryTree, Footer
from textual_terminal import Terminal

from syntia.components import TabbedTextArea, VerticalSplitter


class Syntia(App):
    BINDINGS = [
        ("ctrl+s", "save_file", "Save file"),
        ("ctrl+w", "close_tab", "Close tab"),
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
        height: 1fr;      /* fill most of the vertical space */
    }
    #terminal {
        width: 1fr;
        height: 15;       /* fixed height for terminal */
        border: solid $primary;
    }
    """

    def __init__(self, root_directory: PathLike, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_directory = root_directory

    def compose(self) -> ComposeResult:
        tree = DirectoryTree(path=self.root_directory, id="tree")
        tree.ICON_NODE = "\u25b6 "
        tree.ICON_NODE_EXPANDED = "\u25bc "

        tabbed_editor = TabbedTextArea(id="editor")
        terminal_widget = Terminal(command="bash", id="terminal")

        yield Horizontal(
            tree,
            VerticalSplitter(),
            Vertical(
                tabbed_editor,
                terminal_widget,
            ),
        )
        yield Footer()

    def on_ready(self) -> None:
        terminal: Terminal = self.query_one("#terminal")
        terminal.start()

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
