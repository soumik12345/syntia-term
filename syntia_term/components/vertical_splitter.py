from textual.events import MouseDown, MouseMove, MouseUp
from textual.widget import Widget


class VerticalSplitter(Widget):
    """A 1-cell wide vertical splitter that resizes the widget to its left."""

    DEFAULT_CSS = """
    VerticalSplitter {
        width: 1;
        height: 1fr;
        background: $surface;  /* faint bar color */
    }
    
    VerticalSplitter:hover {
        background: $primary;  /* highlighted color on hover */
        opacity: 0.7;
    }
    """

    def render(self):
        return ""

    _dragging: bool = False
    _start_x: int = 0
    _start_left_width: int = 0

    def on_mouse_down(self, event: MouseDown) -> None:
        self._dragging = True
        self.capture_mouse(True)
        left = self._left_widget()
        self._start_left_width = left.size.width
        self._start_x = event.screen_x

    def on_mouse_move(self, event: MouseMove) -> None:
        if not self._dragging:
            return
        left = self._left_widget()
        parent_width = self.parent.size.width
        delta = event.screen_x - self._start_x
        new_width = max(16, min(parent_width - 10, self._start_left_width + delta))
        left.styles.width = new_width
        left.refresh(layout=True)

    def on_mouse_up(self, event: MouseUp) -> None:
        if self._dragging:
            self._dragging = False
            self.capture_mouse(False)

    def _left_widget(self) -> Widget:
        idx = self.parent.children.index(self)
        return self.parent.children[idx - 1]
