from os import PathLike
from pathlib import Path
from typing import Dict, Optional, Union

from textual.events import Key, MouseDown
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, TextArea


class TabbedTextArea(Widget, can_focus=True):
    """A custom widget that manages multiple TextArea widgets in tabs."""

    DEFAULT_CSS = """
    TabbedTextArea {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedTextArea > TabbedContent {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedTextArea TextArea {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_files: Dict[str, Path] = {}  # tab_id -> file_path mapping
        self.tabbed_content: Optional[TabbedContent] = None

    def compose(self):
        self.tabbed_content = TabbedContent()
        yield self.tabbed_content

    def add_language_support(
        self, file_path: PathLike, text_area: TextArea
    ) -> TextArea:
        if file_path.suffix == ".py":
            text_area.language = "python"
        elif file_path.suffix == ".md":
            text_area.language = "markdown"
        elif file_path.suffix in [".js", ".jsx"]:
            text_area.language = "javascript"
        elif file_path.suffix in [".ts", ".tsx"]:
            text_area.language = "typescript"
        elif file_path.suffix == ".json":
            text_area.language = "json"
        elif file_path.suffix in [".html", ".htm"]:
            text_area.language = "html"
        elif file_path.suffix == ".css":
            text_area.language = "css"
        elif file_path.suffix == ".toml":
            text_area.language = "toml"

        return text_area

    def add_file_tab(self, file_path: Union[str, PathLike]) -> str:
        """Add a new tab with a TextArea for the given file."""
        file_path = Path(file_path)
        file_name = file_path.name

        # Check if file is already open
        for tab_id, existing_path in self.open_files.items():
            if existing_path == file_path:
                # Switch to existing tab
                self.tabbed_content.active = tab_id
                return tab_id

        # Create unique tab ID
        tab_id = f"tab_{len(self.open_files)}"

        # Read file content
        try:
            content = file_path.read_text()
        except Exception:
            content = ""

        # Create TextArea
        text_area = TextArea(text=content, read_only=False, id=f"editor_{tab_id}")

        # Set language based on file extension
        text_area = self.add_language_support(file_path, text_area)

        # Create tab pane
        tab_pane = TabPane(file_name, text_area, id=tab_id)

        # Add to tabbed content
        self.tabbed_content.add_pane(tab_pane)

        # Store file mapping
        self.open_files[tab_id] = file_path

        # Switch to the new tab
        self.tabbed_content.active = tab_id

        # Focus the text area
        text_area.focus()

        return tab_id

    def get_active_editor(self) -> Optional[TextArea]:
        """Get the currently active TextArea."""
        if not self.tabbed_content or not self.tabbed_content.active:
            return None

        active_tab = self.tabbed_content.get_pane(self.tabbed_content.active)
        if not active_tab:
            return None

        # The TextArea should be the content of the TabPane
        text_areas = active_tab.query(TextArea)
        return text_areas.first() if text_areas else None

    def get_active_file_path(self) -> Optional[Path]:
        """Get the file path of the currently active tab."""
        if not self.tabbed_content or not self.tabbed_content.active:
            return None

        return self.open_files.get(self.tabbed_content.active)

    def save_active_file(self) -> bool:
        """Save the currently active file. Returns True if successful."""
        editor = self.get_active_editor()
        file_path = self.get_active_file_path()

        if not editor or not file_path:
            return False

        try:
            file_path.write_text(editor.text)
            return True
        except Exception:
            return False

    def close_tab(self, tab_id: Optional[str] = None) -> bool:
        """Close a tab. If tab_id is None, closes the active tab."""
        if not self.tabbed_content:
            return False

        if tab_id is None:
            tab_id = self.tabbed_content.active

        if not tab_id or tab_id not in self.open_files:
            return False

        # Get file path before removing it
        file_path = self.open_files[tab_id]

        # Remove the tab
        self.tabbed_content.remove_pane(tab_id)

        # Remove from file mapping
        del self.open_files[tab_id]

        # Notify app about tab closure for markdown synchronization
        if file_path.suffix.lower() == ".md":
            try:
                # Import here to avoid circular imports
                from syntia.components.tabbed_right_panel import TabbedRightPanel

                tabbed_right_panel: TabbedRightPanel = self.app.query_one(
                    "#right_panel", TabbedRightPanel
                )
                tabbed_right_panel.remove_markdown_tab(file_path)
                # Notify user about the synchronized closure
                self.app.notify(f"Closed {file_path.name} and its preview", timeout=2)
            except Exception:
                # Handle case where right panel might not be available
                self.app.notify(f"Closed {file_path.name}", timeout=2)
        else:
            # Notify user about non-markdown tab closure
            self.app.notify(f"Closed {file_path.name}", timeout=2)

        return True

    def has_open_files(self) -> bool:
        """Check if there are any open files."""
        return len(self.open_files) > 0

    def on_key(self, event: Key) -> None:
        """Handle key events."""
        if event.key == "ctrl+w":
            self.close_tab()
            event.prevent_default()
        else:
            # Pass other events to the active editor
            editor = self.get_active_editor()
            if editor:
                editor.post_message(event)

    def on_mouse_down(self, event: MouseDown) -> None:
        """Handle mouse events, particularly right-clicks on tabs."""
        if event.button == 3:  # Right mouse button
            # Check if we're clicking on a tab header
            if self.tabbed_content:
                # Get the tab that was clicked
                clicked_tab_id = self._get_tab_at_position(event.x, event.y)
                if clicked_tab_id:
                    self.close_tab(clicked_tab_id)
                    event.prevent_default()

    def _get_tab_at_position(self, x: int, y: int) -> Optional[str]:
        """Get the tab ID at the given position."""
        if not self.tabbed_content:
            return None

        # Check if the click is in the tabs area (typically the top part)
        if y == 0:  # Tab headers are at the very top
            tab_ids = list(self.open_files.keys())
            if not tab_ids:
                return None

            # Calculate approximate tab positions
            # Tab titles have some padding, so we estimate based on content
            current_x = 0
            for tab_id in tab_ids:
                if tab_id in self.open_files:
                    file_path = self.open_files[tab_id]
                    # Estimate tab width based on filename length + padding
                    tab_title = file_path.name
                    estimated_width = len(tab_title) + 4  # Add padding

                    if current_x <= x < current_x + estimated_width:
                        return tab_id
                    current_x += estimated_width
        return None
