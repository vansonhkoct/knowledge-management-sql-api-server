import { readFile, readdir } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite-pgvector'

import { schemaSql } from './schema.js'

const backupPath = process.env.PGLITE_RESTORE_BACKUP
const targetDir = process.env.PGLITE_RESTORE_TARGET
if (!backupPath || !targetDir) {
  throw new Error('PGLITE_RESTORE_BACKUP and PGLITE_RESTORE_TARGET are required')
}

try {
  const entries = await readdir(targetDir)
  if (entries.length > 0) throw new Error('PGLITE_RESTORE_TARGET must be empty or absent')
} catch (error) {
  if (error.code !== 'ENOENT') throw error
}

const bytes = await readFile(path.resolve(backupPath))
const dump = new File([bytes], path.basename(backupPath), { type: 'application/gzip' })
const db = await PGlite.create(path.resolve(targetDir), {
  extensions: { vector },
  loadDataDir: dump,
})
try {
  await db.exec(schemaSql)
  const result = await db.query('SELECT count(*)::integer AS chunk_count FROM rag_chunk')
  console.log(JSON.stringify({
    event: 'pglite_restore_complete',
    targetDir: path.resolve(targetDir),
    chunkCount: result.rows[0].chunk_count,
  }))
} finally {
  await db.close()
}
