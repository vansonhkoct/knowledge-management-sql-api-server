
import json
import asyncio
from src.models.master import Log
from src.models.master import User
from src.models.master import UserSession


_LOGTYPE_USER_LOGIN = "USER_LOGIN"
_LOGTYPE_CHATLLM_API = "CHATLLM_API"
_LOGTYPE_USER_LOGIN = "USER_LOGIN"
_LOGTYPE_USER_LOGIN = "USER_LOGIN"
_LOGTYPE_USER_LOGIN = "USER_LOGIN"


def add_log_user_login(
  user: User, 
  userSession: UserSession
  ):
    # Add log
    asyncio.create_task(
      Log.create(**{
        "type": _LOGTYPE_USER_LOGIN,
        "field1": f"user.party_id:{user.party_id}",
        "field2": f"user.id:{user.id}; user.name:{user.name}",
        "field3": f"userSession.id:{userSession.id}",
      })
    )


def add_log_apillm(
  question: str,
  index_name: str,
  prompt: str,
  llm_answer_result: dict,
  suggested_token: int,
  prompt_token: int,
  input_llm_max_token: int,
  es_result_ids: dict,
  ):
    # Add log
    asyncio.create_task(
      Log.create(**{
        "type": _LOGTYPE_CHATLLM_API,
        "field1": json.dumps({
          "index_name": index_name,
          "question": question,
        }, ensure_ascii=False),
        "field2": json.dumps({
          "data": {
            "answer_result": llm_answer_result["answer_result"],
          },
          "suggested_token": suggested_token,
          "prompt_token": prompt_token,
          "input_llm_max_token": input_llm_max_token,
          "es_result_ids": es_result_ids,
        }, ensure_ascii=False),
        "field3": prompt,
      })
    )