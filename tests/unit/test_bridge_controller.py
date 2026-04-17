from __future__ import annotations

import json

from core.bridge_controller import BridgeController


def test_send_command_writes_outbound_file(isolated_paths):
    controller = BridgeController()
    controller.send_command("load_scene", {"scene_name": "hub"})
    command_file = controller.outbound_dir / "game_command.json"
    payload = json.loads(command_file.read_text(encoding="utf-8"))
    assert payload["command_type"] == "load_scene"
    assert payload["payload"]["scene_name"] == "hub"


def test_poll_inbound_reads_new_events(isolated_paths):
    controller = BridgeController()
    inbound_file = controller.inbound_dir / "game_event.json"
    inbound_file.write_text(
        json.dumps({"event_type": "xp_earned", "payload": {"amount": 15}}),
        encoding="utf-8",
    )
    events = controller.poll_inbound()
    assert len(events) == 1
    assert events[0]["event_type"] == "xp_earned"
