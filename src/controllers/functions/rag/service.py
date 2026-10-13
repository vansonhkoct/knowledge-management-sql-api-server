import asyncio
import hashlib
import os
import uuid

from src.controllers.functions.esbundle.es_chatllm import (
  MODEL_TYPE_EMBEDDING,
  _build_embedding_bundle,
  _resolve_model_endpoint,
  async_extract_pdf_file_to_text,
)

from .interfaces import VectorChunk
from .pglite_vector_store import PGliteVectorStore
from .profile import embedding_profile_id as _embedding_profile_id
from src.models.master import File


INDEX_VERSION = os.getenv("FILE_INDEX_VERSION", "pdf-v1")
CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "100"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "32"))


def embedding_profile_id(endpoint) -> str:
  return _embedding_profile_id(
    endpoint,
    index_version=INDEX_VERSION,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=CHUNK_OVERLAP,
  )


def _chunk_page(text: str) -> list[str]:
  normalized = "\n".join(line.rstrip() for line in (text or "").splitlines()).strip()
  if not normalized:
    return []

  chunks = []
  start = 0
  while start < len(normalized):
    target_end = min(start + CHUNK_SIZE, len(normalized))
    end = target_end
    if target_end < len(normalized):
      split_at = normalized.rfind("\n", start + (CHUNK_SIZE // 2), target_end)
      if split_at > start:
        end = split_at
    content = normalized[start:end].strip()
    if content:
      chunks.append(content)
    if end >= len(normalized):
      break
    start = max(end - CHUNK_OVERLAP, start + 1)
  return chunks


async def _embed_documents(embedding, texts: list[str]) -> list[list[float]]:
  vectors = []
  loop = asyncio.get_running_loop()
  for start in range(0, len(texts), EMBEDDING_BATCH_SIZE):
    batch = texts[start:start + EMBEDDING_BATCH_SIZE]
    batch_vectors = await loop.run_in_executor(None, embedding.embed_documents, batch)
    if len(batch_vectors) != len(batch):
      raise ValueError("Embedding endpoint returned an unexpected number of vectors")
    vectors.extend(batch_vectors)
  return vectors


async def index_pdf(
  *,
  party_id: str,
  filename: str,
  file_id: str,
  file,
  category_id: str | None = None,
  document_tags: list[str] | None = None,
  document_title: str | None = None,
  document_summary: str | None = None,
  document_remarks: str | None = None,
  document_userdata=None,
):
  page_texts, _ = await async_extract_pdf_file_to_text(
    filename=filename,
    file=file,
    meta_data_mapping={
      "document_file_id": file_id,
      "document_category": category_id or "",
    },
    accept_non_standard_chars=False,
  )

  prepared = []
  chunk_index = 0
  for page_number, page_text in enumerate(page_texts):
    for content in _chunk_page(page_text):
      prepared.append((chunk_index, page_number, content))
      chunk_index += 1
  if not prepared:
    raise ValueError("The PDF contains no extractable text")

  endpoint = await _resolve_model_endpoint(party_id, MODEL_TYPE_EMBEDDING)
  profile_id = embedding_profile_id(endpoint)
  embedding = _build_embedding_bundle(endpoint)
  header = "\n".join(
    value.strip()
    for value in [document_remarks, document_title, document_summary]
    if value and value.strip()
  )
  embedding_inputs = [f"{header}\n\n{content}" if header else content for _, _, content in prepared]
  vectors = await _embed_documents(embedding, embedding_inputs)

  metadata_base = {
    "document_file_id": file_id,
    "document_category": category_id or "",
    "document_file_name": filename,
    "document_file_url": filename,
    "document_tags": document_tags or [],
    "document_title": document_title,
    "document_summary": document_summary,
    "document_remarks": document_remarks,
    "document_userdata": document_userdata,
    "data_strategy": "PGLITE_VECTOR_V1",
    "data_portion_type": "CHUNK",
  }
  chunks = [
    VectorChunk(
      id=str(uuid.uuid4()),
      party_id=party_id,
      file_id=file_id,
      category_id=category_id,
      profile_id=profile_id,
      chunk_index=index,
      page_number=page_number,
      representation="CHUNK",
      content=content,
      content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
      metadata={**metadata_base, "page": page_number},
      embedding=vector,
    )
    for (index, page_number, content), vector in zip(prepared, vectors)
  ]

  store = PGliteVectorStore()
  await store.replace_file_chunks(
    chunks,
    model_name=endpoint.model_name,
    index_version=INDEX_VERSION,
  )
  return (
    chunks,
    [chunk.id for chunk in chunks],
    "pglite:rag_chunk",
    f"{INDEX_VERSION}:{profile_id}",
  )


async def search_knowledge(
  *,
  party_id: str,
  question: str,
  category_ids: list[str] | None = None,
  file_ids: list[str] | None = None,
  exclude_file_ids: list[str] | None = None,
  limit: int = 10,
) -> list[dict]:
  endpoint = await _resolve_model_endpoint(party_id, MODEL_TYPE_EMBEDDING)
  profile_id = embedding_profile_id(endpoint)
  embedding = _build_embedding_bundle(endpoint)
  query_vector = await asyncio.get_running_loop().run_in_executor(
    None,
    embedding.embed_query,
    question,
  )
  rows = await PGliteVectorStore().search(
    party_id=party_id,
    profile_id=profile_id,
    query_embedding=query_vector,
    category_ids=category_ids,
    file_ids=file_ids,
    exclude_file_ids=exclude_file_ids,
    limit=min(max(limit * 5, limit), 100),
  )
  candidate_file_ids = list({str(row["file_id"]) for row in rows})
  if not candidate_file_ids:
    return []
  indexed_file_ids = {
    str(file_id)
    for file_id in await File.filter(
      id__in=candidate_file_ids,
      party_id=party_id,
      index_status="INDEXED",
      is_disabled=False,
      is_deleted=False,
    ).values_list("id", flat=True)
  }
  rows = [row for row in rows if str(row["file_id"]) in indexed_file_ids][:limit]
  return [
    {
      "id": str(row["id"]),
      "file_id": str(row["file_id"]),
      "content": row["content"],
      "score": float(row["score"]),
      "metadata": row["metadata"],
    }
    for row in rows
  ]


async def delete_file_chunks(*, party_id: str, file_id: str) -> int:
  return await PGliteVectorStore().delete_file(party_id=party_id, file_id=file_id)


async def update_file_metadata(
  *,
  party_id: str,
  file_id: str,
  category_id: str | None,
  tags: list[str] | None = None,
  userdata=None,
) -> int:
  return await PGliteVectorStore().update_file_metadata(
    party_id=party_id,
    file_id=file_id,
    category_id=category_id,
    metadata={
      "document_category": category_id or "",
      "document_tags": tags or [],
      "document_userdata": userdata,
    },
  )


async def fetch_file_chunks(*, party_id: str, file_id: str) -> list[dict]:
  rows = await PGliteVectorStore().fetch_file(party_id=party_id, file_id=file_id)
  return [
    {"text": row["content"], "metadata": row["metadata"]}
    for row in rows
  ]
