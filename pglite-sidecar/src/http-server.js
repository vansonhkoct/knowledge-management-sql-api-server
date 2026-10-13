import { createServer } from 'node:http'

const maxBodyBytes = 100 * 1024 * 1024

function sendJson(response, status, payload) {
  const body = JSON.stringify(payload)
  response.writeHead(status, {
    'content-type': 'application/json; charset=utf-8',
    'content-length': Buffer.byteLength(body),
  })
  response.end(body)
}

async function readJson(request) {
  const chunks = []
  let size = 0
  for await (const chunk of request) {
    size += chunk.length
    if (size > maxBodyBytes) throw new Error('Request body is too large')
    chunks.push(chunk)
  }
  if (chunks.length === 0) return {}
  return JSON.parse(Buffer.concat(chunks).toString('utf8'))
}

async function ensureProfile(connection, profile) {
  const existing = await connection.query(
    `SELECT model_name, vector_dimension, index_version
     FROM rag_profile WHERE id = $1::uuid`,
    [profile.id],
  )
  if (existing.rows.length === 0) {
    await connection.query(
      `INSERT INTO rag_profile (id, model_name, vector_dimension, index_version)
       VALUES ($1::uuid, $2, $3, $4)`,
      [profile.id, profile.modelName, profile.vectorDimension, profile.indexVersion],
    )
    return
  }

  const current = existing.rows[0]
  if (current.vector_dimension !== profile.vectorDimension) {
    throw new Error(
      `Embedding dimension changed from ${current.vector_dimension} to ${profile.vectorDimension}; ` +
      'configure a new embedding endpoint/profile',
    )
  }
  if (current.index_version !== profile.indexVersion) {
    throw new Error('Index version changed for the active embedding profile; configure a new profile')
  }
}

async function replaceFile(db, body) {
  const { profile, chunks } = body
  if (!profile || !Array.isArray(chunks) || chunks.length === 0) {
    throw new Error('profile and non-empty chunks are required')
  }
  const dimension = chunks[0].embedding?.length || 0
  if (dimension === 0 || chunks.some((chunk) => chunk.embedding?.length !== dimension)) {
    throw new Error('Embedding vectors must have one consistent, non-zero dimension')
  }
  if (chunks.some((chunk) => (
    chunk.party_id !== chunks[0].party_id ||
    chunk.file_id !== chunks[0].file_id ||
    chunk.profile_id !== profile.id
  ))) {
    throw new Error('Every replacement chunk must belong to the same party, file, and profile')
  }
  profile.vectorDimension = dimension

  await db.transaction(async (transaction) => {
    await ensureProfile(transaction, profile)
    await transaction.query(
      'DELETE FROM rag_chunk WHERE party_id = $1::uuid AND file_id = $2::uuid',
      [chunks[0].party_id, chunks[0].file_id],
    )
    for (const chunk of chunks) {
      await transaction.query(
        `INSERT INTO rag_chunk (
           id, party_id, file_id, category_id, profile_id, chunk_index,
           page_number, representation, content, content_hash, metadata, embedding
         ) VALUES (
           $1::uuid, $2::uuid, $3::uuid, $4::uuid, $5::uuid, $6,
           $7, $8, $9, $10, $11::jsonb, $12::vector
         )`,
        [
          chunk.id, chunk.party_id, chunk.file_id, chunk.category_id,
          chunk.profile_id, chunk.chunk_index, chunk.page_number,
          chunk.representation, chunk.content, chunk.content_hash,
          JSON.stringify(chunk.metadata || {}),
          `[${chunk.embedding.map(Number).join(',')}]`,
        ],
      )
    }
  })
  return { inserted: chunks.length }
}

async function search(db, body) {
  const filters = ['party_id = $1::uuid', 'profile_id = $2::uuid']
  const parameters = [body.partyId, body.profileId, `[${body.queryEmbedding.map(Number).join(',')}]`]

  const addValues = (column, values, negate = false) => {
    const comparisons = []
    for (const value of values || []) {
      parameters.push(value)
      comparisons.push(`${column} ${negate ? '<>' : '='} $${parameters.length}::uuid`)
    }
    if (comparisons.length > 0) {
      // Inclusion lists are alternatives; exclusion lists must reject every id.
      filters.push(`(${comparisons.join(negate ? ' AND ' : ' OR ')})`)
    }
  }
  addValues('category_id', body.categoryIds)
  addValues('file_id', body.fileIds)
  addValues('file_id', body.excludeFileIds, true)
  parameters.push(Math.max(1, Math.min(Number(body.limit || 10), 100)))

  const result = await db.query(
    `SELECT id, file_id, category_id, chunk_index, page_number,
            representation, content, metadata,
            1 - (embedding <=> $3::vector) AS score
     FROM rag_chunk
     WHERE ${filters.join(' AND ')}
       AND vector_dims(embedding) = vector_dims($3::vector)
     ORDER BY embedding <=> $3::vector, id
     LIMIT $${parameters.length}`,
    parameters,
  )
  return { items: result.rows }
}

async function route(db, request) {
  const url = new URL(request.url, 'http://localhost')
  if (request.method === 'GET' && url.pathname === '/health') {
    const result = await db.query(
      'SELECT 1 AS ready, max(version) AS schema_version FROM rag_schema_migration',
    )
    return result.rows[0]
  }

  const body = await readJson(request)
  if (request.method === 'POST' && url.pathname === '/v1/files/replace') return await replaceFile(db, body)
  if (request.method === 'POST' && url.pathname === '/v1/search') return await search(db, body)
  if (request.method === 'POST' && url.pathname === '/v1/files/delete') {
    const result = await db.query(
      'DELETE FROM rag_chunk WHERE party_id = $1::uuid AND file_id = $2::uuid',
      [body.partyId, body.fileId],
    )
    return { affected: result.affectedRows || 0 }
  }
  if (request.method === 'POST' && url.pathname === '/v1/files/update-metadata') {
    const result = await db.query(
      `UPDATE rag_chunk
       SET category_id = $3::uuid, metadata = metadata || $4::jsonb
       WHERE party_id = $1::uuid AND file_id = $2::uuid`,
      [body.partyId, body.fileId, body.categoryId, JSON.stringify(body.metadata || {})],
    )
    return { affected: result.affectedRows || 0 }
  }
  if (request.method === 'POST' && url.pathname === '/v1/files/get') {
    const result = await db.query(
      `SELECT id, file_id, category_id, chunk_index, page_number,
              representation, content, metadata
       FROM rag_chunk
       WHERE party_id = $1::uuid AND file_id = $2::uuid
       ORDER BY chunk_index`,
      [body.partyId, body.fileId],
    )
    return { items: result.rows }
  }
  const error = new Error('Not found')
  error.statusCode = 404
  throw error
}

export async function startRagHttpServer({ db, host, port }) {
  let requestQueue = Promise.resolve()
  const server = createServer((request, response) => {
    const execute = async () => {
      try {
        sendJson(response, 200, await route(db, request))
      } catch (error) {
        sendJson(response, error.statusCode || 400, { error: String(error.message || error) })
      }
    }
    requestQueue = requestQueue.then(execute, execute)
  })
  await new Promise((resolve, reject) => {
    server.once('error', reject)
    server.listen(port, host, resolve)
  })
  return server
}
