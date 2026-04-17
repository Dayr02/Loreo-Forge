"""Qt widget wrapper for the Godot runtime."""

from __future__ import annotations

from typing import Dict, Optional

from core.bridge_controller import BridgeController

try:
    from PyQt5.QtCore import pyqtSignal
    from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    class QWidget:  # type: ignore
        def __init__(self, *_args, **_kwargs) -> None:
            pass

    class QLabel:  # type: ignore
        def __init__(self, text: str = "") -> None:
            self._text = text

        def setWordWrap(self, _value: bool) -> None:
            return None

        def setText(self, value: str) -> None:
            self._text = value

    class QVBoxLayout:  # type: ignore
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def addWidget(self, *_args, **_kwargs) -> None:
            return None

    class _Signal:
        def __init__(self) -> None:
            self._subscribers = []

        def connect(self, callback):
            self._subscribers.append(callback)

        def emit(self, *args, **kwargs):
            for callback in list(self._subscribers):
                callback(*args, **kwargs)

    def pyqtSignal(*_args, **_kwargs):  # type: ignore
        return _Signal()


class GodotWidget(QWidget):
    godot_ready = pyqtSignal()
    godot_closed = pyqtSignal()
    godot_event_received = pyqtSignal(dict)

    def __init__(self, bridge_controller: Optional[BridgeController] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.bridge_controller = bridge_controller or BridgeController()
        self.bridge_controller.event_received.connect(self.godot_event_received.emit)
        self.bridge_controller.godot_started.connect(self.godot_ready.emit)
        self.bridge_controller.godot_stopped.connect(self.godot_closed.emit)

        layout = QVBoxLayout(self)
        self.placeholder_label = QLabel(
            "Godot runtime not embedded yet. Launching as managed external window."
        )
        self.placeholder_label.setWordWrap(True)
        layout.addWidget(self.placeholder_label)

    def launch_scene(self, scene_name: str, initial_data: Optional[Dict] = None) -> bool:
        success = self.bridge_controller.start_godot(scene_name, initial_data or {})
        if success:
            self.placeholder_label.setText(f"Godot running scene: {scene_name or 'default'}")
        return success

    def shutdown(self) -> None:
        self.bridge_controller.stop_godot()
        self.placeholder_label.setText("Godot stopped.")
