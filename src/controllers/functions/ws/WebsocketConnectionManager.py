from fastapi import WebSocket
import asyncio

class WebsocketConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []
    self.active_connections_map: dict[str, WebSocket] = {}
    self.lifo_cache_map: dict[str, dict] = {}

  async def connect(self, websocket: WebSocket, api_uid: str):
    print("\nwebsocket_endpoint >> ", "connect", api_uid)
    await websocket.accept()
    self.active_connections.append(websocket)
    self.active_connections_map[api_uid] = self.active_connections_map[api_uid] if api_uid in self.active_connections_map else websocket
    print("\nwebsocket_endpoint >> ", "self.active_connections_map", self.active_connections_map)

  def disconnect(self, websocket: WebSocket, api_uid: str):
    print("\nwebsocket_endpoint >> ", "disconnect", api_uid)
    self.active_connections.remove(websocket)
    del self.active_connections_map[api_uid]
    if api_uid in self.lifo_cache_map:
      del self.lifo_cache_map[api_uid]

  async def send_personal_message(self, message: str, api_uid: str, is_lifo: bool = False):
    if (api_uid in self.active_connections_map):
      if (is_lifo):
        self.lifo_cache_map[api_uid] = message
      else:
        # print("websocket_endpoint >> ", "send_personal_message", api_uid)
        print("pm", end="", flush=True)
        await self.active_connections_map[api_uid].send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await connection.send_text(message)


wsConnectionManager: WebsocketConnectionManager = WebsocketConnectionManager()


async def lifo_engine():
    while True:
        # Do some async operations here
        api_uids = list(wsConnectionManager.lifo_cache_map.keys())
        for api_uid in api_uids:
            # print("websocket_endpoint >> ", "send_personal_message (lifo_engine)", api_uid)
            print("pm_lifo", end="", flush=True)
            await wsConnectionManager.active_connections_map[api_uid].send_text(wsConnectionManager.lifo_cache_map[api_uid])
            del wsConnectionManager.lifo_cache_map[api_uid]


        # Wait for 0.25 seconds
        await asyncio.sleep(0.25)


asyncio.ensure_future(lifo_engine())
