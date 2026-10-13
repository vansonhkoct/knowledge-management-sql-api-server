import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite-pgvector'

import { schemaSql } from './schema.js'

const db = await PGlite.create({ extensions: { vector } })
try {
  await db.exec(schemaSql)
  await db.query(
    `INSERT INTO rag_profile (id, model_name, vector_dimension, index_version)
     VALUES ($1, $2, $3, $4)`,
    ['00000000-0000-0000-0000-000000000001', 'smoke', 3, 'smoke-v1'],
  )
  await db.query(
    `INSERT INTO rag_chunk (
       id, party_id, file_id, profile_id, chunk_index,
       content, content_hash, embedding
     ) VALUES ($1, $2, $3, $4, 0, $5, $6, $7::vector)`,
    [
      '00000000-0000-0000-0000-000000000002',
      '00000000-0000-0000-0000-000000000003',
      '00000000-0000-0000-0000-000000000004',
      '00000000-0000-0000-0000-000000000001',
      'smoke test',
      '0000000000000000000000000000000000000000000000000000000000000000',
      '[1,0,0]',
    ],
  )
  const result = await db.query(
    `SELECT content, 1 - (embedding <=> $1::vector) AS score
     FROM rag_chunk
     ORDER BY embedding <=> $1::vector
     LIMIT 1`,
    ['[1,0,0]'],
  )
  if (result.rows[0]?.content !== 'smoke test') {
    throw new Error('pgvector smoke query did not return the inserted chunk')
  }
  console.log('PGlite pgvector smoke test: ok')
} finally {
  await db.close()
}
