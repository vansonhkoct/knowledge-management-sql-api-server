# PGlite operations

The Node sidecar is the only process allowed to open `PGLITE_DATA_DIR`. The
FastAPI process and ingestion worker use `PGLITE_SERVICE_URL`, which must remain
on a private loopback/container network.

## Start and verify

```bash
cd pglite-sidecar
npm ci
npm start
curl --fail http://127.0.0.1:5434/health
```

The process logs `pglite_ready` only after pgvector and the RAG schema are
available. The application health endpoint also reports `pglite.ready`.

## Backup

The owner creates a compressed data-directory dump every 24 hours by default.
Send `SIGUSR2` to request one immediately. Backups are written to
`PGLITE_BACKUP_DIR`; copy them to encrypted backup storage using deployment
automation. Do not copy the live data directory.

## Restore drill

1. Stop the sidecar that owns the source/target data directory.
2. Select a verified backup and a new, empty target directory.
3. Restore without overwriting the current directory:

```bash
PGLITE_RESTORE_BACKUP=/backups/pglite-...tar.gz \
PGLITE_RESTORE_TARGET=/var/lib/km-pglite-restored \
npm run restore
```

4. Start a sidecar against the restored directory on a separate private port.
5. Check `/health`, the logged chunk count, and representative tenant-filtered
   searches before changing deployment configuration.

Keep application-database and upload-directory backups separate. If PGlite
cannot be restored, reset affected file index states to `NOT_INDEXED`; admins
can select and enqueue their source PDFs again.
