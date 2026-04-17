extends Node

const INBOUND_DIR := "user://../../data/bridge/inbound"

func write_json_file(file_name: String, payload: Dictionary) -> void:
  DirAccess.make_dir_recursive_absolute(INBOUND_DIR)
  var path := "%s/%s" % [INBOUND_DIR, file_name]
  var file := FileAccess.open(path, FileAccess.WRITE)
  if file == null:
    return
  file.store_string(JSON.stringify(payload))
  file.close()

func emit_ready_event() -> void:
  write_json_file("game_event.json", {
    "event_type": "godot_ready",
    "payload": {"source": "godot"},
  })
