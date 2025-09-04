from textual import events
from textual_terminal import Terminal


class SyntiaTerminal(Terminal):
    """Custom Terminal widget that allows app-level keybindings to bubble up."""

    # Define keybindings that should bubble up to the app level
    APP_KEYBINDINGS = {
        "ctrl+s",  # Save file
        "ctrl+w",  # Close tab
        "ctrl+t",  # Toggle terminal
        "ctrl+q",  # Quit
    }

    async def on_key(self, event: events.Key) -> None:
        """Handle key events, allowing app-level keybindings to bubble up."""
        if self.emulator is None:
            return

        # Allow app-level keybindings to bubble up by not stopping the event
        if event.key in self.APP_KEYBINDINGS:
            return  # Don't call event.stop(), let it bubble up to app

        if event.key == "ctrl+f1":
            # release focus from widget: because event.stop() follows, releasing
            # focus would not be possible without mouse click.
            #
            # OPTIMIZE: make the key to release focus configurable
            self.app.set_focus(None)
            return

        # For all other keys, handle them normally (send to terminal)
        event.stop()
        char = self.ctrl_keys.get(event.key) or event.character
        if char:
            await self.send_queue.put(["stdin", char])
