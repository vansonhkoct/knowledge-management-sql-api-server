import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite-pgvector'

import { startRagHttpServer } from './http-server.js'
import { schemaSql } from './schema.js'

const db = await PGlite.create({ extensions: { vector } })
let server

const partyId = '10000000-0000-0000-0000-000000000001'
const profileId = '20000000-0000-0000-0000-000000000001'
const categoryIds = [
  '30000000-0000-0000-0000-000000000001',
  '30000000-0000-0000-0000-000000000002',
]
const fileIds = [
  '40000000-0000-0000-0000-000000000001',
  '40000000-0000-0000-0000-000000000002',
]

async function post(baseUrl, path, body) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(body),
  })
  const result = await response.json()
  if (!response.ok) throw new Error(result.error || `HTTP ${response.status}`)
  return result
}

try {
  await db.exec(schemaSql)
  server = await startRagHttpServer({ db, host: '127.0.0.1', port: 0 })
  const address = server.address()
  const baseUrl = `http://127.0.0.1:${address.port}`

  for (let index = 0; index < 2; index += 1) {
    await post(baseUrl, '/v1/files/replace', {
      profile: { id: profileId, modelName: 'smoke', indexVersion: 'pdf-v1' },
      chunks: [{
        id: `50000000-0000-0000-0000-00000000000${index + 1}`,
        party_id: partyId,
        file_id: fileIds[index],
        category_id: categoryIds[index],
        profile_id: profileId,
        chunk_index: 0,
        page_number: 1,
        representation: 'CHUNK',
        content: `document ${index + 1}`,
        content_hash: `${index + 1}`.repeat(64),
        metadata: { page: 1 },
        embedding: [1, index, 0],
      }],
    })
  }

  const included = await post(baseUrl, '/v1/search', {
    partyId,
    profileId,
    queryEmbedding: [1, 0, 0],
    categoryIds,
    limit: 10,
  })
  if (new Set(included.items.map((item) => item.file_id)).size !== 2) {
    throw new Error('Multi-category inclusion did not return both files')
  }

  const excluded = await post(baseUrl, '/v1/search', {
    partyId,
    profileId,
    queryEmbedding: [1, 0, 0],
    categoryIds,
    excludeFileIds: [fileIds[0]],
    limit: 10,
  })
  if (excluded.items.length !== 1 || excluded.items[0].file_id !== fileIds[1]) {
    throw new Error('File exclusion returned an unexpected result')
  }

  console.log('PGlite HTTP multi-filter smoke test: ok')
} finally {
  if (server) await new Promise((resolve) => server.close(resolve))
  await db.close()
}
