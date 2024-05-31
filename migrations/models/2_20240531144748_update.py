from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE IF NOT EXISTS `_rel_party_accessible_shared_category` (
    `id` INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    `category_id` CHAR(36),
    `party_id` CHAR(36),
    CONSTRAINT `fk__rel_par_category_8513b219` FOREIGN KEY (`category_id`) REFERENCES `category` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk__rel_par_party_39059ed0` FOREIGN KEY (`party_id`) REFERENCES `party` (`id`) ON DELETE CASCADE
) CHARACTER SET utf8mb4;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        DROP TABLE IF EXISTS `_rel_party_accessible_shared_category`;"""
