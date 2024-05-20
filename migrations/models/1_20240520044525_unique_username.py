from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `usercredential` ADD CONSTRAINT unique_usercredential_username_000000 UNIQUE (username);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `usercredential` DROP CONSTRAINT unique_usercredential_username_000000;"""
