"""Client-side connectivity tests for the Elasticsearch cluster."""

from __future__ import annotations

import time
import uuid

from elasticsearch import Elasticsearch

from client_tests.test_utils import load_local_env, print_heading, print_kv, require_env


def _new_client() -> Elasticsearch:
    host = require_env("ES_HOST")
    username = require_env("ES_USERNAME")
    password = require_env("ES_PASSWORD")
    print_heading("Connecting to Elasticsearch")
    print_kv("Host", host)
    return Elasticsearch(
        hosts=[host],
        basic_auth=(username, password),
        verify_certs=False,
    )


def _exercise_cluster(es: Elasticsearch) -> None:
    print_heading("Cluster health")
    info = es.info()
    print_kv("Cluster name", info.get("cluster_name"))
    health = es.cluster.health()
    print_kv("Status", health.get("status"))
    print_kv("Active shards", health.get("active_shards"))


def _roundtrip_document(es: Elasticsearch) -> None:
    index_name = f"client-tests-{uuid.uuid4().hex[:8]}"
    print_heading("Indexing round-trip")
    es.options(ignore_status=[400]).indices.create(index=index_name)
    doc = {"message": "client smoke test", "ts": time.time()}
    index_res = es.index(index=index_name, document=doc)
    doc_id = index_res.get("_id")
    fetched = es.get(index=index_name, id=doc_id)
    print_kv("Indexed doc id", doc_id)
    print_kv("Fetched message", fetched["_source"].get("message"))
    es.options(ignore_status=[400, 404]).indices.delete(index=index_name)


def main() -> None:
    load_local_env()
    es = _new_client()
    _exercise_cluster(es)
    _roundtrip_document(es)
    print_heading("Elasticsearch smoke test completed")


if __name__ == "__main__":
    main()
