

from sentence_transformers import SentenceTransformer

class EmbeddingsBundle:
    def __init__(self, model_path, model_path_legacy):
        self.model_legacy = SentenceTransformer(model_path_legacy)
        self.model = SentenceTransformer(model_path)

    def embed_documents(self, text_list):
        embeddings = self.model.encode(text_list)
        encod_list = embeddings.tolist()
        return encod_list

    def embed_query(self, text):
        embeddings = self.model.encode([text])
        encod_list = embeddings.tolist()
        return encod_list[0]


    def embed_documents_legacy(self, text_list):
        embeddings = self.model_legacy.encode(text_list)
        encod_list = embeddings.tolist()
        return encod_list

    def embed_query_legacy(self, text):
        embeddings = self.model_legacy.encode([text])
        encod_list = embeddings.tolist()
        return encod_list[0]

