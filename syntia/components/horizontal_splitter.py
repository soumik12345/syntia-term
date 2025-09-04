from textual.events import MouseDown, MouseMove, MouseUp
from textual.widget import Widget


class HorizontalSplitter(Widget):
    """A 1-cell high horizontal splitter that resizes the widget below it."""

    DEFAULT_CSS = """
    HorizontalSplitter {
        height: 1;
        width: 1fr;
        background: $surface;  /* faint bar color */
    }
    
    HorizontalSplitter:hover {
        background: $primary;  /* highlighted color on hover */
        opacity: 0.7;
    }
    """

    def render(self):
        return ""

    _dragging: bool = False
    _start_y: int = 0
    _start_below_height: int = 0

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.capture_mouse(True)
        below = self._below_widget()
        self._start_below_height = below.size.height
        self._start_y = event.screen_y

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return
        below = self._below_widget()
        parent_height = self.parent.size.height
        delta = event.screen_y - self._start_y
        new_height = max(5, min(parent_height - 10, self._start_below_height - delta))
        below.styles.height = new_height
        below.refresh(layout=True)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.capture_mouse(False)

    def _below_widget(self) -> Widget:
        idx = self.parent.children.index(self)
        return self.parent.children[idx + 1]
