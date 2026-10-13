# PGlite RAG sidecar

This process is the single owner of the persistent PGlite data directory. It
loads pgvector, applies the versioned RAG schema, and exposes a narrow private
HTTP API for the API and ingestion worker. Requests are serialized inside the
owner process.

```bash
npm install
npm start
```

The default application listener is `127.0.0.1:5434`, and the default data
directory is `./var/pglite`. It must not be published outside the private API
deployment. A PostgreSQL-wire listener can be enabled for diagnostics with
`PGLITE_SOCKET_ENABLED=1`; its connection limit remains intentionally `1`.

Send `SIGUSR2` to request an owner-consistent backup. A backup is also created
every 24 hours by default under `./var/pglite-backups`. Source files and the
application database must be backed up independently.
