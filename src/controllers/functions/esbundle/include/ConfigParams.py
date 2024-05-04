
class ConfigParams():
    def __init__(self):
        self.username = "elastic"
        self.password = "octopuspass"
        self.host = "https://192.168.2.107:9200"

        self.embedding_model = "moka-ai/m3e-small"
        self.llm_model = "THUDM/chatglm2-6b-int4"
        self.llm_model_gpu = False

