
import requests


class EmbeddingsBundle:
    def __init__(
        self,
        base_url,
        model_name,
        api_key=None,
        api_path="/v1",
        headers_json=None,
        options_json=None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.api_path = api_path or "/v1"
        self.headers_json = headers_json if isinstance(headers_json, dict) else {}
        self.options_json = options_json if isinstance(options_json, dict) else {}

    def _build_url(self, suffix):
        api_path = (self.api_path or "").strip()
        suffix = suffix.lstrip("/")

        if api_path in ["", "/"]:
            return f"{self.base_url}/{suffix}"

        normalized_api_path = api_path if api_path.startswith("/") else f"/{api_path}"
        if self.base_url.endswith(normalized_api_path):
            return f"{self.base_url}/{suffix}"

        return f"{self.base_url}{normalized_api_path}/{suffix}"

    def _build_headers(self):
        headers = {
            "Content-Type": "application/json",
            **self.headers_json,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _embed(self, text_list):
        response = requests.post(
            self._build_url("embeddings"),
            headers=self._build_headers(),
            json={
                "model": self.model_name,
                "input": text_list,
                **self.options_json,
            },
            timeout=240,
        )
        response.raise_for_status()

        body = response.json()
        return [it["embedding"] for it in body.get("data", [])]

    def embed_documents(self, text_list):
        return self._embed(text_list)

    def embed_query(self, text):
        return self._embed([text])[0]

    def embed_documents_legacy(self, text_list):
        return self._embed(text_list)

    def embed_query_legacy(self, text):
        return self._embed([text])[0]

