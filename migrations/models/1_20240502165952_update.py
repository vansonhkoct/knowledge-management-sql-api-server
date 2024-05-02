from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `category` ADD `alias` VARCHAR(512);
        ALTER TABLE `file` ADD `alias` VARCHAR(512);
        ALTER TABLE `file` MODIFY COLUMN `filename` VARCHAR(255);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `file` DROP COLUMN `alias`;
        ALTER TABLE `file` MODIFY COLUMN `filename` VARCHAR(5120);
        ALTER TABLE `category` DROP COLUMN `alias`;"""
