from os import PathLike
from pathlib import Path
from typing import Dict, Optional, Union

from textual.events import Key, MouseDown
from textual.widget import Widget
from textual.widgets import MarkdownViewer, TabbedContent, TabPane

from syntia.components.terminal import Terminal


class TabbedRightPanel(Widget, can_focus=True):
    """A custom widget that manages MarkdownViewer widgets in tabs for markdown files."""

    DEFAULT_CSS = """
    TabbedRightPanel {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedRightPanel > TabbedContent {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedRightPanel MarkdownViewer {
        height: 1fr;
        width: 1fr;
    }
    
    TabbedRightPanel Terminal {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self, terminal: Terminal = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.open_files: Dict[str, Path] = {}  # tab_id -> file_path mapping
        self.tabbed_content: Optional[TabbedContent] = None
        self.terminal: Optional[Terminal] = terminal
        self.terminal_tab_id = "terminal_tab"

    def compose(self):
        self.tabbed_content = TabbedContent()
        yield self.tabbed_content

    async def on_mount(self) -> None:
        """Called when the widget is mounted."""
        # Add terminal as the first tab if provided
        if self.terminal and self.tabbed_content:
            terminal_tab = TabPane("🖥️ Terminal", self.terminal, id=self.terminal_tab_id)
            self.tabbed_content.add_pane(terminal_tab)
            # Set terminal tab as active by default
            self.tabbed_content.active = self.terminal_tab_id
            # Focus the terminal widget
            self.terminal.focus()

    def add_markdown_tab(self, file_path: Union[str, PathLike], content: str) -> str:
        """Add a new tab with a MarkdownViewer for the given markdown file."""
        file_path = Path(file_path)
        file_name = file_path.name

        # Check if file is already open
        for tab_id, existing_path in self.open_files.items():
            if existing_path == file_path:
                # Update existing tab content and switch to it
                existing_tab = self.tabbed_content.get_pane(tab_id)
                if existing_tab:
                    markdown_viewers = existing_tab.query(MarkdownViewer)
                    if markdown_viewers:
                        markdown_viewer = markdown_viewers.first()
                        markdown_viewer.update(content)
                self.tabbed_content.active = tab_id
                return tab_id

        # Create unique tab ID
        tab_id = f"preview_tab_{len(self.open_files)}"

        # Create MarkdownViewer
        markdown_viewer = MarkdownViewer(
            markdown=content,
            show_table_of_contents=False,
            id=f"markdown_viewer_{tab_id}",
        )

        # Create tab pane with preview prefix
        tab_pane = TabPane(f"📖 {file_name}", markdown_viewer, id=tab_id)

        # Add to tabbed content
        self.tabbed_content.add_pane(tab_pane)

        # Store file mapping
        self.open_files[tab_id] = file_path

        # Switch to the new tab
        self.tabbed_content.active = tab_id

        return tab_id

    def update_markdown_tab(
        self, file_path: Union[str, PathLike], content: str
    ) -> bool:
        """Update the content of an existing markdown tab."""
        file_path = Path(file_path)

        # Find the tab for this file
        for tab_id, existing_path in self.open_files.items():
            if existing_path == file_path:
                tab = self.tabbed_content.get_pane(tab_id)
                if tab:
                    markdown_viewers = tab.query(MarkdownViewer)
                    if markdown_viewers:
                        markdown_viewer = markdown_viewers.first()
                        markdown_viewer.update(content)
                        return True
        return False

    def remove_markdown_tab(self, file_path: Union[str, PathLike]) -> bool:
        """Remove a markdown tab for the given file path."""
        file_path = Path(file_path)

        # Find and remove the tab
        for tab_id, existing_path in self.open_files.items():
            if existing_path == file_path:
                self.tabbed_content.remove_pane(tab_id)
                del self.open_files[tab_id]
                return True
        return False

    def get_active_file_path(self) -> Optional[Path]:
        """Get the file path of the currently active tab."""
        if not self.tabbed_content or not self.tabbed_content.active:
            return None
        return self.open_files.get(self.tabbed_content.active)

    def has_open_tabs(self) -> bool:
        """Check if there are any open tabs."""
        return len(self.open_files) > 0

    def clear_all_tabs(self) -> None:
        """Remove all tabs."""
        if self.tabbed_content:
            for tab_id in list(self.open_files.keys()):
                self.tabbed_content.remove_pane(tab_id)
        self.open_files.clear()

    def is_markdown_file_open(self, file_path: Union[str, PathLike]) -> bool:
        """Check if a markdown file is currently open in a tab."""
        file_path = Path(file_path)
        return any(
            existing_path == file_path for existing_path in self.open_files.values()
        )

    def get_terminal(self) -> Optional[Terminal]:
        """Get the terminal widget."""
        return self.terminal

    def switch_to_terminal_tab(self) -> None:
        """Switch to the terminal tab."""
        if self.tabbed_content and self.terminal:
            self.tabbed_content.active = self.terminal_tab_id
            # Focus the terminal when switching to it
            self.terminal.focus()

    def focus(self, scroll_visible: bool = True) -> None:
        """Override focus to delegate to the active tab content."""
        if (
            self.tabbed_content
            and self.tabbed_content.active == self.terminal_tab_id
            and self.terminal
        ):
            # Focus the terminal if it's the active tab
            self.terminal.focus(scroll_visible)
        else:
            # Otherwise use default focus behavior
            super().focus(scroll_visible)

    def close_active_tab(self) -> bool:
        """Close the currently active tab."""
        if not self.tabbed_content or not self.tabbed_content.active:
            return False

        tab_id = self.tabbed_content.active

        # Prevent closing the terminal tab
        if tab_id == self.terminal_tab_id:
            return False

        if tab_id in self.open_files:
            self.tabbed_content.remove_pane(tab_id)
            del self.open_files[tab_id]
            return True
        return False

    def close_tab_by_id(self, tab_id: str) -> bool:
        """Close a specific tab by its ID."""
        # Prevent closing the terminal tab
        if tab_id == self.terminal_tab_id:
            return False

        if tab_id in self.open_files:
            self.tabbed_content.remove_pane(tab_id)
            del self.open_files[tab_id]
            return True
        return False

    def on_key(self, event: Key) -> None:
        """Handle key events."""
        if event.key == "ctrl+w":
            self.close_active_tab()
            event.prevent_default()
        else:
            # Pass other events to the active tab content
            if (
                self.tabbed_content
                and self.tabbed_content.active == self.terminal_tab_id
                and self.terminal
            ):
                # Let the terminal handle the key event
                return

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation events."""
        # Check if the terminal tab was activated
        if event.tab.id == self.terminal_tab_id and self.terminal:
            # Focus the terminal widget when its tab is activated
            self.terminal.focus()

    def on_mouse_down(self, event: MouseDown) -> None:
        """Handle mouse events, particularly right-clicks on tabs."""
        if event.button == 3:  # Right mouse button
            # Check if we're clicking on a tab header (only in the top area)
            if self.tabbed_content and event.y == 0:
                # Get the tab that was clicked
                clicked_tab_id = self._get_tab_at_position(event.x, event.y)
                if clicked_tab_id:
                    self.close_tab_by_id(clicked_tab_id)
                    event.prevent_default()
                    return

        # For other mouse events, let the content handle them (especially terminal)
        # Don't prevent default for mouse events in the content area

    def _get_tab_at_position(self, x: int, y: int) -> Optional[str]:
        """Get the tab ID at the given position."""
        if not self.tabbed_content:
            return None

        # Check if the click is in the tabs area (typically the top part)
        if y == 0:  # Tab headers are at the very top
            current_x = 0

            # First, check if we're clicking on the terminal tab
            if self.terminal:
                terminal_title = "🖥️ Terminal"
                terminal_width = len(terminal_title) + 4
                if current_x <= x < current_x + terminal_width:
                    return self.terminal_tab_id
                current_x += terminal_width

            # Then check markdown preview tabs
            tab_ids = list(self.open_files.keys())
            for tab_id in tab_ids:
                if tab_id in self.open_files:
                    file_path = self.open_files[tab_id]
                    # Tab title includes 📖 prefix + filename
                    tab_title = f"📖 {file_path.name}"
                    estimated_width = len(tab_title) + 4  # Add padding

                    if current_x <= x < current_x + estimated_width:
                        return tab_id
                    current_x += estimated_width
        return None
