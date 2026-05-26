from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        INSERT IGNORE INTO `permission` (`id`, `is_disabled`, `is_deleted`, `created_at`, `modified_at`, `name`, `desc`, `body`, `body_json`, `code`) VALUES
            ('14017e97-7a52-42b4-9ab3-52a21ba4a5bf', 0, 0, '2024-05-10 11:59:00.049282', '2024-05-10 11:59:00.049303', '', NULL, NULL, NULL, 'category -> manage'),
            ('26111e9c-a128-46e4-95f0-6a6c0c39b7a8', 0, 0, '2024-05-10 11:59:00.055415', '2024-05-10 11:59:00.055433', '', NULL, NULL, NULL, 'permission -> manage'),
            ('34017e97-6a52-32b4-cab3-52a21ba4a5bf', 0, 0, '2024-05-10 11:59:00.049282', '2024-05-10 11:59:00.049303', '', NULL, NULL, NULL, 'category -> upload'),
            ('440af212-8e53-4d7c-9b23-7674cee23fca', 0, 0, '2024-05-10 11:59:00.053346', '2024-05-10 11:59:00.053364', '', NULL, NULL, NULL, 'role -> manage'),
            ('8478b0ad-eac2-402c-855a-e02d9f59da7e', 0, 0, '2024-05-31 07:53:36.433140', '2024-05-31 07:53:36.433245', '', NULL, NULL, NULL, 'superadmin -> manage_partys'),
            ('850b5d30-fbde-4b7e-9db5-ba6de30baf4a', 0, 0, '2024-05-10 11:59:00.045053', '2024-05-10 11:59:00.045073', '', NULL, NULL, NULL, 'user -> manage'),
            ('8b9cffad-243c-4f1b-8ae1-16074620cca2', 0, 0, '2024-05-10 11:59:00.051407', '2024-05-10 11:59:00.051426', '', NULL, NULL, NULL, 'file -> manage'),
            ('b7663744-78d0-4268-9021-36b179b1d9f7', 0, 0, '2024-05-10 11:59:00.057298', '2024-05-10 11:59:00.057314', '', NULL, NULL, NULL, 'knowledge -> search'),
            ('e46bf8b2-6301-4c3b-b72d-93d94c86fe3b', 0, 0, '2024-05-31 07:53:36.449374', '2024-05-31 07:53:36.449424', '', NULL, NULL, NULL, 'superadmin -> manage_shared_categorys');

        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '14017e97-7a52-42b4-9ab3-52a21ba4a5bf'
        WHERE p.`code` = 'category -> manage';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '26111e9c-a128-46e4-95f0-6a6c0c39b7a8'
        WHERE p.`code` = 'permission -> manage';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '34017e97-6a52-32b4-cab3-52a21ba4a5bf'
        WHERE p.`code` = 'category -> upload';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '440af212-8e53-4d7c-9b23-7674cee23fca'
        WHERE p.`code` = 'role -> manage';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '8478b0ad-eac2-402c-855a-e02d9f59da7e'
        WHERE p.`code` = 'superadmin -> manage_partys';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '850b5d30-fbde-4b7e-9db5-ba6de30baf4a'
        WHERE p.`code` = 'user -> manage';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = '8b9cffad-243c-4f1b-8ae1-16074620cca2'
        WHERE p.`code` = 'file -> manage';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = 'b7663744-78d0-4268-9021-36b179b1d9f7'
        WHERE p.`code` = 'knowledge -> search';
        UPDATE `_rel_role_permission` rp
        JOIN `permission` p ON p.`id` = rp.`permission_id`
        SET rp.`permission_id` = 'e46bf8b2-6301-4c3b-b72d-93d94c86fe3b'
        WHERE p.`code` = 'superadmin -> manage_shared_categorys';

        CREATE TEMPORARY TABLE `_rel_role_permission_dedup` AS
        SELECT DISTINCT `permission_id`, `role_id`
        FROM `_rel_role_permission`;
        DELETE FROM `_rel_role_permission`;
        INSERT INTO `_rel_role_permission` (`permission_id`, `role_id`)
        SELECT `permission_id`, `role_id`
        FROM `_rel_role_permission_dedup`;
        DROP TEMPORARY TABLE `_rel_role_permission_dedup`;

        DELETE FROM `permission` WHERE `code` = 'category -> manage' AND `id` <> '14017e97-7a52-42b4-9ab3-52a21ba4a5bf';
        DELETE FROM `permission` WHERE `code` = 'permission -> manage' AND `id` <> '26111e9c-a128-46e4-95f0-6a6c0c39b7a8';
        DELETE FROM `permission` WHERE `code` = 'category -> upload' AND `id` <> '34017e97-6a52-32b4-cab3-52a21ba4a5bf';
        DELETE FROM `permission` WHERE `code` = 'role -> manage' AND `id` <> '440af212-8e53-4d7c-9b23-7674cee23fca';
        DELETE FROM `permission` WHERE `code` = 'superadmin -> manage_partys' AND `id` <> '8478b0ad-eac2-402c-855a-e02d9f59da7e';
        DELETE FROM `permission` WHERE `code` = 'user -> manage' AND `id` <> '850b5d30-fbde-4b7e-9db5-ba6de30baf4a';
        DELETE FROM `permission` WHERE `code` = 'file -> manage' AND `id` <> '8b9cffad-243c-4f1b-8ae1-16074620cca2';
        DELETE FROM `permission` WHERE `code` = 'knowledge -> search' AND `id` <> 'b7663744-78d0-4268-9021-36b179b1d9f7';
        DELETE FROM `permission` WHERE `code` = 'superadmin -> manage_shared_categorys' AND `id` <> 'e46bf8b2-6301-4c3b-b72d-93d94c86fe3b';

        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.049282', `modified_at` = '2024-05-10 11:59:00.049303' WHERE `id` = '14017e97-7a52-42b4-9ab3-52a21ba4a5bf';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.055415', `modified_at` = '2024-05-10 11:59:00.055433' WHERE `id` = '26111e9c-a128-46e4-95f0-6a6c0c39b7a8';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.049282', `modified_at` = '2024-05-10 11:59:00.049303' WHERE `id` = '34017e97-6a52-32b4-cab3-52a21ba4a5bf';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.053346', `modified_at` = '2024-05-10 11:59:00.053364' WHERE `id` = '440af212-8e53-4d7c-9b23-7674cee23fca';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-31 07:53:36.433140', `modified_at` = '2024-05-31 07:53:36.433245' WHERE `id` = '8478b0ad-eac2-402c-855a-e02d9f59da7e';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.045053', `modified_at` = '2024-05-10 11:59:00.045073' WHERE `id` = '850b5d30-fbde-4b7e-9db5-ba6de30baf4a';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.051407', `modified_at` = '2024-05-10 11:59:00.051426' WHERE `id` = '8b9cffad-243c-4f1b-8ae1-16074620cca2';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-10 11:59:00.057298', `modified_at` = '2024-05-10 11:59:00.057314' WHERE `id` = 'b7663744-78d0-4268-9021-36b179b1d9f7';
        UPDATE `permission` SET `is_disabled` = 0, `is_deleted` = 0, `name` = '', `desc` = NULL, `body` = NULL, `body_json` = NULL, `created_at` = '2024-05-31 07:53:36.449374', `modified_at` = '2024-05-31 07:53:36.449424' WHERE `id` = 'e46bf8b2-6301-4c3b-b72d-93d94c86fe3b';

        ALTER TABLE `permission` ADD CONSTRAINT `unique_permission_code_9b9d76` UNIQUE (`code`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `permission` DROP INDEX `unique_permission_code_9b9d76`;"""