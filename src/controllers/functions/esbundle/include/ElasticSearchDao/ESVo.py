
from . import _constants

class ESVoDocSearch:
    index_name: str
    question: str | None
    query_strings: dict | None
    query_vectors: dict | None
    knn_boosts: dict | None = None 
    document_category: str | None = None 
    k: int = 10
    num_candidates: int = 100
    data_strategy: str = None
    data_portion_type: str = _constants.DATA_PORTION_PAGE
    must_match_document_category: bool = True
    should_match_document_tags: int = 0
    should_match_document_title: int = 0
    should_match_document_summary: int = 0
    should_match_document_text: int = 0
    
    def __init__(
        self,
        index_name: str,
        question: str | None,
        query_strings: dict | None,
        query_vectors: dict | None,
        knn_boosts: dict | None = None,
        document_category: str | None = None,
        k: int = 10,
        num_candidates: int = 100,
        data_strategy: str = None,
        data_portion_type: str = _constants.DATA_PORTION_PAGE,
        must_match_document_category: bool = True,
        should_match_document_tags: int = 0,
        should_match_document_title: int = 0,
        should_match_document_summary: int = 0,
        should_match_document_text: int = 0,
        ):
            self.index_name = index_name
            self.question = question
            self.query_strings = query_strings
            self.query_vectors = query_vectors
            self.knn_boosts = knn_boosts
            self.document_category = document_category
            self.k = k
            self.num_candidates = num_candidates
            self.data_strategy = data_strategy
            self.data_portion_type = data_portion_type
            self.must_match_document_category = must_match_document_category
            self.should_match_document_tags = should_match_document_tags
            self.should_match_document_title = should_match_document_title
            self.should_match_document_summary = should_match_document_summary
            self.should_match_document_text = should_match_document_text

    def is_search_strategy_2(self):
        return (self.data_strategy == "2")

    def is_search_portion_type_page(self):
        return (self.portion_type == _constants.DATA_PORTION_PAGE)

    def is_search_portion_type_chunk(self):
        return (self.portion_type == _constants.DATA_PORTION_CHUNK)

    def is_search_portion_type_none(self):
        return (
            not self.is_search_portion_type_page()
            and not self.is_search_portion_type_chunk()
        )




class ESVoDocInsert:
    index_name: str
    text_data: dict
    text: str
    chunk_size: int = 500
    chunk_overlap: int = 10
    extra_metadata: dict | None = None
    is_testrun: bool = False
    
    def __init__(
        self,
        index_name: str,
        text_data: dict,
        text: str,
        chunk_size: int = 500,
        chunk_overlap: int = 10,
        extra_metadata: dict | None = None,
        is_testrun: bool = False,
        ):
            self.index_name = index_name
            self.text_data = text_data
            self.text = text
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.extra_metadata = extra_metadata
            self.is_testrun = is_testrun