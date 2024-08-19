import os
import traceback
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request, Body
from fastapi import WebSocket, WebSocketDisconnect
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q
import asyncio
from datetime import datetime
import json
import math

import nltk

from src.controllers.functions._generic.fileutils import UploadFileRecord
from src.controllers.functions._generic.fileutils import upload_file_write_to_upload_folder
from src.controllers.functions._generic.fileutils import remove_file_from_upload_folder
from src.controllers.functions._generic.fileutils import load_uploaded_file
from src.controllers.functions.log.log import add_log_apillm
from src.controllers.functions.file.file import bootstrapImportESBundle
from src.controllers.functions.file.file import create_entry_file
from src.controllers.functions.file.file import on_move_file
from src.controllers.functions.file.file import on_remove_file
from src.controllers.functions.file.file import on_upload_file
from src.controllers.functions.file.file import fetch_es_docs
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.controllers.functions.user.userauth_email import make_password_hash, check_password_hash
from src.controllers.functions.ws.WebsocketConnectionManager import wsConnectionManager
from src.controllers.functions.esbundle import es_chatllm as ESChatLLM
from src.controllers.functions.esbundle.include.ElasticSearchDao.ESVo import ESVoDocSearch, ESVoDocInsert
from src.controllers.functions.esbundle.include.ChatLLMDao.LLMVo import LLMVoAskQuestion
from src.controllers.functions.esbundle.include.ConfigParams import llm_model_enable_api

from src.models.master import File, KMFile
from src.models.master import Category, KMCategory
from src.models.master import Log



nltk.download('punkt_tab')
nltk.download('averaged_perceptron_tagger_eng')


router = APIRouter(prefix="/api/v1")



TAG_C001 = "C_FILE_ESTEST001"
TAG_E001 = "E_FILE_ESTEST001"
TAG_E002 = "E_FILE_ESTEST002"
TAG_E003 = "E_FILE_ESTEST003"



@router.post("/file_estest/make_password_hash")
async def makePasswordHash(
  request: Request,
):
  try:
    data = await request.json()
    password = data["password"]
    
    return {
      "success": True,
      "message": TAG_C001,
      "data": make_password_hash(
        password = password,
      ),
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



@router.post("/file_estest/check_password_hash")
async def checkPasswordHash(
  request: Request,
):
  try:
    data = await request.json()
    password = data["password"]
    password_hash = data["password_hash"]

    return {
      "success": True,
      "message": TAG_C001,
      "data": check_password_hash(
        password_hash = password_hash,
        password = password,
      ),
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
  
  if (item is not None):
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



async def __reparse_file_as_docs(
  item: File,
  r_file,
  is_testrun,
  accept_non_standard_chars: bool = False,
):
  print("\n\n==== PART 1 ===")

  
  print("==== PART 2 ===")
  
  _, text = await ESChatLLM.async_extract_pdf_file_to_text(
    filename=item.filename,
    file=r_file,
    meta_data_mapping = {
        "document_file_id": str(item.id) if item.id is not None else "",
        "document_category": str(item.category_id) if item.category_id is not None else "",
    },
    accept_non_standard_chars = accept_non_standard_chars or False,
  )
  
  print("==== PART 3 ===")

  old_doc_ids = await ESChatLLM.bot_es_get_document_es_ids_by_document_file_id(
    index_name=str(item.party_id),
    document_file_id=item.id,
    data_strategy="1",
  )

  old_doc_ids_strat_2 = await ESChatLLM.bot_es_get_document_es_ids_by_document_file_id(
    index_name=str(item.party_id),
    document_file_id=item.id,
    data_strategy="2",
  )

  print(f"==== PART 3 === obtained old_dic_ids: {len(old_doc_ids)} old indices\n")
  
  extra_metadata = {}
  
  if len(old_doc_ids) > 0:
    doc = await ESChatLLM.bot_es_get_document_by_id(
      index_name=str(item.party_id),
      id=old_doc_ids[0],
    )

    extra_metadata = {
        "document_tags": doc["metadata"]["document_tags"] if "metadata" in doc and "document_tags" in doc["metadata"] else None,
        "document_title": doc["metadata"]["document_title"] if "metadata" in doc and "document_title" in doc["metadata"] else None,
        "document_summary": doc["metadata"]["document_summary"] if "metadata" in doc and "document_summary" in doc["metadata"] else None,
        "document_remarks": doc["metadata"]["document_remarks"] if "metadata" in doc and "document_remarks" in doc["metadata"] else None,
    }
    
  print(f"==== PART 3 === extra metadata: {extra_metadata} \n")
    

  print(f"==== PART 4 === attempting adding into {item.party_id}")
  
  vo = ESVoDocInsert(
    index_name = str(item.party_id),
    text = text,
    extra_metadata = extra_metadata,
    is_testrun = is_testrun,
  )
  
  docs, new_ids, index_name = await ESChatLLM.bot_es_add_document(
    vo=vo,
  )

  if not is_testrun and item is not None and item.id is not None and new_ids is not None:
    print(f"==== PART 4 === attempt save into es_doc_ids of {item.id}")
    item.es_doc_ids = ",".join(new_ids)
    await item.save()
    print(f"==== PART 4 === done save into es_doc_ids of {item.id}: {len(new_ids)} indices")

  
  if not is_testrun and item is not None and item.id is not None:
    print(f"==== PART 4 === attempting remove from {item.party_id}: {len(old_doc_ids_strat_2)} old indices")
          
    for index, id in enumerate(old_doc_ids_strat_2):
      print(f"==== PART 4 === removing {index}/{len(old_doc_ids_strat_2)} - {id}", end = "\r")
      await ESChatLLM.bot_es_delete_document_by_id(
        index_name=str(item.party_id),
        id=id,
      )

    print(f"==== PART 4 === done save into es_doc_ids of {item.id}: {len(new_ids)} indices - Done!")

  print("==== OK ====\n", index_name, "\n")

  return docs, new_ids, index_name




@router.post("/file_estest/test_reparse_file_as_docs")
async def test_reparse_file_as_docs(
  request: Request,
):
  data = await request.json()
  id = data["id"]
  is_testrun = data["is_testrun"]
  accept_non_standard_chars = data["accept_non_standard_chars"] if "accept_non_standard_chars" in data else False

  item = (
    await File
      .filter(Q(**{
        "id": id,
        "is_deleted": False,
      }))
      .prefetch_related()
      .first()
  )

  r_file = None
  
  if (item is not None):

    r_file = load_uploaded_file(filename=item.filename)

    if r_file is not None:

      docs, ids, index_name = await __reparse_file_as_docs(
        item = item,
        r_file = r_file,
        is_testrun = is_testrun,
        accept_non_standard_chars = accept_non_standard_chars,
      )

  return {
    "success": True,
    "message": TAG_C001,
    "esparsedata": {
      "ids": ids,
      "index_name": index_name,
      "docs": docs,
    },
    "data": {
      "item": item,
      "r_file": r_file.name,
    },
  }






@router.post("/file_estest/test_reparse_all_files_as_docs")
async def test_reparse_all_files_as_docs(
  request: Request,
):
  data = await request.json()
  party_id = data["party_id"] if "party_id" in data else None
  is_testrun = data["is_testrun"]

  q = {
    "party_id__isnull": False,
    "is_deleted": False,
  }
  
  if (party_id is not None):
    q["party_id"] = party_id

  items = (
    await File
      .filter(Q(**q))
  )



  file_count = 0
  docs_count = 0
  ids_count = 0
  
  for index, item in enumerate(items):
    
    print(f"test_reparse_all_files_as_docs: {index} / {len(items)}")
    
    r_file = None
    
    if (item is not None):
      r_file = load_uploaded_file(filename=item.filename)
      
      if r_file is not None:
        
        docs, ids, index_name = await __reparse_file_as_docs(
          item = item,
          r_file = r_file,
          is_testrun = is_testrun,
        )
        
        docs_count += len(docs)
        ids_count += len(ids)

    file_count += 1
    
    print({
      "ids_count": ids_count,
      "docs_count": docs_count,
      "file_count": file_count,
    })

  return {
    "success": True,
    "message": TAG_C001,
    "data": {
      "ids_count": ids_count,
      "docs_count": docs_count,
      "file_count": file_count,
    },
  }





@router.post("/file_estest/test_search_by_multi_vector_query_strings")
async def test_search_by_multi_vector_query_strings(
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
    data_vector_query_strategy = data["data_vector_query_strategy"] if "data_vector_query_strategy" in data else 1,
    must_match_document_category = data["must_match_document_category"] if "must_match_document_category" in data else True,
    should_match_document_tags = data["should_match_document_tags"] if "should_match_document_tags" in data else 0,
    should_match_document_title = data["should_match_document_title"] if "should_match_document_title" in data else 0,
    should_match_document_summary = data["should_match_document_summary"] if "should_match_document_summary" in data else 0,
    should_match_document_text = data["should_match_document_text"] if "should_match_document_text" in data else 0,
  )

  es_result = await ESChatLLM.bot_es_search_multi_vector(
    vo=vo_es,
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": es_result,
  }
  
  


@router.post("/file_estest/get_es_doc_ids_by_document_file_id")
async def test_get_es_doc_ids_by_document_file_id(
  request: Request,
):
  data = await request.json()

  result = await ESChatLLM.bot_es_get_document_es_ids_by_document_file_id(
    index_name=data["index_name"],
    document_file_id=data["document_file_id"],
    data_strategy=data["data_strategy"] if "data_strategy" in data else "2",
  )
  
  docs = []
  for id in result:
    doc = await ESChatLLM.bot_es_get_document_by_id(
      index_name=data["index_name"],
      id=id,
    )
    doc["document_header_vector"] = []
    doc["page_content_vector"] = []
    doc["page_content_w_header_vector"] = []
    docs.append(doc)

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
    "esdocs": docs,
  }
  
  
  
@router.post("/file_estest/get_es_doc_by_id")
async def test_get_es_doc_by_id(
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
  




@router.post("/file_estest/bot_es_doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk")
async def test_bot_es_doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
  request: Request,
):
  data = await request.json()

  result = await ESChatLLM.bot_es_doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
    index_name=data["index_name"],
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
  }



is_busy: bool = False




@router.post("/file_estest/test_llm_ask_question")
async def test_bot_llm_ask_question(
  request: Request,
):
  if not llm_model_enable_api:
    raise HTTPException(
      status_code=400,
      detail={
        "message": TAG_E003,
        "error": f"Server LLM ask question ability disabled",
      }
    )
  
  data = await request.json()
    
  global is_busy

  retry_count = 0
  max_retries = (data["max_retries"] if "max_retries" in data else 10) or 10
  retry_delay = 2

  while is_busy and retry_count < max_retries:
      print(f" -- B({retry_count+1}/{max_retries}) -- ", end = "", flush=True)
      await asyncio.sleep(retry_delay)
      retry_count += 1

  if is_busy:
    print(f"\n\nServer busy! Someone is forfeiting test_bot_llm_ask_question -- B({retry_count+1}/{max_retries}) -- ")
    raise HTTPException(
      status_code=400,
      detail={
        "message": TAG_E002,
        "error": f"Server busy (Attempt {retry_count+1}/{max_retries})",
      }
    )


  is_busy = True


  try:
    vo_es = ESVoDocSearch(
      index_name = data["index_name"],
      question = data["question"] if "question" in data else None,
      query_strings = data["query_strings"] if "query_strings" in data else None,
      query_vectors = data["query_vectors"] if "query_vectors" in data else None,
      knn_boosts = data["knn_boosts"] if "knn_boosts" in data else None,
      document_category = data["document_category"],
      document_file_ids = data["document_file_ids"] if "document_file_ids" in data else [],
      k = data["k"] if "k" in data else 10,
      num_candidates = data["num_candidates"] if "num_candidates" in data else 100,
      data_strategy = data["data_strategy"] if "data_strategy" in data else None,
      data_portion_type = data["data_portion_type"] if "data_portion_type" in data else None,
      data_vector_query_strategy = data["data_vector_query_strategy"] if "data_vector_query_strategy" in data else 1,
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
      if os.getenv("ES_REMOVE_LOWSCORE_SEARCH_RESULTS") == "1":
        # if it["score"] / it["record_max_score"] < 0.75:
        #   return False
        # if it["score"] / it["possible_max_score"] < 0.60:
        #   return False
        if it["score"] < 1.7:
          return False
        return True
        
      else:
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
      # print("KEY", key_file_id, group_filtered_es_result[key_file_id])
      document_header = f"""


---------
{group_filtered_es_result[key_file_id][0]["metadata"]["document_remarks"] if "document_remarks" in group_filtered_es_result[key_file_id][0]["metadata"] else ""}
{group_filtered_es_result[key_file_id][0]["metadata"]["document_title"] if "document_title" in group_filtered_es_result[key_file_id][0]["metadata"] else ""}
{group_filtered_es_result[key_file_id][0]["metadata"]["document_summary"] if "document_summary" in group_filtered_es_result[key_file_id][0]["metadata"] else ""}

"""


      document_footer = '\n\n----------\n\n'
      document_content_array = [ it["content"] for it in group_filtered_es_result[key_file_id] ]
      document_content = (
"""

...

""".join(document_content_array)

)
      document_content = f"""

...

{document_content}

...

"""

      aggregated_context.append(document_header)
      aggregated_context.append(document_content)
      aggregated_context.append(document_footer)
    

    prompt = "".join([
      "以下是系統提供的資料段落：\n",
      "".join(aggregated_context),
      # "\n\n根據上述已知信息，簡潔和專業的來回答用户的問題。如果無法從中得到答案，請説 “根據已知信息無法回答該問題” 或 “沒有提供足夠的相關信息”，不允許在答案中添加其他任何成分，答案請使用中文。 以下是問題： 根據已知信息，",
      "\n\n===================\n\n請閱讀上述文件段落，單純依靠系統所提供的信息 (不必考慮信息以外的知識)，並使用中文（不要使用其他語言）告訴我：",
      data["question"],
      "\n\n===================\n\n如果無法從系統提供的資料段落和我的問題匹配，請嘗試參考資料段落，從而建議我可以嘗試詢問的問題。"
    ])
    
    suggested_token = 8192
    prompt_token = math.ceil( len(prompt) * 1.6 )
    input_llm_max_token = data["llm_max_token"] if "llm_max_token" in data else 0
    
    print({
      "suggested_token": suggested_token,
      "prompt_token": prompt_token,
      "input_llm_max_token": input_llm_max_token,
    })
    
    llm_max_token = max(input_llm_max_token, suggested_token, prompt_token)

    vo_llm = LLMVoAskQuestion(
      prompt = prompt,
      history = [],
      llm_model_name = data["llm_model_name"] if "llm_model_name" in data else None,
      llm_max_token = llm_max_token,
      llm_temperature = data["llm_temperature"] if "llm_temperature" in data else 0.03,
      llm_top_p = data["llm_top_p"] if "llm_top_p" in data else 0.92,
      llm_top_k = data["llm_top_k"] if "llm_top_k" in data else 4,
      llm_history_len = data["llm_history_len"] if "llm_history_len" in data else 3,
      api_uid = data["api_uid"] if "api_uid" in data else "",
      emit_to_uid = _do_emit_to_uid,
    )
    
    if not (data["skip_llm"] if "skip_llm" in data else False):
      llm_answer_result = await ESChatLLM.bot_llm_ask_question(
        vo=vo_llm,
      )
    else:
      llm_answer_result = None

    is_busy = False


    add_log_apillm(
      question = vo_es.question,
      index_name = vo_es.index_name,
      prompt = prompt,
      llm_answer_result = llm_answer_result,
      suggested_token = suggested_token,
      prompt_token = prompt_token,
      input_llm_max_token = input_llm_max_token,
      es_result_ids = [{
        "file_id": it["file_id"],
        "page": it["metadata"]["page"],
      } for it in es_result],
    )


    return {
      "success": True,
      "message": TAG_C001,
      "data": llm_answer_result,
      "suggested_token": suggested_token,
      "prompt_token": prompt_token,
      "input_llm_max_token": input_llm_max_token,
      "prompt": prompt,
      "group_filtered_es_result_count": len(group_filtered_es_result),
      "filtered_es_result_count": len(filtered_es_result),
      "es_result_count": len(es_result),
      "group_filtered_es_result": group_filtered_es_result,
      "filtered_es_result": filtered_es_result,
      "es_result": es_result,
    }
    
  except Exception as e:
    is_busy = False
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
        # "suggested_token": suggested_token,
        # "prompt_token": prompt_token,
        # "input_llm_max_token": input_llm_max_token,
      }
    )



def _do_emit_to_uid(topic, dict, uid):
  async def fn():
    await wsConnectionManager.send_personal_message(
      message=json.dumps({
        "topic": topic,
        "dict": dict,
        }), 
      api_uid=uid,
      is_lifo=True,
    )
  
  asyncio.run(fn())
  




