from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `category` ADD `party_id` CHAR(36) NOT NULL;
        ALTER TABLE `category` ADD CONSTRAINT `fk_category_party_88d7ddd8` FOREIGN KEY (`party_id`) REFERENCES `party` (`_id`) ON DELETE CASCADE;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `category` DROP FOREIGN KEY `fk_category_party_88d7ddd8`;
        ALTER TABLE `category` DROP COLUMN `party_id`;"""
