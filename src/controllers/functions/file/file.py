
import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../../../")

from controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from models.master import File

from typing import BinaryIO


ESChatLLM = None
extract_pdf_file_to_text = None


def bootstrapImportESBundle():
  global ESChatLLM
  global extract_pdf_file_to_text
  
  if (ESChatLLM == None):
    from controllers.functions.esbundle.es_chatllm import ESChatLLM as _ESChatLLM
    ESChatLLM = _ESChatLLM
    
  if (extract_pdf_file_to_text == None):
    from controllers.functions.esbundle.es_chatllm import extract_pdf_file_to_text as _extract_pdf_file_to_text
    extract_pdf_file_to_text = _extract_pdf_file_to_text



async def create_entry_file(
  uploadFileRecord: UploadFileRecord = None,
  party_id: str = None,
  category_id: str = None,
):
  new_entry = await File.create(
    alias = uploadFileRecord.alias,
    filename = uploadFileRecord.filename,
    mime_type = uploadFileRecord.mimetype,
    size_bytes = uploadFileRecord.filesize,
    category_id = category_id,
    party_id = party_id,
  )

  return new_entry



async def on_upload_file(
  party_id: str,
  filename: str,
  file_id: str,
  file: BinaryIO,
  category_id: str,
):
  bootstrapImportESBundle()
  
  text_data, text = extract_pdf_file_to_text(
    filename=filename,
    file=file,
    meta_data_mapping = {
        "document_file_id": str(file_id) if file_id != None else "",
        "document_category": str(category_id) if category_id != None else "",
    }
  )

  docs, ids, index_name = await ESChatLLM.bot_es_add_document(
    index_name=str(party_id),
    text_data=text_data,
    text=text,
  )

  return docs, ids, index_name


async def on_move_file(
  party_id: str,
  file: File,
  category_id: str,
):
  bootstrapImportESBundle()
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids != None else "").split(",")

  for index in range(len(es_doc_ids)):
    await ESChatLLM.bot_es_update_document_metadata(
      index_name=str(party_id),
      id=es_doc_ids[index],
      document_category=category_id if category_id != None else "",
    )
  
  
  
async def on_remove_file(
  party_id: str,
  file: File,
):
  bootstrapImportESBundle()
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids != None else "").split(",")

  for index in range(len(es_doc_ids)):
    await ESChatLLM.bot_es_delete_document_by_id(
      index_name=str(party_id),
      id=es_doc_ids[index],
    )
  
  
  
async def fetch_es_docs(
  party_id: str,
  file: File,
):
  bootstrapImportESBundle()
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids != None else "").split(",")
  results = []

  for index in range(len(es_doc_ids)):
    res = await ESChatLLM.bot_es_get_document_by_id(
      index_name=str(party_id),
      id=es_doc_ids[index],
    )
    
    if (res != None):
      results.append({
        "text": res["text"],
        "metadata": res["metadata"],
      })
  
  return results
  
  
  

