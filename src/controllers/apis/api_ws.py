import os
import traceback
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from src.controllers.functions.ws.WebsocketConnectionManager import wsConnectionManager
from src.controllers.functions.ws.FileStatusConnectionManager import fileStatusConnectionManager
from src.controllers.functions.ws.auth import authenticate_party_socket

router = APIRouter(prefix="/api/v1")



@router.websocket("/ws/{api_uid}/chatllm_answering")
async def websocket_endpoint(websocket: WebSocket, api_uid: str):
  if os.getenv("APP_ENV", "development").lower() == "production":
    await websocket.close(code=1008)
    return
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
  user = await authenticate_party_socket(websocket, party_id)
  if user is None:
    await websocket.close(code=1008)
    return
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

