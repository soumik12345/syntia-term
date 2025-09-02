from os import PathLike
from typing import Union

from textual.app import App
from textual.containers import Horizontal
from textual.widgets import DirectoryTree, TextArea, Footer


class Syntia(App):
    BINDINGS = [
        ("ctrl+s", "save_file", "Save file"),
        ("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, root_directory: PathLike, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_directory = root_directory
        self.current_open_file: Union[PathLike, None] = None

    def compose(self):
        yield Horizontal(
            DirectoryTree(path=self.root_directory),
            TextArea(id="editor"),
        )
        yield Footer()

    def _on_directory_tree_file_selected(self, event: DirectoryTree.FileSelected):
        if not event.path.is_file():
            return
        self.current_open_file = event.path
        text_editor: TextArea = self.query_one("#editor", TextArea)
        text_editor.text = event.path.read_text()
        if event.path.suffix == ".py":
            text_editor.language = "python"
        elif event.path.suffix == ".md":
            text_editor.language = "markdown"
        else:
            text_editor.language = "text"

    def action_save_file(self):
        if self.current_open_file is None:
            return
        editor: TextArea = self.query_one("#editor", TextArea)
        self.current_open_file.write_text(editor.text)
