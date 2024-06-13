from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, Enum, String, Text, DateTime, UUID, JSON
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import relationship

import enum


class Base(DeclarativeBase):
  pass

class UserCredentialType(enum.Enum):
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    MSAL = "MSAL"

class UserRequestType(enum.Enum):
    ACCOUNT_REGISTER = "ACCOUNT_REGISTER"
    ACCOUNT_RESET_PASSWORD = "ACCOUNT_RESET_PASSWORD"



class _ModelBaseAccess:
    id = mapped_column(UUID, primary_key=True, index=True)
    is_disabled = mapped_column(Boolean, index=True, default=True)
    is_deleted = mapped_column(Boolean, index=True, default=True)
    created_at = mapped_column(DateTime, default=datetime.now())
    modified_at = mapped_column(DateTime, onupdate=datetime.now())
    name = mapped_column(String(255), default="")
    desc = mapped_column(Text, nullable=True)

class _ModelBaseBody:
    body = mapped_column(Text, nullable=True)
    body_json = mapped_column(JSON, nullable=True)




class Role(Base, _ModelBaseAccess, _ModelBaseBody):
    __tablename__ = "role"
    
    party_id = mapped_column(ForeignKey("party.id"), nullable=True)
    # accessible_categorys = fields.ManyToManyField("models.Category", through="_rel_role_accessible_category", null=True)

    party = relationship("Party", back_populates="roles", 
                         primaryjoin="Role.party_id == Party.id")
    users = relationship("User", back_populates="role",
                         primaryjoin="Role.id == User.role_id")
    permissions = relationship(secondary="z_rel_role_permission", back_populates="roles")
    permissions_assoc = relationship("z_rel_role_permission", back_populates="role",
                                     primaryjoin="Role.id == ZRelRolePermission.role_id")

    code = mapped_column(String(64), nullable=True, index=True)
    
    def __repr__(self):
        return f"{self.name}"


# class Category(Model, _ModelBaseAccess, _ModelBaseBody):
#     party = fields.ForeignKeyField("models.Party", related_names="categorys", null=True)
#     parent_category = fields.ForeignKeyField("models.Category", related_names="categorys", null=True)

#     files: fields.ReverseRelation["File"]
#     sub_categorys: fields.ReverseRelation["Category"]
    
#     # accessible_roles: fields.ManyToManyRelation["Role"]

#     alias = fields.CharField(max_length=512, null=True)
#     folderpath_relative = fields.CharField(max_length=512, default="")
#     folderpath_absolute = fields.CharField(max_length=5120, null=True)

#     def __str__(self):
#         return self.name

class Permission(Base, _ModelBaseAccess, _ModelBaseBody):
    __tablename__ = "permission"
    
    roles = relationship(secondary="z_rel_role_permission", back_populates="permissions")
    roles_assoc = relationship("z_rel_role_permission", back_populates="permission",
                                  primaryjoin="Permission.id == ZRelRolePermission.permission_id")

    code = mapped_column(String(64), nullable=True, index=True)

    def __repr__(self):
        return f"{self.name}"

# class File(Model, _ModelBaseAccess):
#     category = fields.ForeignKeyField("models.Category", related_names="files", null=True)
#     party = fields.ForeignKeyField("models.Party", related_names="files", null=True)

#     alias = fields.CharField(max_length=512, null=True)
#     filename = fields.CharField(max_length=255, null=True)
#     mime_type = fields.CharField(max_length=64, null=True)
#     size_bytes = fields.IntField(null=True)
    
#     es_doc_ids = fields.TextField(null=True)
    
#     def __str__(self):
#         return self.name

class Party(Base, _ModelBaseAccess):
    __tablename__ = "party"
    
    # categorys: fields.ReverseRelation["Category"]
    # files: fields.ReverseRelation["File"]
    roles = relationship("Role", back_populates="party",
                         primaryjoin="Role.party_id == Party.id")
    users = relationship("User", back_populates="party",
                         primaryjoin="User.party_id == Party.id")

    def __repr__(self):
        return f"{self.name}"


class User(Base, _ModelBaseAccess, _ModelBaseBody):
    __tablename__ = "user"
    
    role_id = mapped_column(ForeignKey("role.id"), nullable=True)
    party_id = mapped_column(ForeignKey("party.id"), nullable=True)
    
    role = relationship("Role", back_populates="users",
                         primaryjoin="Role.id == User.role_id")
    party = relationship("Party", back_populates="users",
                         primaryjoin="Party.id == User.party_id")

    userCredentials = relationship("UserCredential", back_populates="user",
                         primaryjoin="UserCredential.user_id == User.id")


    email = mapped_column(String(512), index=True, nullable=True)
    short_name = mapped_column(String(256), index=True, nullable=True)
    phone_code = mapped_column(String(24), index=True, nullable=True)
    phone_number = mapped_column(String(256), index=True, nullable=True)


    # userCredentials: fields.ReverseRelation["UserCredential"]
    # userSessions: fields.ReverseRelation["UserSession"]
    # userRequests: fields.ReverseRelation["UserRequest"]
    
    def __repr__(self):
        return f"{self.name}"
    

class UserCredential(Base, _ModelBaseAccess):
    __tablename__ = "usercredential"
  
    user_id = mapped_column(ForeignKey("user.id"), nullable=True)
    
    user = relationship("User", back_populates="userCredentials",
                         primaryjoin="UserCredential.user_id == User.id")
    
    credential_type = mapped_column(Enum(UserCredentialType), index=True)
    status = mapped_column(String(10), index=True, nullable=True)
    username = mapped_column(String(256), index=True, unique=True, nullable=True)
    password_hash = mapped_column(String(256), index=True, nullable=True)
    
    def __repr__(self):
        return f"{self.name}"

# class UserSession(Model, _ModelBaseAccess):
#     user = fields.ForeignKeyField("models.User", related_name="userSessions", null=True)
#     access_token = fields.CharField(max_length=256, index=True, null=True)
#     refresh_token = fields.CharField(max_length=256, index=True, null=True)
#     issued_at = fields.DatetimeField(null=True)
#     def __str__(self):
#         return self.name

# class UserRequest(Model, _ModelBaseAccess, _ModelBaseBody):
#     user = fields.ForeignKeyField("models.User", related_name="userRequests", null=True)
#     request_type = fields.CharEnumField(enum_type=UserRequestType, index=True, null=True)
#     status = fields.CharField(max_length=10, index=True, null=True)
#     token = fields.CharField(max_length=256, index=True, null=True)
#     code = fields.CharField(max_length=256, index=True, null=True)
#     def __str__(self):
#         return self.name

# class Chat(Model, _ModelBaseAccess):
#     category = fields.ForeignKeyField("models.Category", related_name="chats", null=True)
#     userAsCreator = fields.ForeignKeyField("models.User", related_name="userCreatedChats", null=True)
#     chatmessages: fields.ReverseRelation["ChatMessage"]
#     prompt_prefix = fields.CharField(max_length=2048, default="")
#     def __str__(self):
#         return self.name

# class ChatMessage(Model, _ModelBaseAccess, _ModelBaseBody):
#     chat = fields.ForeignKeyField("models.Chat", related_name="chatMessages", null=True)
#     user = fields.ForeignKeyField("models.User", related_name="chatMessages", null=True)
#     chatmessagefeedbacks: fields.ReverseRelation["ChatMessageFeedback"]
#     def __str__(self):
#         return self.name

# class ChatMessageFeedback(Model, _ModelBaseAccess, _ModelBaseBody):
#     chatmessage = fields.ForeignKeyField("models.ChatMessage", related_name="chatMessageFeedbacks", null=True)
#     user = fields.ForeignKeyField("models.User", related_name="chatMessageFeedbacks", null=True)
#     score = fields.IntField(null=True)
#     is_like = fields.BooleanField(default=False)
#     is_dislike = fields.BooleanField(default=False)
#     def __str__(self):
#         return self.name



# class ZRelRoleAccessibleCategory(Model):
#     role = fields.ForeignKeyField("models.Role", null=True, related_name="ZRelRoleAccessibleCategory")
#     category = fields.ForeignKeyField("models.Category", null=True, related_name="ZRelRoleAccessibleCategory")
#     created_at = fields.DatetimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name
    
#     class Meta:
#         table = "z_rel_role_accessible_category"
    
    

class ZRelRolePermission(Base):
    __tablename__ = "z_rel_role_permission"

    role_id = mapped_column(ForeignKey("role.id"), nullable=True)
    permission_id = mapped_column(ForeignKey("permission.id"), nullable=True)
    
    role = relationship("Role", back_populates="z_rel_role_permission_permission_associations")
    permission = relationship("Permission", back_populates="z_rel_role_permission_role_associations")

    created_at = mapped_column(DateTime, default=datetime.now())

    def __repr__(self):
        return f"{self.name}"


# class ZRelPartyAccessibleSharedCategory(Model):
#     party = fields.ForeignKeyField("models.Party", null=True, related_name="ZRelPartyAccessibleSharedCategory")
#     category = fields.ForeignKeyField("models.Category", null=True, related_name="ZRelPartyAccessibleSharedCategory")
#     created_at = fields.DatetimeField(auto_now_add=True)

#     def __str__(self):
#         return self.name
    
#     class Meta:
#         table = "z_rel_party_accessible_shared_category"
    

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
