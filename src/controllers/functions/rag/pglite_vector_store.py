import os
from dataclasses import asdict

import httpx

from .interfaces import VectorChunk


class PGliteVectorStore:
  def __init__(self, service_url: str | None = None):
    self.service_url = (
      service_url
      or os.getenv("PGLITE_SERVICE_URL", "http://127.0.0.1:5434")
    ).rstrip("/")
    self.timeout = httpx.Timeout(connect=5, read=120, write=120, pool=5)

  async def _request(self, path: str, payload: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=self.timeout) as client:
      if payload is None:
        response = await client.get(f"{self.service_url}{path}")
      else:
        response = await client.post(f"{self.service_url}{path}", json=payload)
    if response.is_error:
      detail = response.json().get("error", response.text)
      raise RuntimeError(f"PGlite sidecar request failed: {detail}")
    return response.json()

  async def health(self) -> dict:
    return await self._request("/health")

  async def replace_file_chunks(
    self,
    chunks: list[VectorChunk],
    *,
    model_name: str,
    index_version: str,
  ) -> None:
    if not chunks:
      raise ValueError("Cannot index a PDF with no extractable text")
    await self._request("/v1/files/replace", {
      "profile": {
        "id": chunks[0].profile_id,
        "modelName": model_name,
        "indexVersion": index_version,
      },
      "chunks": [asdict(chunk) for chunk in chunks],
    })

  async def search(
    self,
    *,
    party_id: str,
    profile_id: str,
    query_embedding: list[float],
    category_ids: list[str] | None = None,
    file_ids: list[str] | None = None,
    exclude_file_ids: list[str] | None = None,
    limit: int = 10,
  ) -> list[dict]:
    result = await self._request("/v1/search", {
      "partyId": party_id,
      "profileId": profile_id,
      "queryEmbedding": query_embedding,
      "categoryIds": category_ids,
      "fileIds": file_ids,
      "excludeFileIds": exclude_file_ids,
      "limit": limit,
    })
    return result["items"]

  async def delete_file(self, *, party_id: str, file_id: str) -> int:
    result = await self._request("/v1/files/delete", {
      "partyId": party_id,
      "fileId": file_id,
    })
    return int(result["affected"])

  async def update_file_metadata(
    self,
    *,
    party_id: str,
    file_id: str,
    category_id: str | None,
    metadata: dict,
  ) -> int:
    result = await self._request("/v1/files/update-metadata", {
      "partyId": party_id,
      "fileId": file_id,
      "categoryId": category_id,
      "metadata": metadata,
    })
    return int(result["affected"])

  async def fetch_file(self, *, party_id: str, file_id: str) -> list[dict]:
    result = await self._request("/v1/files/get", {
      "partyId": party_id,
      "fileId": file_id,
    })
    return result["items"]
