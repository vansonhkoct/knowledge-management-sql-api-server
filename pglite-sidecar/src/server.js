import { mkdir, rm, writeFile } from 'node:fs/promises'
import path from 'node:path'
import process from 'node:process'

import { PGlite } from '@electric-sql/pglite'
import { vector } from '@electric-sql/pglite-pgvector'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'

import { schemaSql, schemaVersion } from './schema.js'
import { startRagHttpServer } from './http-server.js'

const dataDir = path.resolve(process.env.PGLITE_DATA_DIR || './var/pglite')
const socketPath = (process.env.PGLITE_SOCKET_PATH || '').trim()
const host = process.env.PGLITE_HOST || '127.0.0.1'
const port = Number.parseInt(process.env.PGLITE_PORT || '5433', 10)
const maxConnections = Number.parseInt(process.env.PGLITE_MAX_CONNECTIONS || '1', 10)
const idleTimeout = Number.parseInt(process.env.PGLITE_IDLE_TIMEOUT_MS || '30000', 10)
const backupDir = path.resolve(process.env.PGLITE_BACKUP_DIR || './var/pglite-backups')
const backupIntervalHours = Number.parseFloat(process.env.PGLITE_BACKUP_INTERVAL_HOURS || '24')
const httpHost = process.env.PGLITE_HTTP_HOST || '127.0.0.1'
const httpPort = Number.parseInt(process.env.PGLITE_HTTP_PORT || '5434', 10)
const socketEnabled = process.env.PGLITE_SOCKET_ENABLED === '1'

await mkdir(path.dirname(dataDir), { recursive: true })
if (socketPath) {
  await mkdir(path.dirname(socketPath), { recursive: true })
  await rm(socketPath, { force: true })
}

const db = await PGlite.create(dataDir, { extensions: { vector } })
await db.exec(schemaSql)

let socketServer = null
if (socketEnabled) {
  socketServer = new PGLiteSocketServer({
    db,
    ...(socketPath ? { path: socketPath } : { host, port }),
    maxConnections,
    idleTimeout,
    debug: process.env.PGLITE_DEBUG === '1',
  })
  await socketServer.start()
}
const httpServer = await startRagHttpServer({ db, host: httpHost, port: httpPort })
console.log(JSON.stringify({
  event: 'pglite_ready',
  httpListener: `${httpHost}:${httpPort}`,
  socketListener: socketEnabled ? (socketPath || `${host}:${port}`) : null,
  dataDir,
  maxConnections,
  schemaVersion,
  pid: process.pid,
}))

let stopping = false
let backupInProgress = false

async function createBackup() {
  if (backupInProgress || stopping) return
  backupInProgress = true
  try {
    await mkdir(backupDir, { recursive: true })
    const timestamp = new Date().toISOString().replaceAll(':', '-').replaceAll('.', '-')
    const target = path.join(backupDir, `pglite-${timestamp}.tar.gz`)
    const dump = await db.dumpDataDir('gzip')
    await writeFile(target, Buffer.from(await dump.arrayBuffer()))
    console.log(JSON.stringify({ event: 'pglite_backup_complete', target }))
  } catch (error) {
    console.error(JSON.stringify({ event: 'pglite_backup_failed', error: String(error) }))
  } finally {
    backupInProgress = false
  }
}

async function shutdown(signal) {
  if (stopping) return
  stopping = true
  console.log(JSON.stringify({ event: 'pglite_shutdown', signal }))
  if (socketServer) await socketServer.stop()
  await new Promise((resolve) => httpServer.close(resolve))
  await db.close()
  if (socketPath) await rm(socketPath, { force: true })
  process.exit(0)
}

process.on('SIGINT', () => void shutdown('SIGINT'))
process.on('SIGTERM', () => void shutdown('SIGTERM'))
process.on('SIGUSR2', () => void createBackup())

if (Number.isFinite(backupIntervalHours) && backupIntervalHours > 0) {
  const timer = setInterval(
    () => void createBackup(),
    backupIntervalHours * 60 * 60 * 1000,
  )
  timer.unref()
}
