from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `user` ADD `username` VARCHAR(256) NOT NULL DEFAULT '';
        UPDATE `user` u
        LEFT JOIN `usercredential` uc ON uc.`user_id` = u.`id`
        SET u.`username` = COALESCE(uc.`username`, u.`username`)
        WHERE u.`username` = '';
        ALTER TABLE `user` ADD KEY `idx_user_usernam_327acb` (`username`);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `user` DROP INDEX `idx_user_usernam_327acb`;
        ALTER TABLE `user` DROP COLUMN `username`;"""