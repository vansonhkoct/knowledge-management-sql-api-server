import os
from datetime import datetime

username = os.getenv("ES_USERNAME")
password = os.getenv("ES_PASSWORD")
host = os.getenv("ES_HOST")

embedding_model_legacy = os.getenv("ES_EMBEDDING_MODEL_LEGACY")
embedding_model = os.getenv("ES_EMBEDDING_MODEL")
es_verbose = True if os.getenv("ES_VERBOSE") == "1" else False
es_debug = True if (os.getenv("ES_DEBUG") == "1" or os.getenv("ES_VERBOSE") == "1") else False

llm_model_uses_gpu = True if os.getenv("ES_CHATLLM_LLM_MODEL_USES_GPU") == "1" else False
llm_model = os.getenv("ES_CHATLLM_LLM_MODEL_GPU") if llm_model_uses_gpu == True else os.getenv("ES_CHATLLM_LLM_MODEL_CPU")
llm_controller_debug = True if os.getenv("ES_CHATLLM_LLM_CONTROLLER_DEBUG") == "1" else False

print("\n--- [es_chatllm -> ConfigParams:]\n")
print(f"es host: {host}")
print(f"es embedding_model_legacy: {embedding_model_legacy}")
print(f"es embedding_model: {embedding_model}")
print(f"es es_debug: {es_debug}")
print(f"llm_model_uses_gpu: {llm_model_uses_gpu}")
print(f"llm_model: {llm_model}")
print(f"llm_controller_debug: {llm_controller_debug}")
print("---\n")
        
def es_dbg(head = "", body = ""):
    if es_debug:
        print(f'[ES] {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} {head} - {body}')

def es_verb(head = "", body = ""):
    if es_verbose:
        print(f'[ES] {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} {head} - {body}')
    elif es_debug:
        print(f'[ES] {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} {head} - {body}'[:255])

def llm_dbg(head = "", body = ""):
    if es_debug:
        print(f'[ChatLLM] {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} {head} - {body}')

def llm_verbose(head = "", body = ""):
    if es_verbose:
        print(f'[ChatLLM] {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")} {head} - {body}')
    elif es_debug:
        print('.', end = "", flush=True)

