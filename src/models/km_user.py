from enum import Enum
from tortoise import Tortoise, connections, fields, run_async
from tortoise.models import Model
from tortoise import fields
from tortoise.utils import get_schema_sql



class UserCredentialType(Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    MSAL = "MSAL"

class UserRequestType(Enum):
    ACCOUNT_REGISTER = "ACCOUNT_REGISTER"
    ACCOUNT_RESET_PASSWORD = "ACCOUNT_RESET_PASSWORD"



class _ModelBaseAccess:
    _id = fields.UUIDField(pk=True)
    is_disabled = fields.BooleanField(index=True, default=0)
    is_deleted = fields.BooleanField(index=True, default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    modified_at = fields.DatetimeField(auto_now=True)
    name = fields.CharField(max_length=255, default="")
    desc = fields.TextField(null=True)
    def __str__(self):
        return self.name

class _ModelBaseBody:
    body = fields.TextField(null=True)
    body_json = fields.JSONField(null=True)




class Role(Model, _ModelBaseAccess, _ModelBaseBody):
    permissions: fields.ManyToManyRelation["Permission"]
    users: fields.ReverseRelation["User"]
    def __str__(self):
        return self.name

class Category(Model, _ModelBaseAccess, _ModelBaseBody):
    # party = fields.ForeignKeyField("models.Party", related_names="categorys")
    files = fields.ManyToManyField("models.File", through="_rel_file_category")
    permissions: fields.ManyToManyRelation["Permission"]
    def __str__(self):
        return self.name

class Permission(Model, _ModelBaseAccess, _ModelBaseBody):
    roles = fields.ManyToManyField("models.Role", through="_rel_role_permission")
    categorys = fields.ManyToManyField("models.Category", through="_rel_permission_category")
    def __str__(self):
        return self.name

class File(Model, _ModelBaseAccess):
    categorys: fields.ManyToManyRelation["Category"]
    filename = fields.CharField(max_length=5120, null=True)
    mime_type = fields.CharField(max_length=64, null=True)
    size_bytes = fields.IntField(null=True)
    def __str__(self):
        return self.name

class Party(Model, _ModelBaseAccess):
    # categorys: fields.ReverseRelation["Category"]
    users = fields.ManyToManyField("models.User", through="_rel_party_user")
    def __str__(self):
        return self.name

class User(Model, _ModelBaseAccess, _ModelBaseBody):
    role = fields.ForeignKeyField("models.Role", related_name="users")
    partys: fields.ManyToManyRelation["Party"]
    userCredentials: fields.ReverseRelation["UserCredential"]
    userSessions: fields.ReverseRelation["UserSession"]
    userRequests: fields.ReverseRelation["UserRequest"]
    email = fields.CharField(512, index=True, null=True)
    short_name = fields.CharField(256, index=True, null=True)
    phone_code = fields.CharField(24, index=True, null=True)
    phone_number = fields.CharField(256, index=True, null=True)
    def __str__(self):
        return self.name

class UserCredential(Model, _ModelBaseAccess):
    user = fields.ForeignKeyField("models.User", related_name="userCredentials")
    credential_type = fields.CharEnumField(enum_type=UserCredentialType, index=True)
    status = fields.CharField(max_length=10, index=True, null=True)
    username = fields.CharField(max_length=256, index=True, null=True)
    password_hash = fields.CharField(max_length=256, index=True, null=True)
    def __str__(self):
        return self.name

class UserSession(Model, _ModelBaseAccess):
    user = fields.ForeignKeyField("models.User", related_name="userSessions")
    access_token = fields.CharField(max_length=256, index=True, null=True)
    refresh_token = fields.CharField(max_length=256, index=True, null=True)
    issued_at = fields.DatetimeField(null=True)
    def __str__(self):
        return self.name

class UserRequest(Model, _ModelBaseAccess, _ModelBaseBody):
    user = fields.ForeignKeyField("models.User", related_name="userRequests")
    request_type = fields.CharEnumField(enum_type=UserRequestType, index=True, null=True)
    status = fields.CharField(max_length=10, index=True, null=True)
    token = fields.CharField(max_length=256, index=True, null=True)
    code = fields.CharField(max_length=256, index=True, null=True)
    def __str__(self):
        return self.name

class Chat(Model, _ModelBaseAccess):
    categorys = fields.ForeignKeyField("models.Category", related_name="chats")
    chatmessages: fields.ReverseRelation["ChatMessage"]
    prompt_prefix = fields.CharField(max_length=2048, default="")
    def __str__(self):
        return self.name

class ChatMessage(Model, _ModelBaseAccess, _ModelBaseBody):
    chat = fields.ForeignKeyField("models.Chat", related_name="chatMessages")
    user = fields.ForeignKeyField("models.User", related_name="chatMessages")
    chatmessagefeedbacks: fields.ReverseRelation["ChatMessageFeedback"]
    def __str__(self):
        return self.name

class ChatMessageFeedback(Model, _ModelBaseAccess, _ModelBaseBody):
    chatmessage = fields.ForeignKeyField("models.ChatMessage", related_name="chatMessageFeedbacks")
    score = fields.IntField(null=True)
    is_like = fields.BooleanField(default=False)
    is_dislike = fields.BooleanField(default=False)
    def __str__(self):
        return self.name



# async def run():

#     print("\n\nMySQL:\n")
#     await Tortoise.init(
#         config_file="../../config.json"
#     )
#     await Tortoise.generate_schemas(safe=True)
#     sql = get_schema_sql(connections.get("default"), safe=True)
#     print(sql)

# if __name__ == "__main__":
#     run_async(run())
