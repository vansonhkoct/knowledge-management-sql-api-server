from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `chat` ADD `last_message_at` DATETIME(6);
        ALTER TABLE `chat` ADD `last_message_preview` LONGTEXT;
        ALTER TABLE `chat` ADD `title_is_user_defined` BOOL NOT NULL  DEFAULT 0;
        ALTER TABLE `chat` ADD `user_id` CHAR(36);
        ALTER TABLE `chat` ADD `party_id` CHAR(36);
        ALTER TABLE `chatmessage` ADD `citations_json` JSON;
        ALTER TABLE `chatmessage` ADD `retrieval_enabled` BOOL;
        ALTER TABLE `chatmessage` ADD `category_alias_snapshot` VARCHAR(512);
        ALTER TABLE `chatmessage` ADD `role` VARCHAR(24) NOT NULL  DEFAULT 'USER';
        ALTER TABLE `chatmessage` ADD `category_id_snapshot` CHAR(36);
        ALTER TABLE `chatmessage` ADD `message_metadata_json` JSON;
        ALTER TABLE `chat` ADD CONSTRAINT `fk_chat_user_6dac522c` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE;
        ALTER TABLE `chat` ADD CONSTRAINT `fk_chat_party_901bdf8a` FOREIGN KEY (`party_id`) REFERENCES `party` (`id`) ON DELETE CASCADE;
        ALTER TABLE `chatmessage` ADD INDEX `idx_chatmessage_role_44e377` (`role`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `chatmessage` DROP INDEX `idx_chatmessage_role_44e377`;
        ALTER TABLE `chat` DROP FOREIGN KEY `fk_chat_party_901bdf8a`;
        ALTER TABLE `chat` DROP FOREIGN KEY `fk_chat_user_6dac522c`;
        ALTER TABLE `chat` DROP COLUMN `last_message_at`;
        ALTER TABLE `chat` DROP COLUMN `last_message_preview`;
        ALTER TABLE `chat` DROP COLUMN `title_is_user_defined`;
        ALTER TABLE `chat` DROP COLUMN `user_id`;
        ALTER TABLE `chat` DROP COLUMN `party_id`;
        ALTER TABLE `chatmessage` DROP COLUMN `citations_json`;
        ALTER TABLE `chatmessage` DROP COLUMN `retrieval_enabled`;
        ALTER TABLE `chatmessage` DROP COLUMN `category_alias_snapshot`;
        ALTER TABLE `chatmessage` DROP COLUMN `role`;
        ALTER TABLE `chatmessage` DROP COLUMN `category_id_snapshot`;
        ALTER TABLE `chatmessage` DROP COLUMN `message_metadata_json`;"""
