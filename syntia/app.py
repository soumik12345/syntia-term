from os import PathLike
from typing import Union

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, Footer

from syntia.components import VerticalSplitter, TabbedTextArea


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
        height: 1fr;
    }
    """

    def __init__(self, root_directory: PathLike, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_directory = root_directory

    def compose(self) -> ComposeResult:
        tree = DirectoryTree(path=self.root_directory, id="tree")
        tree.ICON_NODE = "\u25B6 "
        tree.ICON_NODE_EXPANDED = "\u25BC "

        tabbed_editor = TabbedTextArea(id="editor")
        yield Horizontal(
            tree,
            VerticalSplitter(),
            tabbed_editor,
        )
        yield Footer()

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
