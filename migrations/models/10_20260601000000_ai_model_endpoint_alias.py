from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `ai_model_endpoint`
        ADD `assistant_alias` VARCHAR(255) NOT NULL DEFAULT 'Knowledge Management Assistant';
    """


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `ai_model_endpoint`
        DROP COLUMN `assistant_alias`;
    """