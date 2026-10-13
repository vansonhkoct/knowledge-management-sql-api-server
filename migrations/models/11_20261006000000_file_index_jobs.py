from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `file` ADD `index_status` VARCHAR(24) NOT NULL DEFAULT 'NOT_INDEXED';
        ALTER TABLE `file` ADD `index_error` LONGTEXT;
        ALTER TABLE `file` ADD `index_attempt_count` INT NOT NULL DEFAULT 0;
        ALTER TABLE `file` ADD `index_version` VARCHAR(64);
        ALTER TABLE `file` ADD `source_hash` VARCHAR(64);
        ALTER TABLE `file` ADD `indexed_source_hash` VARCHAR(64);
        ALTER TABLE `file` ADD `indexed_at` DATETIME(6);
        ALTER TABLE `file` ADD KEY `idx_file_index_status_d37d31` (`index_status`);

        UPDATE `file`
        SET `index_status` = 'NOT_INDEXED', `index_error` = NULL;

        CREATE TABLE `file_index_job` (
            `id` CHAR(36) NOT NULL PRIMARY KEY,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `modified_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            `status` VARCHAR(24) NOT NULL DEFAULT 'QUEUED',
            `attempt` INT NOT NULL DEFAULT 0,
            `error` LONGTEXT,
            `source_hash` VARCHAR(64),
            `index_version` VARCHAR(64),
            `started_at` DATETIME(6),
            `completed_at` DATETIME(6),
            `file_id` CHAR(36) NOT NULL,
            `party_id` CHAR(36) NOT NULL,
            `requested_by_id` CHAR(36),
            KEY `idx_file_index_job_status_07ae2a` (`status`),
            KEY `idx_file_index_job_file_id_28737a` (`file_id`),
            KEY `idx_file_index_job_party_id_f4a2ba` (`party_id`),
            KEY `idx_file_index_job_requested_by_id_7bd62c` (`requested_by_id`),
            CONSTRAINT `fk_file_index_job_file` FOREIGN KEY (`file_id`) REFERENCES `file` (`id`) ON DELETE CASCADE,
            CONSTRAINT `fk_file_index_job_party` FOREIGN KEY (`party_id`) REFERENCES `party` (`id`) ON DELETE CASCADE,
            CONSTRAINT `fk_file_index_job_requested_by` FOREIGN KEY (`requested_by_id`) REFERENCES `user` (`id`) ON DELETE SET NULL
        ) CHARACTER SET utf8mb4;

        INSERT IGNORE INTO `permission`
            (`id`, `is_disabled`, `is_deleted`, `created_at`, `modified_at`, `name`, `desc`, `body`, `body_json`, `code`)
        VALUES
            ('c73e9b54-f29e-4a11-8ac8-f84f0ca6b2e4', 0, 0, CURRENT_TIMESTAMP(6), CURRENT_TIMESTAMP(6), '', NULL, NULL, NULL, 'admin -> manage_file_indexing');

        INSERT INTO `_rel_role_permission` (`permission_id`, `role_id`)
        SELECT p.`id`, r.`id`
        FROM `role` r
        JOIN `permission` p ON p.`code` = 'admin -> manage_file_indexing'
        WHERE r.`code` = 'admin'
          AND r.`is_deleted` = 0
          AND NOT EXISTS (
            SELECT 1 FROM `_rel_role_permission` rp
            WHERE rp.`permission_id` = p.`id`
              AND rp.`role_id` = r.`id`
          );
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DELETE rp FROM `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        WHERE p.`code` = 'admin -> manage_file_indexing';
        DELETE FROM `permission` WHERE `code` = 'admin -> manage_file_indexing';
        DROP TABLE IF EXISTS `file_index_job`;
        ALTER TABLE `file` DROP INDEX `idx_file_index_status_d37d31`;
        ALTER TABLE `file` DROP COLUMN `index_status`;
        ALTER TABLE `file` DROP COLUMN `index_error`;
        ALTER TABLE `file` DROP COLUMN `index_attempt_count`;
        ALTER TABLE `file` DROP COLUMN `index_version`;
        ALTER TABLE `file` DROP COLUMN `source_hash`;
        ALTER TABLE `file` DROP COLUMN `indexed_source_hash`;
        ALTER TABLE `file` DROP COLUMN `indexed_at`;
    """
