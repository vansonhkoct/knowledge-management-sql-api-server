from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `category` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `chat` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `chatmessage` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `chatmessagefeedback` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `file` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `party` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `permission` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `role` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `user` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `usercredential` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `userrequest` RENAME COLUMN `_id` TO `id`;
        ALTER TABLE `usersession` RENAME COLUMN `_id` TO `id`;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `chat` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `file` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `role` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `user` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `party` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `category` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `permission` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `chatmessage` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `userrequest` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `usersession` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `usercredential` RENAME COLUMN `id` TO `_id`;
        ALTER TABLE `chatmessagefeedback` RENAME COLUMN `id` TO `_id`;"""
