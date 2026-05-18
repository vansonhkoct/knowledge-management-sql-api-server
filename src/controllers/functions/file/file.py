
from typing import BinaryIO

from py_eschat_llm import ESVoDocInsert
from py_eschat_llm import es_chatllm as ESChatLLM
from src.controllers.functions._generic.fileutils import UploadFileRecord
from src.models.master import File


def bootstrapImportESBundle():
  """Backward-compatible hook maintained for legacy callers."""
  return True



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
  plaintext: str,
  category_id: str,
  document_tags: list[str] | None = None,
  document_title: str = None,
  document_summary: str = None,
  document_remarks: str = None,
  document_userdata = None,
):
  bootstrapImportESBundle()
  
  if plaintext is not None:
    text = plaintext
  else:
    _, text = await ESChatLLM.async_extract_pdf_file_to_text(
      filename=filename,
      file=file,
      meta_data_mapping = {
          "document_file_id": str(file_id) if file_id is not None else "",
          "document_category": str(category_id) if category_id is not None else "",
      },
      accept_non_standard_chars = False,
    )

  vo = ESVoDocInsert(
    index_name = str(party_id),
    text = text,
    extra_metadata = {
        "document_tags": document_tags or [],
        "document_title": str(document_title) if document_title is not None else None,
        "document_summary": str(document_summary) if document_summary is not None else None,
        "document_remarks": str(document_remarks) if document_remarks is not None else None,
        "document_userdata": document_userdata,
    },
    is_testrun = False,
  )

  docs, new_ids, index_name = await ESChatLLM.bot_es_add_document(
    vo=vo,
  )

  return docs, new_ids, index_name



async def on_update_file(
  party_id: str,
  file: File,
  category_id: str,
  tags: list[str] = None,
  userdata = None,
):
  bootstrapImportESBundle()
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids is not None else "").split(",")

  for index in range(len(es_doc_ids)):
    await ESChatLLM.bot_es_update_document_metadata(
      index_name=str(party_id),
      id=es_doc_ids[index],
      document_category=category_id if category_id is not None else "",
      document_tags=tags,
      document_userdata=userdata,
    )
  
  
  
async def on_remove_file(
  party_id: str,
  file: File,
):
  bootstrapImportESBundle()
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids is not None else "").split(",")

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
  
  es_doc_ids = (file.es_doc_ids if file.es_doc_ids is not None else "").split(",")
  results = []

  for index in range(len(es_doc_ids)):
    res = await ESChatLLM.bot_es_get_document_by_id(
      index_name=str(party_id),
      id=es_doc_ids[index],
    )
    
    if res is not None:
      results.append({
        "text": res["text"],
        "metadata": res["metadata"],
      })
  
  return results
  
  
  

