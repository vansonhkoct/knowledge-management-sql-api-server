
from src.controllers.functions._generic.fileutils import UploadFileRecord, upload_file_write_to_upload_folder
from src.controllers.functions.esbundle.include.ElasticSearchDao.ESVo import ESVoDocInsert
from src.models.master import File

from typing import BinaryIO


ESChatLLM = None
async_extract_pdf_file_to_text = None


def bootstrapImportESBundle():
  global ESChatLLM
  global extract_pdf_file_to_text
  
  if (ESChatLLM is None):
    import controllers.functions.esbundle.es_chatllm as _ESChatLLM
    ESChatLLM = _ESChatLLM
    
  if (extract_pdf_file_to_text is None):
    from controllers.functions.esbundle.es_chatllm import async_extract_pdf_file_to_text as _async_extract_pdf_file_to_text
    async_extract_pdf_file_to_text = _async_extract_pdf_file_to_text



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
  document_tags = [],
  document_title: str = None,
  document_summary: str = None,
  document_remarks: str = None,
):
  bootstrapImportESBundle()
  
  text_data, text = await async_extract_pdf_file_to_text(
    filename=filename,
    file=file,
    meta_data_mapping = {
        "document_file_id": str(file_id) if file_id != None else "",
        "document_category": str(category_id) if category_id != None else "",
    },
    accept_non_standard_chars = False,
  )

  vo = ESVoDocInsert(
    index_name = str(party_id),
    text = text,
    extra_metadata = {
        "document_tags": document_tags,
        "document_title": str(document_title) if document_title is not None else None,
        "document_summary": str(document_summary) if document_summary is not None else None,
        "document_remarks": str(document_remarks) if document_remarks is not None else None,
    },
    is_testrun = False,
  )

  docs, new_ids, index_name = await ESChatLLM.bot_es_add_document(
    vo=vo,
  )

  return docs, new_ids, index_name



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
  
  
  

