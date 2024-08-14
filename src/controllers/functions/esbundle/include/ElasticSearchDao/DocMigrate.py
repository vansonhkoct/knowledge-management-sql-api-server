

from elasticsearch import Elasticsearch
from . import _constants
from .. import ConfigParams

def doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
    es_client: Elasticsearch,
    index_name: str, 
):
    ConfigParams.es_dbg("doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk -> source", f"\n{source}\n")
    
    return es_client.update_by_query(
        index=f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{str(index_name)}",
        refresh=True,
        body={
          "query": {
              "bool": {
                  "must_not": [
                      {
                          "exists": {
                              "field": "metadata.data_strategy"
                          }
                      }
                  ]
              }
          },
          "script": {
            "params": {
                "data_strategy": _constants.DATA_STRATEGY_1,
                "data_portion_type": _constants.DATA_PORTION_TYPE_CHUNK,
            },
            "lang": "painless",
            "source": " ctx._source.metadata.data_strategy = params.data_strategy; \n ctx._source.metadata.data_portion_type = params.data_portion_type; "
          },
        }
    )

