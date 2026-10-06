from fastapi import WebSocket
import asyncio

class WebsocketConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []
    self.active_connections_map: dict[str, WebSocket] = {}
    self.lifo_cache_map: dict[str, str] = {}
    self.lifo_flush_tasks: dict[str, asyncio.Task] = {}

  async def connect(self, websocket: WebSocket, api_uid: str):
    print("\nwebsocket_endpoint >> ", "connect", api_uid)
    await websocket.accept()
    if websocket not in self.active_connections:
      self.active_connections.append(websocket)
    self.active_connections_map[api_uid] = websocket
    print("\nwebsocket_endpoint >> ", "self.active_connections_map", self.active_connections_map)

  def disconnect(self, websocket: WebSocket, api_uid: str):
    print("\nwebsocket_endpoint >> ", "disconnect", api_uid)
    if websocket in self.active_connections:
      self.active_connections.remove(websocket)

    if self.active_connections_map.get(api_uid) is websocket:
      del self.active_connections_map[api_uid]
      self.lifo_cache_map.pop(api_uid, None)
      lifo_task = self.lifo_flush_tasks.pop(api_uid, None)
      if lifo_task is not None:
        lifo_task.cancel()

  async def send_personal_message(self, message: str, api_uid: str, is_lifo: bool = False):
    if (api_uid in self.active_connections_map):
      if (is_lifo):
        self.lifo_cache_map[api_uid] = message
        lifo_task = self.lifo_flush_tasks.get(api_uid)
        if lifo_task is None or lifo_task.done():
          self.lifo_flush_tasks[api_uid] = asyncio.create_task(self._flush_lifo_messages(api_uid))
      else:
        # print("websocket_endpoint >> ", "send_personal_message", api_uid)
        print("pm", end="", flush=True)
        await self.active_connections_map[api_uid].send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await connection.send_text(message)

  async def _flush_lifo_messages(self, api_uid: str):
    try:
      while True:
        await asyncio.sleep(0.05)

        if api_uid not in self.active_connections_map:
          self.lifo_cache_map.pop(api_uid, None)
          return

        message = self.lifo_cache_map.pop(api_uid, None)
        if message is None:
          return

        print("pm_lifo", end="", flush=True)
        await self.active_connections_map[api_uid].send_text(message)

        if api_uid not in self.lifo_cache_map:
          return
    finally:
      task = self.lifo_flush_tasks.get(api_uid)
      if task is not None and task.done():
        self.lifo_flush_tasks.pop(api_uid, None)


wsConnectionManager: WebsocketConnectionManager = WebsocketConnectionManager()
