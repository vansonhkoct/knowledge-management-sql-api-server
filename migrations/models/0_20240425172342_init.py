from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `category` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    KEY `idx_category_is_disa_488bff` (`is_disabled`),
    KEY `idx_category_is_dele_f4470e` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chat` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `prompt_prefix` VARCHAR(2048) NOT NULL  DEFAULT '',
    `categorys_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_chat_category_545c5737` FOREIGN KEY (`categorys_id`) REFERENCES `category` (`_id`) ON DELETE CASCADE,
    KEY `idx_chat_is_disa_1107c3` (`is_disabled`),
    KEY `idx_chat_is_dele_2df0a7` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `file` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `filename` VARCHAR(5120),
    `mime_type` VARCHAR(64),
    `size_bytes` INT,
    KEY `idx_file_is_disa_d4ee3a` (`is_disabled`),
    KEY `idx_file_is_dele_3c04e3` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `party` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    KEY `idx_party_is_disa_5219b1` (`is_disabled`),
    KEY `idx_party_is_dele_c64e73` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `permission` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    KEY `idx_permission_is_disa_6f3608` (`is_disabled`),
    KEY `idx_permission_is_dele_02b890` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `role` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    KEY `idx_role_is_disa_faae6d` (`is_disabled`),
    KEY `idx_role_is_dele_bb0fba` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `user` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `email` VARCHAR(512),
    `short_name` VARCHAR(256),
    `phone_code` VARCHAR(24),
    `phone_number` VARCHAR(256),
    `role_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_user_role_9fbc3534` FOREIGN KEY (`role_id`) REFERENCES `role` (`_id`) ON DELETE CASCADE,
    KEY `idx_user_is_disa_8f0eb2` (`is_disabled`),
    KEY `idx_user_is_dele_0c3788` (`is_deleted`),
    KEY `idx_user_email_1b4f1c` (`email`),
    KEY `idx_user_short_n_279079` (`short_name`),
    KEY `idx_user_phone_c_c70cc8` (`phone_code`),
    KEY `idx_user_phone_n_c3c403` (`phone_number`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chatmessage` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `chat_id` CHAR(36) NOT NULL,
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_chatmess_chat_c575971c` FOREIGN KEY (`chat_id`) REFERENCES `chat` (`_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_chatmess_user_937278f5` FOREIGN KEY (`user_id`) REFERENCES `user` (`_id`) ON DELETE CASCADE,
    KEY `idx_chatmessage_is_disa_0939fb` (`is_disabled`),
    KEY `idx_chatmessage_is_dele_9e8e5f` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `chatmessagefeedback` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `score` INT,
    `is_like` BOOL NOT NULL  DEFAULT 0,
    `is_dislike` BOOL NOT NULL  DEFAULT 0,
    `chatmessage_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_chatmess_chatmess_c841e7b1` FOREIGN KEY (`chatmessage_id`) REFERENCES `chatmessage` (`_id`) ON DELETE CASCADE,
    KEY `idx_chatmessage_is_disa_44836c` (`is_disabled`),
    KEY `idx_chatmessage_is_dele_59b181` (`is_deleted`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `usercredential` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `credential_type` VARCHAR(5) NOT NULL  COMMENT 'EMAIL: EMAIL\nPHONE: PHONE\nMSAL: MSAL',
    `status` VARCHAR(10),
    `username` VARCHAR(256),
    `password_hash` VARCHAR(256),
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_usercred_user_3e81c1f5` FOREIGN KEY (`user_id`) REFERENCES `user` (`_id`) ON DELETE CASCADE,
    KEY `idx_usercredent_is_disa_ff4411` (`is_disabled`),
    KEY `idx_usercredent_is_dele_2413cc` (`is_deleted`),
    KEY `idx_usercredent_credent_804412` (`credential_type`),
    KEY `idx_usercredent_status_be79eb` (`status`),
    KEY `idx_usercredent_usernam_3d0708` (`username`),
    KEY `idx_usercredent_passwor_0b6c1c` (`password_hash`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `userrequest` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `request_type` VARCHAR(22)   COMMENT 'ACCOUNT_REGISTER: ACCOUNT_REGISTER\nACCOUNT_RESET_PASSWORD: ACCOUNT_RESET_PASSWORD',
    `status` VARCHAR(10),
    `token` VARCHAR(256),
    `code` VARCHAR(256),
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_userrequ_user_1c63c275` FOREIGN KEY (`user_id`) REFERENCES `user` (`_id`) ON DELETE CASCADE,
    KEY `idx_userrequest_is_disa_3f92b9` (`is_disabled`),
    KEY `idx_userrequest_is_dele_298701` (`is_deleted`),
    KEY `idx_userrequest_request_04292f` (`request_type`),
    KEY `idx_userrequest_status_116914` (`status`),
    KEY `idx_userrequest_token_f580c0` (`token`),
    KEY `idx_userrequest_code_143cf6` (`code`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `usersession` (
    `_id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `access_token` VARCHAR(256),
    `refresh_token` VARCHAR(256),
    `issued_at` DATETIME(6),
    `user_id` CHAR(36) NOT NULL,
    CONSTRAINT `fk_usersess_user_f7ed35c2` FOREIGN KEY (`user_id`) REFERENCES `user` (`_id`) ON DELETE CASCADE,
    KEY `idx_usersession_is_disa_13f338` (`is_disabled`),
    KEY `idx_usersession_is_dele_1c589c` (`is_deleted`),
    KEY `idx_usersession_access__aa6c11` (`access_token`),
    KEY `idx_usersession_refresh_033a81` (`refresh_token`)
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `aerich` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `version` VARCHAR(255) NOT NULL,
    `app` VARCHAR(100) NOT NULL,
    `content` JSON NOT NULL
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `_rel_file_category` (
    `category_id` CHAR(36) NOT NULL,
    `file_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`category_id`) REFERENCES `category` (`_id`) ON DELETE CASCADE,
    FOREIGN KEY (`file_id`) REFERENCES `file` (`_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `_rel_party_user` (
    `party_id` CHAR(36) NOT NULL,
    `user_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`party_id`) REFERENCES `party` (`_id`) ON DELETE CASCADE,
    FOREIGN KEY (`user_id`) REFERENCES `user` (`_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `_rel_role_permission` (
    `permission_id` CHAR(36) NOT NULL,
    `role_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`_id`) ON DELETE CASCADE,
    FOREIGN KEY (`role_id`) REFERENCES `role` (`_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;
CREATE TABLE IF NOT EXISTS `_rel_permission_category` (
    `permission_id` CHAR(36) NOT NULL,
    `category_id` CHAR(36) NOT NULL,
    FOREIGN KEY (`permission_id`) REFERENCES `permission` (`_id`) ON DELETE CASCADE,
    FOREIGN KEY (`category_id`) REFERENCES `category` (`_id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        """
