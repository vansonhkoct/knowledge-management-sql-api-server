## Prerequisites

```
python3 -m venv ./venv
source venv/bin/activate
pip install -r requirements.txt
```

For development/test tooling use `requirements-dev.txt`. The retired
Elasticsearch fallback is not installed by default; use
`requirements-elasticsearch.txt` only while that fallback is still needed.

The file-ingest queue requires Redis. On macOS with Homebrew:

```bash
brew install redis
brew services start redis
redis-cli ping
```

The last command should print `PONG`. Alternatively, run a local container:

```bash
docker run --name knowledge-management-redis \
  -p 127.0.0.1:6379:6379 -d redis:7-alpine
```

## Local run

```
cp .env.default .env
cd pglite-sidecar
npm ci
npm start
```

Then run the API and file-ingest worker in separate terminals from the
repository root:

```bash
python3 main_uvicorn.py
```

```bash
python3 main_file_ingest_worker.py
```

If Redis is unavailable, the worker waits and reconnects instead of exiting.
Set `REDIS_URL` when Redis is not listening on `localhost:6379`.

`APP_DATABASE_URL` defaults to a disposable local SQLite database for
development. Production must set `APP_ENV=production` and an explicit MySQL
URL. PGlite remains a separate persistent RAG projection in both modes.

See [PGlite operations](docs/PGLITE_OPERATIONS.md) for backup and restore.

## Checks

```bash
pytest -q
cd pglite-sidecar && npm run smoke && npm run smoke:http
```



## Debug

Run/Debug using VSCode (already attached `.vscode/launch.json`)


## New db

```
aerich init -t database.TORTOISE_ORM
aerich init-db
```


## Update db schema

```
aerich migrate
aerich upgrade
```
