import traceback
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from src.controllers.functions.ws.WebsocketConnectionManager import wsConnectionManager

router = APIRouter(prefix="/api/v1")



@router.websocket("/ws/{api_uid}/chatllm_answering")
async def websocket_endpoint(websocket: WebSocket, api_uid: str):
  await wsConnectionManager.connect(websocket=websocket, api_uid=api_uid)
  try:
    while True:
      data = await websocket.receive_text()
      await wsConnectionManager.send_personal_message(message=data, api_uid=api_uid)
  except WebSocketDisconnect as e:
    print("websocket_endpoint >> ", e)
    wsConnectionManager.disconnect(websocket, api_uid=api_uid)


