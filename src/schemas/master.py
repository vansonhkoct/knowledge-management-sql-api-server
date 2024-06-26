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
    id = fields.UUIDField(pk=True)
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
    party = fields.ForeignKeyField("models.Party", related_names="roles", null=True)
    code = fields.CharField(max_length=64, null=True, index=True)
    permissions: fields.ManyToManyRelation["Permission"]
    accessible_categorys = fields.ManyToManyField("models.Category", through="_rel_role_accessible_category", null=True)
    users: fields.ReverseRelation["User"]
    def __str__(self):
        return self.name

    class PydanticMeta:
        exclude = (
            "party",
        )

class Category(Model, _ModelBaseAccess, _ModelBaseBody):
    party = fields.ForeignKeyField("models.Party", related_names="categorys", null=True)
    parent_category = fields.ForeignKeyField("models.Category", related_names="categorys", null=True)

    files: fields.ReverseRelation["File"]
    sub_categorys: fields.ReverseRelation["Category"]
    
    accessible_roles: fields.ManyToManyRelation["Role"]

    alias = fields.CharField(max_length=512, null=True)
    folderpath_relative = fields.CharField(max_length=512, default="")
    folderpath_absolute = fields.CharField(max_length=5120, null=True)

    def __str__(self):
        return self.name

class Permission(Model, _ModelBaseAccess, _ModelBaseBody):
    code = fields.CharField(max_length=64, null=True, index=True)
    roles = fields.ManyToManyField("models.Role", through="_rel_role_permission", null=True)
    def __str__(self):
        return self.name

class File(Model, _ModelBaseAccess):
    category = fields.ForeignKeyField("models.Category", related_names="files", null=True)
    party = fields.ForeignKeyField("models.Party", related_names="files", null=True)

    alias = fields.CharField(max_length=512, null=True)
    filename = fields.CharField(max_length=255, null=True)
    mime_type = fields.CharField(max_length=64, null=True)
    size_bytes = fields.IntField(null=True)
    
    es_doc_ids = fields.TextField(null=True)
    
    def __str__(self):
        return self.name

class Party(Model, _ModelBaseAccess):
    categorys: fields.ReverseRelation["Category"]
    roles: fields.ReverseRelation["Role"]
    files: fields.ReverseRelation["File"]
    users: fields.ReverseRelation["User"]

    def __str__(self):
        return self.name
    
    class PydanticMeta:
        exclude = (
            "categorys",
            "users",
            "files",
        )

class User(Model, _ModelBaseAccess, _ModelBaseBody):
    role = fields.ForeignKeyField("models.Role", related_name="users", null=True)
    party = fields.ForeignKeyField("models.Party", related_name="users", null=True)
    userCredentials: fields.ReverseRelation["UserCredential"]
    userSessions: fields.ReverseRelation["UserSession"]
    userRequests: fields.ReverseRelation["UserRequest"]
    
    email = fields.CharField(512, index=True, null=True)
    short_name = fields.CharField(256, index=True, null=True)
    phone_code = fields.CharField(24, index=True, null=True)
    phone_number = fields.CharField(256, index=True, null=True)

    def __str__(self):
        return self.name
    
    class PydanticMeta:
        exclude = (
            "userCredentials",
            "userRequests",
            "userSessions",
            "party.roles",
            "chatMessages",
        )

class UserCredential(Model, _ModelBaseAccess):
    user = fields.ForeignKeyField("models.User", related_name="userCredentials", null=True)
    credential_type = fields.CharEnumField(enum_type=UserCredentialType, index=True)
    status = fields.CharField(max_length=10, index=True, null=True)
    username = fields.CharField(max_length=256, index=True, unique=True, null=True)
    password_hash = fields.CharField(max_length=256, index=True, null=True)
    def __str__(self):
        return self.name

class UserSession(Model, _ModelBaseAccess):
    user = fields.ForeignKeyField("models.User", related_name="userSessions", null=True)
    access_token = fields.CharField(max_length=256, index=True, null=True)
    refresh_token = fields.CharField(max_length=256, index=True, null=True)
    issued_at = fields.DatetimeField(null=True)
    def __str__(self):
        return self.name

class UserRequest(Model, _ModelBaseAccess, _ModelBaseBody):
    user = fields.ForeignKeyField("models.User", related_name="userRequests", null=True)
    request_type = fields.CharEnumField(enum_type=UserRequestType, index=True, null=True)
    status = fields.CharField(max_length=10, index=True, null=True)
    token = fields.CharField(max_length=256, index=True, null=True)
    code = fields.CharField(max_length=256, index=True, null=True)
    def __str__(self):
        return self.name

class Chat(Model, _ModelBaseAccess):
    categorys = fields.ForeignKeyField("models.Category", related_name="chats", null=True)
    chatmessages: fields.ReverseRelation["ChatMessage"]
    prompt_prefix = fields.CharField(max_length=2048, default="")
    def __str__(self):
        return self.name

class ChatMessage(Model, _ModelBaseAccess, _ModelBaseBody):
    chat = fields.ForeignKeyField("models.Chat", related_name="chatMessages", null=True)
    user = fields.ForeignKeyField("models.User", related_name="chatMessages", null=True)
    chatmessagefeedbacks: fields.ReverseRelation["ChatMessageFeedback"]
    def __str__(self):
        return self.name

class ChatMessageFeedback(Model, _ModelBaseAccess, _ModelBaseBody):
    chatmessage = fields.ForeignKeyField("models.ChatMessage", related_name="chatMessageFeedbacks", null=True)
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
