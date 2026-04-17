extends Node

const HOST := "127.0.0.1"
const PORT := 27182

var peer := StreamPeerTCP.new()
var socket_enabled := false

func _ready() -> void:
  var result := peer.connect_to_host(HOST, PORT)
  socket_enabled = result == OK

func send_message(payload: Dictionary) -> void:
  if not socket_enabled:
    return
  peer.put_utf8_string(JSON.stringify(payload) + "\n")
