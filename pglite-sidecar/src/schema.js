export const schemaVersion = 1

export const schemaSql = `
  CREATE EXTENSION IF NOT EXISTS vector;

  CREATE TABLE IF NOT EXISTS rag_schema_migration (
    version integer PRIMARY KEY,
    applied_at timestamptz NOT NULL DEFAULT now()
  );

  CREATE TABLE IF NOT EXISTS rag_profile (
    id uuid PRIMARY KEY,
    model_name text NOT NULL,
    vector_dimension integer NOT NULL CHECK (vector_dimension > 0),
    index_version text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    modified_at timestamptz NOT NULL DEFAULT now()
  );

  CREATE TABLE IF NOT EXISTS rag_chunk (
    id uuid PRIMARY KEY,
    party_id uuid NOT NULL,
    file_id uuid NOT NULL,
    category_id uuid,
    profile_id uuid NOT NULL REFERENCES rag_profile(id),
    chunk_index integer NOT NULL,
    page_number integer,
    representation text NOT NULL DEFAULT 'CHUNK',
    content text NOT NULL,
    content_hash char(64) NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    embedding vector NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (file_id, profile_id, chunk_index, representation)
  );

  CREATE INDEX IF NOT EXISTS rag_chunk_party_profile_idx
    ON rag_chunk (party_id, profile_id);
  CREATE INDEX IF NOT EXISTS rag_chunk_file_idx
    ON rag_chunk (file_id);
  CREATE INDEX IF NOT EXISTS rag_chunk_category_idx
    ON rag_chunk (category_id);
  CREATE INDEX IF NOT EXISTS rag_chunk_metadata_idx
    ON rag_chunk USING gin (metadata);

  INSERT INTO rag_schema_migration (version)
  VALUES (${schemaVersion})
  ON CONFLICT (version) DO NOTHING;
`
