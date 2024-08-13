import os

class ConfigParams():
    def __init__(self):
        self.username = os.getenv("ES_CHATLLM_USERNAME")
        self.password = os.getenv("ES_CHATLLM_PASSWORD")
        self.host = os.getenv("ES_CHATLLM_HOST")

        self.embedding_model_legacy = os.getenv("ES_CHATLLM_EMBEDDING_MODEL_LEGACY")
        self.embedding_model = os.getenv("ES_CHATLLM_EMBEDDING_MODEL")
        self.llm_model_uses_gpu = True if os.getenv("ES_CHATLLM_LLM_MODEL_USES_GPU") == "1" else False
        self.llm_model = os.getenv("ES_CHATLLM_LLM_MODEL_GPU") if self.llm_model_uses_gpu == True else os.getenv("ES_CHATLLM_LLM_MODEL_CPU")

        print("\n--- [es_chatllm -> ConfigParams:]\n")
        print(f"es host: {self.host}")
        print(f"es embedding_model: {self.embedding_model_legacy}")
        print(f"es embedding_model: {self.embedding_model}")
        print(f"llm_model_uses_gpu: {self.llm_model_uses_gpu}")
        print(f"llm_model: {self.llm_model}")
        print("---\n")