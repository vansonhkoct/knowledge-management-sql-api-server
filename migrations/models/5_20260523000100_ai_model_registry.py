from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        CREATE TABLE `ai_model_endpoint` (
    `id` CHAR(36) NOT NULL  PRIMARY KEY,
    `is_disabled` BOOL NOT NULL  DEFAULT 0,
    `is_deleted` BOOL NOT NULL  DEFAULT 0,
    `created_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6),
    `modified_at` DATETIME(6) NOT NULL  DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    `name` VARCHAR(255) NOT NULL  DEFAULT '',
    `desc` LONGTEXT,
    `body` LONGTEXT,
    `body_json` JSON,
    `model_type` VARCHAR(16) NOT NULL,
    `provider` VARCHAR(64) NOT NULL  DEFAULT 'openai-compatible',
    `base_url` VARCHAR(2048) NOT NULL,
    `api_path` VARCHAR(512) NOT NULL  DEFAULT '/v1',
    `api_key` VARCHAR(2048),
    `model_name` VARCHAR(255) NOT NULL,
    `headers_json` JSON,
    `options_json` JSON,
    KEY `idx_ai_model_en_is_disa_66bb10` (`is_disabled`),
    KEY `idx_ai_model_en_is_dele_6f5285` (`is_deleted`),
    KEY `idx_ai_model_en_model_t_0d5d59` (`model_type`),
    KEY `idx_ai_model_en_model_n_2c76e4` (`model_name`)
) CHARACTER SET utf8mb4;
        ALTER TABLE `party` ADD `default_llm_model_id` CHAR(36);
        ALTER TABLE `party` ADD `default_embedding_model_id` CHAR(36);
        ALTER TABLE `party` ADD KEY `idx_party_default__llm_7c9f80` (`default_llm_model_id`);
        ALTER TABLE `party` ADD KEY `idx_party_default__embedding_7915da` (`default_embedding_model_id`);
        ALTER TABLE `party` ADD CONSTRAINT `fk_party_ai_model_llm` FOREIGN KEY (`default_llm_model_id`) REFERENCES `ai_model_endpoint` (`id`) ON DELETE SET NULL;
        ALTER TABLE `party` ADD CONSTRAINT `fk_party_ai_model_embedding` FOREIGN KEY (`default_embedding_model_id`) REFERENCES `ai_model_endpoint` (`id`) ON DELETE SET NULL;"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE `party` DROP FOREIGN KEY `fk_party_ai_model_llm`;
        ALTER TABLE `party` DROP FOREIGN KEY `fk_party_ai_model_embedding`;
        ALTER TABLE `party` DROP INDEX `idx_party_default__llm_7c9f80`;
        ALTER TABLE `party` DROP INDEX `idx_party_default__embedding_7915da`;
        ALTER TABLE `party` DROP COLUMN `default_llm_model_id`;
        ALTER TABLE `party` DROP COLUMN `default_embedding_model_id`;
        DROP TABLE IF EXISTS `ai_model_endpoint`;"""