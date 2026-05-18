"""Convenience entry-point that runs both client smoke tests."""

import asyncio

from client_tests import test_elasticsearch_connection, test_llm_api


def main() -> None:
    test_elasticsearch_connection.main()
    asyncio.run(test_llm_api.main())


if __name__ == "__main__":
    main()
