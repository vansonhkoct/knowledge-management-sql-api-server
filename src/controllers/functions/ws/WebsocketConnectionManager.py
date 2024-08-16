from fastapi import WebSocket

class WebsocketConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []
    self.active_connections_map: dict[str, WebSocket] = {}

  async def connect(self, websocket: WebSocket, api_uid: str):
    print("websocket_endpoint >> ", "connect", api_uid)
    await websocket.accept()
    self.active_connections.append(websocket)
    self.active_connections_map[api_uid] = self.active_connections_map[api_uid] if api_uid in self.active_connections_map else websocket
    print("websocket_endpoint >> ", "self.active_connections_map", self.active_connections_map)

  def disconnect(self, websocket: WebSocket, api_uid: str):
    print("websocket_endpoint >> ", "disconnect", api_uid)
    self.active_connections.remove(websocket)
    del self.active_connections_map[api_uid]

  async def send_personal_message(self, message: str, api_uid: str):
    print("websocket_endpoint >> ", "sss", api_uid)
    if (api_uid in self.active_connections_map):
      print("websocket_endpoint >> ", "send_personal_message", api_uid)
      await self.active_connections_map[api_uid].send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await connection.send_text(message)


wsConnectionManager: WebsocketConnectionManager = WebsocketConnectionManager()


