from pathlib import Path
from typing import Dict, Optional, Union
from os import PathLike

from textual.containers import Container
from textual.events import Key
from textual.widget import Widget
from textual.widgets import TabbedContent, TabPane, TextArea


class TabbedTextArea(Widget):
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
        text_area = TextArea(
            text=content,
            read_only=False,
            id=f"editor_{tab_id}"
        )
        
        # Set language based on file extension
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
        
        # Remove the tab
        self.tabbed_content.remove_pane(tab_id)
        
        # Remove from file mapping
        del self.open_files[tab_id]
        
        return True
    
    def has_open_files(self) -> bool:
        """Check if there are any open files."""
        return len(self.open_files) > 0
    
    def on_key(self, event: Key) -> None:
        """Handle key events."""
        # Allow Ctrl+W to close current tab
        if event.key == "ctrl+w":
            self.close_tab()
            event.prevent_default()
        else:
            # Pass other events to the active editor
            editor = self.get_active_editor()
            if editor:
                editor.post_message(event)
