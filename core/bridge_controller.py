"""PyQt5 to Godot bridge controller."""

from __future__ import annotations

import json
import socket
import subprocess
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from config.settings import settings
from utils.logger import LoggerMixin

try:
    from PyQt5.QtCore import QObject, QTimer, pyqtSignal
except ImportError:  # pragma: no cover
    class QObject:  # type: ignore
        pass

    class _Signal:
        def __init__(self) -> None:
            self._subscribers: List[Callable[..., None]] = []

        def connect(self, callback: Callable[..., None]) -> None:
            self._subscribers.append(callback)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for callback in list(self._subscribers):
                callback(*args, **kwargs)

    def pyqtSignal(*_args: Any, **_kwargs: Any) -> _Signal:  # type: ignore
        return _Signal()

    class QTimer:  # type: ignore
        def __init__(self) -> None:
            self.timeout = _Signal()

        def setInterval(self, _interval: int) -> None:
            return None

        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None


class BridgeController(QObject, LoggerMixin):
    """Owns the Godot subprocess and JSON/socket IPC channels."""

    event_received = pyqtSignal(dict)
    godot_started = pyqtSignal()
    godot_stopped = pyqtSignal()

    def __init__(self, parent: Optional[QObject] = None):
        try:
            super().__init__(parent)
        except TypeError:  # pragma: no cover - fallback QObject path
            super().__init__()
        self.bridge_root = settings.BRIDGE_DIR
        self.outbound_dir = settings.BRIDGE_OUTBOUND_DIR
        self.inbound_dir = settings.BRIDGE_INBOUND_DIR
        self.godot_process: Optional[subprocess.Popen] = None
        self.socket_enabled = False
        self._server_socket: Optional[socket.socket] = None
        self._client_socket: Optional[socket.socket] = None
        self._socket_thread: Optional[threading.Thread] = None
        self._stop_socket = threading.Event()
        self._file_timestamps: Dict[Path, float] = {}
        self.poll_timer = QTimer()
        self.poll_timer.setInterval(100)
        self.poll_timer.timeout.connect(self.poll_inbound)
        self.ensure_bridge_layout()

    def ensure_bridge_layout(self) -> None:
        for directory in (
            self.bridge_root,
            self.outbound_dir,
            self.inbound_dir,
            settings.GAME_STATE_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    def start_socket_server(self) -> None:
        if self._server_socket is not None:
            return

        self._stop_socket.clear()
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((settings.bridge_host, settings.bridge_port))
        server.listen(1)
        server.settimeout(0.25)
        self._server_socket = server

        def _serve() -> None:
            while not self._stop_socket.is_set():
                try:
                    client, _address = server.accept()
                    client.settimeout(0.25)
                    self._client_socket = client
                    self.socket_enabled = True
                    while not self._stop_socket.is_set():
                        try:
                            data = client.recv(65535)
                        except socket.timeout:
                            continue
                        if not data:
                            break
                        for line in data.decode("utf-8").splitlines():
                            if not line.strip():
                                continue
                            try:
                                payload = json.loads(line)
                            except json.JSONDecodeError:
                                self.log_warning("Received invalid JSON from Godot socket")
                                continue
                            self.event_received.emit(payload)
                    client.close()
                except socket.timeout:
                    continue
                except OSError:
                    break
                finally:
                    self._client_socket = None
                    self.socket_enabled = False

        self._socket_thread = threading.Thread(target=_serve, daemon=True)
        self._socket_thread.start()

    def start_godot(self, scene_name: str = "", initial_data: Optional[Dict[str, Any]] = None) -> bool:
        self.ensure_bridge_layout()
        self.start_socket_server()
        if initial_data:
            self.write_outbound("story_context.json", initial_data)
        self.write_outbound(
            "game_command.json",
            {"command_type": "load_scene", "payload": {"scene_name": scene_name}},
        )
        if self.godot_process and self.godot_process.poll() is None:
            self.send_command("load_scene", {"scene_name": scene_name})
            return True

        executable = settings.godot_executable_path or "godot"
        command = [executable, "--path", str(settings.GODOT_PROJECT_DIR)]
        if scene_name:
            command.append(scene_name)

        try:
            self.godot_process = subprocess.Popen(command)
        except OSError as exc:
            self.log_error(f"Failed to launch Godot: {exc}")
            return False

        self.poll_timer.start()
        self.godot_started.emit()
        return True

    def send_command(self, command_type: str, payload: Optional[Dict[str, Any]] = None) -> None:
        message = {"command_type": command_type, "payload": payload or {}}
        self.write_outbound("game_command.json", message)
        if self.socket_enabled and self._client_socket is not None:
            try:
                self._client_socket.sendall((json.dumps(message) + "\n").encode("utf-8"))
            except OSError:
                self.socket_enabled = False

    def write_outbound(self, file_name: str, payload: Dict[str, Any]) -> Path:
        path = self.outbound_dir / file_name
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        self._file_timestamps[path] = path.stat().st_mtime
        return path

    def poll_inbound(self) -> List[Dict[str, Any]]:
        events: List[Dict[str, Any]] = []
        for path in self.inbound_dir.glob("*.json"):
            try:
                mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue
            if self._file_timestamps.get(path) == mtime:
                continue
            self._file_timestamps[path] = mtime
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                self.log_warning(f"Skipping invalid inbound bridge file: {path.name}")
                continue
            events.append(payload)
            self.event_received.emit(payload)
        return events

    def stop_godot(self) -> None:
        self.send_command("shutdown", {})
        if self.godot_process and self.godot_process.poll() is None:
            self.godot_process.terminate()
            try:
                self.godot_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.godot_process.kill()
        self.godot_process = None
        self.poll_timer.stop()
        self._stop_socket.set()
        if self._client_socket is not None:
            self._client_socket.close()
            self._client_socket = None
        if self._server_socket is not None:
            self._server_socket.close()
            self._server_socket = None
        self.socket_enabled = False
        self.godot_stopped.emit()
