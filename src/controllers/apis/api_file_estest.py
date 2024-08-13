import traceback
from fastapi import APIRouter, File as FastAPIFile, UploadFile, Form, Request, Body
from fastapi import HTTPException
from typing import Annotated
from tortoise.expressions import Q

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

      import controllers.functions.esbundle.es_chatllm as ESChatLLM
      from controllers.functions.esbundle.es_chatllm import async_extract_pdf_file_to_text
      import nltk
      nltk.download('punkt_tab')
      nltk.download('averaged_perceptron_tagger_eng')
      
      print("\n==== PART 2 ===\n")
      
      text_data, text = await async_extract_pdf_file_to_text(
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

      docs, ids, index_name = await ESChatLLM.bot_es_add_document_testraw(
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
        use_text_splitter=False,
      )

  return {
    "success": True,
    "message": TAG_C001,
    "esparsedata": {
      "ids": ids,
      "docs": docs,
      "index_name": index_name,
    },
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

  import controllers.functions.esbundle.es_chatllm as ESChatLLM
  from controllers.functions.esbundle.es_chatllm import async_extract_pdf_file_to_text
  import nltk
  nltk.download('punkt_tab')
  nltk.download('averaged_perceptron_tagger_eng')
  


  print ("\n==== PART 0 clean ===\n")
  await ESChatLLM.bot_es_delete_all_documents("t20240812_a_mbase_56e0a540-fb4f-40b6-acdd-d325d3d0fd65")
  await ESChatLLM.bot_es_delete_all_documents("t20240812_a_mbase_totaldoc_56e0a540-fb4f-40b6-acdd-d325d3d0fd65")
  
  print ("\n==== PART 0 cleaned ===\n")

  
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
        
        text_data, text = await async_extract_pdf_file_to_text(
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

        docs, ids, index_name = await ESChatLLM.bot_es_add_document_testraw(
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
          use_text_splitter=False,
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
  import controllers.functions.esbundle.es_chatllm as ESChatLLM

  data = await request.json()

  result = await ESChatLLM.bot_es_search_multi_vector_string_fields(
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
  import controllers.functions.esbundle.es_chatllm as ESChatLLM

  data = await request.json()

  result = await ESChatLLM.bot_get_es_doc_ids_document_es_ids_by_document_file_id(
    index_name=data["index_name"],
    document_file_id=data["document_file_id"],
  )

  return {
    "success": True,
    "message": TAG_C001,
    "data": result,
  }
  