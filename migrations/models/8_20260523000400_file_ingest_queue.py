from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `file` ADD `status` VARCHAR(24);
        ALTER TABLE `file` ADD `latest_process_message` LONGTEXT;
        ALTER TABLE `file` ADD `ingest_error` LONGTEXT;
        ALTER TABLE `file` ADD `document_tags_json` JSON;
        ALTER TABLE `file` ADD `document_title` VARCHAR(1024);
        ALTER TABLE `file` ADD `document_summary` LONGTEXT;
        ALTER TABLE `file` ADD `document_remarks` LONGTEXT;
        ALTER TABLE `file` ADD `document_userdata_json` JSON;
        ALTER TABLE `file` ADD KEY `idx_file_status_3dbfa5` (`status`);
        CREATE TABLE `file_process_log` (
    `id` CHAR(36) NOT NULL PRIMARY KEY,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `stage` VARCHAR(24) NOT NULL,
    `status` VARCHAR(24) NOT NULL,
    `message` LONGTEXT,
    `details_json` JSON,
    `file_id` CHAR(36) NOT NULL,
    KEY `idx_file_process_log_stage_713e91` (`stage`),
    KEY `idx_file_process_log_status_8d4a66` (`status`),
    KEY `idx_file_process_log_file_id_6f49a6` (`file_id`),
    CONSTRAINT `fk_file_process_log_file` FOREIGN KEY (`file_id`) REFERENCES `file` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `file_process_log` DROP FOREIGN KEY `fk_file_process_log_file`;
        DROP TABLE IF EXISTS `file_process_log`;
        ALTER TABLE `file` DROP INDEX `idx_file_status_3dbfa5`;
        ALTER TABLE `file` DROP COLUMN `status`;
        ALTER TABLE `file` DROP COLUMN `latest_process_message`;
        ALTER TABLE `file` DROP COLUMN `ingest_error`;
        ALTER TABLE `file` DROP COLUMN `document_tags_json`;
        ALTER TABLE `file` DROP COLUMN `document_title`;
        ALTER TABLE `file` DROP COLUMN `document_summary`;
        ALTER TABLE `file` DROP COLUMN `document_remarks`;
        ALTER TABLE `file` DROP COLUMN `document_userdata_json`;
    """