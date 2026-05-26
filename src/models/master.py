from tortoise import Tortoise
from src.schemas.master import *

Tortoise.init_models(models_paths=[
  "src.schemas.master",
  "aerich.models",
], app_label="models")


KMRole = None
KMCategory = None
KMPermission = None
KMFile = None
KMAIModelEndpoint = None
KMParty = None
KMUser = None
KMUserCredential = None
KMUserSession = None
KMUserRequest = None
KMChat = None
KMChatMessage = None
KMChatMessageFeedback = None

