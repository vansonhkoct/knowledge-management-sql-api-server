from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `role_permission_assignment` (
            `id` CHAR(36) NOT NULL PRIMARY KEY,
            `permission_code` VARCHAR(64) NOT NULL,
            `role_id` CHAR(36) NOT NULL,
            UNIQUE KEY `uid_role_permission_code` (`role_id`, `permission_code`),
            KEY `idx_role_permission_code` (`permission_code`),
            KEY `idx_role_permission_role` (`role_id`),
            CONSTRAINT `fk_role_permission_role` FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4;

        INSERT IGNORE INTO `role_permission_assignment` (`id`, `role_id`, `permission_code`)
        SELECT UUID(), rp.`role_id`,
            CASE p.`code`
                WHEN 'user -> manage' THEN 'user.manage'
                WHEN 'file -> manage' THEN 'file.manage'
                WHEN 'admin -> manage_file_indexing' THEN 'file.index'
                WHEN 'role -> manage' THEN 'role.manage'
                WHEN 'category -> manage' THEN 'category.manage'
                WHEN 'category -> upload' THEN 'category.upload'
                WHEN 'knowledge -> search' THEN 'knowledge.search'
                WHEN 'superadmin -> manage_partys' THEN 'party.manage'
                WHEN 'superadmin -> manage_shared_categorys' THEN 'shared_category.manage'
                ELSE p.`code`
            END
        FROM `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        WHERE p.`code` IN (
            'user -> manage', 'file -> manage', 'admin -> manage_file_indexing',
            'role -> manage', 'category -> manage', 'category -> upload',
            'knowledge -> search', 'superadmin -> manage_partys',
            'superadmin -> manage_shared_categorys', 'user.manage', 'file.manage',
            'file.index', 'role.manage', 'category.manage', 'category.upload',
            'knowledge.search', 'party.manage', 'shared_category.manage'
        );

        INSERT IGNORE INTO `role_permission_assignment` (`id`, `role_id`, `permission_code`)
        SELECT UUID(), r.`id`, codes.`permission_code`
        FROM `role` r
        CROSS JOIN (
            SELECT 'user.manage' AS `permission_code`
            UNION ALL SELECT 'file.manage'
            UNION ALL SELECT 'file.index'
            UNION ALL SELECT 'role.manage'
            UNION ALL SELECT 'category.manage'
            UNION ALL SELECT 'category.upload'
            UNION ALL SELECT 'knowledge.search'
            UNION ALL SELECT 'party.manage'
            UNION ALL SELECT 'shared_category.manage'
        ) codes
        WHERE r.`code` = 'superadmin'
          AND r.`is_disabled` = 0
          AND r.`is_deleted` = 0;

        DROP TABLE `_rel_role_permission`;
        DROP TABLE `permission`;
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `permission` (
            `id` CHAR(36) NOT NULL PRIMARY KEY,
            `is_disabled` BOOL NOT NULL DEFAULT 0,
            `is_deleted` BOOL NOT NULL DEFAULT 0,
            `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
            `modified_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
            `name` VARCHAR(255) NOT NULL DEFAULT '',
            `desc` LONGTEXT,
            `body` LONGTEXT,
            `body_json` JSON,
            `code` VARCHAR(64),
            UNIQUE KEY `unique_permission_code_9b9d76` (`code`)
        ) CHARACTER SET utf8mb4;

        CREATE TABLE `_rel_role_permission` (
            `permission_id` CHAR(36) NOT NULL,
            `role_id` CHAR(36) NOT NULL,
            FOREIGN KEY (`permission_id`) REFERENCES `permission` (`id`) ON DELETE CASCADE,
            FOREIGN KEY (`role_id`) REFERENCES `role` (`id`) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4;

        INSERT INTO `permission` (`id`, `code`)
        SELECT UUID(), codes.`permission_code`
        FROM (
            SELECT DISTINCT `permission_code`
            FROM `role_permission_assignment`
        ) codes;

        INSERT INTO `_rel_role_permission` (`permission_id`, `role_id`)
        SELECT p.`id`, assignment.`role_id`
        FROM `role_permission_assignment` assignment
        JOIN `permission` p ON p.`code` = assignment.`permission_code`;

        DROP TABLE `role_permission_assignment`;
    """
