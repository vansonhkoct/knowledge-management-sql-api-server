from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `log` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `type` VARCHAR(10),
    `field1` LONGTEXT,
    `field2` LONGTEXT,
    `field3` LONGTEXT,
    `user_id` CHAR(36),
    CONSTRAINT `fk_log_user_5dd73170` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
    KEY `idx_log_is_disa_053e97` (`is_disabled`),
    KEY `idx_log_is_dele_5eba41` (`is_deleted`),
    KEY `idx_log_type_2cf691` (`type`)
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `log`;"""
