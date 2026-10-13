import json
import uuid


def embedding_profile_id(
  endpoint,
  *,
  index_version: str,
  chunk_size: int,
  chunk_overlap: int,
) -> str:
  """Return a stable UUID that changes whenever embedding behavior changes."""
  configuration = {
    "endpoint_id": str(endpoint.id),
    "provider": endpoint.provider,
    "base_url": endpoint.base_url,
    "api_path": endpoint.api_path,
    "model_name": endpoint.model_name,
    "headers_json": endpoint.headers_json,
    "options_json": endpoint.options_json,
    "index_version": index_version,
    "chunk_size": chunk_size,
    "chunk_overlap": chunk_overlap,
  }
  canonical = json.dumps(configuration, sort_keys=True, separators=(",", ":"), default=str)
  return str(uuid.uuid5(uuid.NAMESPACE_URL, canonical))
