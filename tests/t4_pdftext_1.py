
from include.pdfpagehelper import pdf_to_pages_as_tables, pil_img_find_tables
from include.pdftablehelper import create_sparse_dict_of_overall_table_layouts, estimate_tables_and_update_text_data_by_sparse_dict, obtain_filtered_text_data
from include.pdfunstructuredhelper import partition_pdf, chunk_by_title, elements_to_json, reformat_paged_text_data

from typing import (
    IO,
    TYPE_CHECKING,
    Any,
    BinaryIO,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
    cast,
)

from tempfile import SpooledTemporaryFile
import json

import asyncio




def extract_pdf_file_to_text(
    filename: str = None,
    file: Optional[Union[BinaryIO, SpooledTemporaryFile]] = None,
    meta_data_mapping = None,
):
    elements = partition_pdf(
        file=file, 
        # strategy="hi_res", 
        strategy="fast", 
        # infer_table_structure=True, 
        # ocr_languages=,  # changing to optional for deprecation
        languages=["chi_tra"],
        model_name="yolox",
    )
    
    # print(elements)
    # return
    
    c_elements = chunk_by_title(
        elements,
        combine_text_under_n_chars=25,
        new_after_n_chars=100,
        multipage_sections=True,
    )
    
    
    jsondump_data = elements_to_json(
        elements,
    )
    
    text_data = json.loads(jsondump_data)
    
    print(json.dumps(text_data, ensure_ascii=False, separators=(',', ':')))
    
    

import io

import os
os.environ["OCR_AGENT"] = "unstructured.partition.utils.ocr_models.paddle_ocr.OCRAgentPaddle"
os.environ["DEFAULT_PADDLE_LANG"] = "ch"

with open("./tests/665b3f9fac7044122d9b3d98_EDBCM24035C.pdf", "rb") as pdf_file:
    pdf_binary_io = io.BytesIO(pdf_file.read())
    extract_pdf_file_to_text(file=pdf_binary_io)
    