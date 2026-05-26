import json

from fastapi import WebSocket


class FileStatusConnectionManager:
  def __init__(self):
    self.active_connections_map: dict[str, dict[str, WebSocket]] = {}

  async def connect(self, websocket: WebSocket, party_id: str, client_uid: str):
    await websocket.accept()
    party_connections = self.active_connections_map.setdefault(party_id, {})
    party_connections[client_uid] = websocket

  def disconnect(self, party_id: str, client_uid: str):
    party_connections = self.active_connections_map.get(party_id, {})
    if client_uid in party_connections:
      del party_connections[client_uid]
    if len(party_connections) == 0 and party_id in self.active_connections_map:
      del self.active_connections_map[party_id]

  async def broadcast_to_party(self, party_id: str, payload: dict):
    party_connections = self.active_connections_map.get(party_id, {})
    stale_client_uids = []

    for client_uid, websocket in party_connections.items():
      try:
        await websocket.send_text(json.dumps(payload))
      except Exception:
        stale_client_uids.append(client_uid)

    for client_uid in stale_client_uids:
      self.disconnect(party_id, client_uid)


fileStatusConnectionManager: FileStatusConnectionManager = FileStatusConnectionManager()