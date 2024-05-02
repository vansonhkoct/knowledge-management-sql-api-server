from tortoise.contrib.pydantic import pydantic_model_creator

import sys
import os

# Get the parent directory
parent_dir = os.path.dirname(os.path.realpath(__file__))

# Add the parent directory to sys.path
sys.path.append(parent_dir + "/../")
# print(sys.path)

from schemas.master import *

KMRole = pydantic_model_creator(Role, name="Role")
KMCategory = pydantic_model_creator(Category, name="Category")
KMPermission = pydantic_model_creator(Permission, name="Permission")
KMFile = pydantic_model_creator(File, name="File")
KMParty = pydantic_model_creator(Party, name="Party")
KMUser = pydantic_model_creator(User, name="User")
KMUserCredential = pydantic_model_creator(UserCredential, name="UserCredential")
KMUserSession = pydantic_model_creator(UserSession, name="UserSession")
KMUserRequest = pydantic_model_creator(UserRequest, name="UserRequest")
KMChat = pydantic_model_creator(Chat, name="Chat")
KMChatMessage = pydantic_model_creator(ChatMessage, name="ChatMessage")
KMChatMessageFeedback = pydantic_model_creator(ChatMessageFeedback, name="ChatMessageFeedback")

