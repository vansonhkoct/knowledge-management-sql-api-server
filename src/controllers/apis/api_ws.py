import traceback
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from src.controllers.functions.ws.WebsocketConnectionManager import wsConnectionManager
from src.controllers.functions.ws.FileStatusConnectionManager import fileStatusConnectionManager

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


@router.websocket("/ws/file_status/{party_id}/{client_uid}")
async def websocket_file_status_endpoint(websocket: WebSocket, party_id: str, client_uid: str):
  await fileStatusConnectionManager.connect(
    websocket=websocket,
    party_id=party_id,
    client_uid=client_uid,
  )
  try:
    while True:
      await websocket.receive_text()
  except WebSocketDisconnect:
    fileStatusConnectionManager.disconnect(party_id=party_id, client_uid=client_uid)


