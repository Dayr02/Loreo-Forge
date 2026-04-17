extends Node

const OUTBOUND_DIR := "user://../../data/bridge/outbound"

func read_json_file(file_name: String) -> Dictionary:
  var path := "%s/%s" % [OUTBOUND_DIR, file_name]
  if not FileAccess.file_exists(path):
    return {}
  var file := FileAccess.open(path, FileAccess.READ)
  if file == null:
    return {}
  var text := file.get_as_text()
  file.close()
  var parsed := JSON.parse_string(text)
  return parsed if typeof(parsed) == TYPE_DICTIONARY else {}

func get_latest_command() -> Dictionary:
  return read_json_file("game_command.json")
