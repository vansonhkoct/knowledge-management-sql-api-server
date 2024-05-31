from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `_rel_party_accessible_shared_category` ADD `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `_rel_party_accessible_shared_category` DROP COLUMN `created_at`;"""
