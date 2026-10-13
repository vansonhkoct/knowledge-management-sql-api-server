from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class VectorChunk:
  id: str
  party_id: str
  file_id: str
  category_id: str | None
  profile_id: str
  chunk_index: int
  page_number: int | None
  representation: str
  content: str
  content_hash: str
  metadata: dict
  embedding: list[float]


class VectorStore(Protocol):
  async def replace_file_chunks(self, chunks: list[VectorChunk]) -> None: ...

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
  ) -> list[dict]: ...

  async def delete_file(self, *, party_id: str, file_id: str) -> int: ...

