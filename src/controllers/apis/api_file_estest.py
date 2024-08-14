import traceback
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request, Body, WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

import nltk
nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')
import json

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../")

from controllers.functions._generic.fileutils import UploadFileRecord
from controllers.functions._generic.fileutils import upload_file_write_to_upload_folder
from controllers.functions._generic.fileutils import remove_file_from_upload_folder
from controllers.functions._generic.fileutils import load_uploaded_file
from controllers.functions.file.file import bootstrapImportESBundle
from controllers.functions.file.file import create_entry_file
from controllers.functions.file.file import on_move_file
from controllers.functions.file.file import on_remove_file
from controllers.functions.file.file import on_upload_file
from controllers.functions.file.file import fetch_es_docs
from controllers.functions.user.userauth_session import fetch_loggedin_user_info

import controllers.functions.esbundle.es_chatllm as ESChatLLM
from controllers.functions.esbundle.include.ElasticSearchDao.ESVo import ESVoDocSearch, ESVoDocInsert
from controllers.functions.esbundle.include.ChatLLMDao.LLMVo import LLMVoAskQuestion


router = APIRouter(prefix="/api/v1")

from models.master import File, KMFile
from models.master import Category, KMCategory


TAG_C001 = "C_FILE_ESTEST001"
TAG_E001 = "E_FILE_ESTEST001"

@router.post("/file_estest/initializeES")
async def initializeES(
  request: Request,
):
  try:
    bootstrapImportESBundle()
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": {
      },
    }

  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.post("/file_estest/load_file")
async def load_file(
  request: Request,
):
  data = await request.json()
  filename = data["filename"]
  
  try:
    with load_uploaded_file(filename=filename) as r_file:
      return {
        "success": True,
        "message": TAG_C001,
        "data": {
          "item": "___FILE_ESTEST___",
          "r_file": r_file.name,
        },
      }

  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )



@router.post("/file_estest/load_api_file")
async def load_api_file(
  request: Request,
):
  data = await request.json()
  id = data["id"]


  item = (
    await File
      .filter(Q(**{
        "id": id,
      }))
      .prefetch_related()
      .first()
  )

  es_docs = []
  r_file = None
  
  if (item != None):
    es_docs = await fetch_es_docs(
      party_id=item.party_id,
      file=item,
    )

    r_file = load_uploaded_file(filename=item.filename)

  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "item": item,
      "r_file": r_file.name,
      "es_docs": es_docs,
    },
  }




@router.post("/file_estest/test_reparse_file_as_docs")
async def test_reparse_file_as_docs(
  request: Request,
):
  data = await request.json()
  id = data["id"]


  item = (
    await File
      .filter(Q(**{
        "id": id,
      }))
      .prefetch_related()
      .first()
  )

  es_docs = []
  r_file = None
  
  if (item != None):
    es_docs = await fetch_es_docs(
      party_id=item.party_id,
      file=item,
    )

    r_file = load_uploaded_file(filename=item.filename)

    if r_file is not None:

      print("\n==== PART 1 ===\n")

      
      print("\n==== PART 2 ===\n")
      
      text_data, text = await ESChatLLM.async_extract_pdf_file_to_text(
        filename=item.filename,
        file=r_file,
        meta_data_mapping = {
            "document_file_id": str(item.id) if item.id != None else "",
            "document_category": str(item.category_id) if item.category_id != None else "",
        }
      )
      
      print("\n==== PART 3 ===\n")

      document_tags = []
      document_title = None
      document_summary = None
      document_remarks = None

      if es_docs is not None and len(es_docs) > 0:
        document_tags = es_docs[0]["metadata"]["document_tags"] if ("metadata" in es_docs[0] and "document_tags" in es_docs[0]["metadata"] ) else document_tags
        document_title = es_docs[0]["metadata"]["document_title"] if ("metadata" in es_docs[0] and "document_title" in es_docs[0]["metadata"] ) else document_title
        document_summary = es_docs[0]["metadata"]["document_summary"] if ("metadata" in es_docs[0] and "document_summary" in es_docs[0]["metadata"] ) else document_summary
        document_remarks = es_docs[0]["metadata"]["document_remarks"] if ("metadata" in es_docs[0] and "document_remarks" in es_docs[0]["metadata"] ) else document_remarks

      print("\n==== PART 4 ===\n")

      results = await ESChatLLM.bot_es_add_document(
        index_name=str(item.party_id),
        text_data=text_data,
        text=text,
        extra_metadata={
            "document_tags": document_tags,
            "document_title": document_title,
            "document_summary": document_summary,
            "document_remarks": document_remarks,
        },
        is_testrun=False,
      )

  return {
    "success": True,
    "message": TAG_C001,
    "esparsedata": results,
    "data": {
      "item": item,
      "r_file": r_file.name,
      "es_docs": es_docs,
    },
  }


@router.post("/file_estest/test_reparse_all_files_as_docs")
async def test_reparse_all_files_as_docs(
  request: Request,
):
  data = await request.json()


  items = (
    await File
      .filter(Q(**{
        "category_id": "ed6042cf-17ac-4e9c-b224-23273f8a5f80",
      }))
  )



  print("\n==== PART 1 ===\n")


  
  for item in items:
    
    es_docs = []
    r_file = None
    
    if (item != None):
      es_docs = await fetch_es_docs(
        party_id=item.party_id,
        file=item,
      )

      r_file = load_uploaded_file(filename=item.filename)
      
      if r_file is not None:

        print("\n==== PART 2 ===\n")
        
        text_data, text = await ESChatLLM.async_extract_pdf_file_to_text(
          filename=item.filename,
          file=r_file,
          meta_data_mapping = {
              "document_file_id": str(item.id) if item.id != None else "",
              "document_category": str(item.category_id) if item.category_id != None else "",
          }
        )
        
        print("\n==== PART 3 ===\n")

        document_tags = []
        document_title = None
        document_summary = None
        document_remarks = None

        if es_docs is not None and len(es_docs) > 0:
          document_tags = es_docs[0]["metadata"]["document_tags"] if ("metadata" in es_docs[0] and "document_tags" in es_docs[0]["metadata"] ) else document_tags
          document_title = es_docs[0]["metadata"]["document_title"] if ("metadata" in es_docs[0] and "document_title" in es_docs[0]["metadata"] ) else document_title
          document_summary = es_docs[0]["metadata"]["document_summary"] if ("metadata" in es_docs[0] and "document_summary" in es_docs[0]["metadata"] ) else document_summary
          document_remarks = es_docs[0]["metadata"]["document_remarks"] if ("metadata" in es_docs[0] and "document_remarks" in es_docs[0]["metadata"] ) else document_remarks

        print("\n==== PART 4 ===\n")

        results = await ESChatLLM.bot_es_add_document(
          index_name=str(item.party_id),
          text_data=text_data,
          text=text,
          extra_metadata={
              "document_tags": document_tags,
              "document_title": document_title,
              "document_summary": document_summary,
              "document_remarks": document_remarks,
          },
          is_testrun=False,
        )

  return {
    "success": True,
    "message": TAG_C001,
    # "esparsedata": {
    #   "ids": ids,
    #   "docs": docs,
    #   "index_name": index_name,
    # },
    # "data": {
    #   "item": item,
    #   "r_file": r_file.name,
    #   "es_docs": es_docs,
    # },
  }



@router.post("/file_estest/test_search_by_multi_vector_query_strings")
async def test_search_by_multi_vector_query_strings(
  request: Request,
):
  data = await request.json()
  
  

  result = await ESChatLLM.bot_es_search_multi_vector(
    index_name=data["index_name"],
    query_strings=data["query_strings"],
    knn_boosts=data["knn_boosts"],
    document_category=data["document_category"],
    k=data["k"],
    num_candidates=data["num_candidates"],
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
  }
  
  


@router.post("/file_estest/get_es_doc_ids_by_document_file_id")
async def test_get_es_doc_ids_by_document_file_id(
  request: Request,
):
  data = await request.json()

  result = await ESChatLLM.bot_es_get_document_es_ids_by_document_file_id(
    index_name=data["index_name"],
    document_file_id=data["document_file_id"],
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
  }
  
  
  
@router.post("/file_estest/get_es_doc_by_id")
async def test_get_es_doc_ids_by_document_file_id(
  request: Request,
):
  data = await request.json()

  result = await ESChatLLM.bot_es_get_document_by_id(
    index_name=data["index_name"],
    id=data["id"],
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
  }
  



@router.post("/file_estest/test_llm_ask_question")
async def test_bot_llm_ask_question(
  request: Request,
):

  data = await request.json()
  
  vo_es = ESVoDocSearch(
    index_name = data["index_name"],
    question = data["question"] if "question" in data else None,
    query_strings = data["query_strings"] if "query_strings" in data else None,
    query_vectors = data["query_vectors"] if "query_vectors" in data else None,
    knn_boosts = data["knn_boosts"] if "knn_boosts" in data else None,
    document_category = data["document_category"],
    k = data["k"] if "k" in data else 10,
    num_candidates = data["num_candidates"] if "num_candidates" in data else 100,
    data_strategy = data["data_strategy"] if "data_strategy" in data else None,
    data_portion_type = data["data_portion_type"] if "data_portion_type" in data else None,
    must_match_document_category = data["must_match_document_category"] if "must_match_document_category" in data else True,
    should_match_document_tags = data["should_match_document_tags"] if "should_match_document_tags" in data else 0,
    should_match_document_title = data["should_match_document_title"] if "should_match_document_title" in data else 0,
    should_match_document_summary = data["should_match_document_summary"] if "should_match_document_summary" in data else 0,
    should_match_document_text = data["should_match_document_text"] if "should_match_document_text" in data else 0,
  )

  es_result = await ESChatLLM.bot_es_search_multi_vector(
    vo=vo_es,
  )


  def do_filter_es_result_item(it):
    if it["score"] / it["record_max_score"] < 0.75:
      return False
    if it["score"] / it["possible_max_score"] < 0.60:
      return False
    return True

  filtered_es_result = [ it for it in es_result if ( do_filter_es_result_item(it) )]
  
  
  # Group Using a dictionary-based approach
  group_filtered_es_result = {}
  for it in filtered_es_result:
      if it["file_id"] not in group_filtered_es_result:
          group_filtered_es_result[it["file_id"]] = []

      group_filtered_es_result[it["file_id"]].append(it)


  aggregated_context = []
  
  for key_file_id in group_filtered_es_result.keys():
    document_header = f"\n\n---------\n{it["metadata"]["document_remarks"]}\n{it["metadata"]["document_title"]}\n{it["metadata"]["document_summary"]}\n"
    document_footer = f"\n\n----------\n\n"
    document_content_array = [ it["content"] for it in group_filtered_es_result[key_file_id] ]
    document_content = f"\n ... \n { "\n ... \n".join(document_content_array) } \n ... \n"

    aggregated_context.append(document_header)
    aggregated_context.append(document_content)
    aggregated_context.append(document_footer)
    

  def do_emit_to_uid(topic, dict, uid):
    wsConnectionManager.send_personal_message(
      message=json.dumps({
        topic: topic,
        dict: dict,
        }), 
      api_uid=uid
      )


  vo_llm = LLMVoAskQuestion(
    prompt = "".join([
      "已知信息：\n",
      aggregated_context,
      "\n\n根據上述已知信息，簡潔和專業的來回答用户的問題。如果無法從中得到答案，請説 “根據已知信息無法回答該問題” 或 “沒有提供足夠的相關信息”，不允許在答案中添加其他任何成分，答案請使用中文。 問題是：",
      data["question"],
    ]),
    llm_max_token = data["llm_max_token"] if "llm_max_token" in data else 8192,
    llm_temperature = data["llm_temperature"] if "llm_temperature" in data else 0.05,
    llm_top_p = data["llm_top_p"] if "llm_top_p" in data else 0.8,
    llm_history_len = data["llm_history_len"] if "llm_history_len" in data else 3,
    api_uid = data["api_uid"] if "api_uid" in data else "",
    emit_to_uid = do_emit_to_uid,
  )

  llm_answer_result = await ESChatLLM.bot_llm_ask_question(
    vo=vo_llm,
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": llm_answer_result,
  }
  
  







class WebsocketConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.active_connections_map: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, api_uid: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.active_connections_map[api_uid] = self.active_connections_map[api_uid] if api_uid in self.active_connections_map else self.active_connections_map[api_uid]

    def disconnect(self, websocket: WebSocket, api_uid: str):
        self.active_connections.remove(websocket)
        del self.active_connections_map[api_uid]

    async def send_personal_message(self, message: str, api_uid: str):
        if (api_uid in self.active_connections_map):
            await self.active_connections_map[api_uid].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


wsConnectionManager = WebsocketConnectionManager()




@router.websocket("/ws/{api_uid}/chatllm_answering/")
async def websocket_endpoint(websocket: WebSocket, api_uid: str):
    await wsConnectionManager.connect(websocket=websocket, api_uid=api_uid)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        wsConnectionManager.disconnect(websocket, api_uid=api_uid)


