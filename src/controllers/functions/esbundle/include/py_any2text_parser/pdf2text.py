
from .include.pdfpagehelper import pdf_to_pages_as_tables, pil_img_find_tables
from .include.pdftablehelper import create_sparse_dict_of_overall_table_layouts, estimate_tables_and_update_text_data_by_sparse_dict, obtain_filtered_text_data
from .include.pdfunstructuredhelper import partition_pdf, chunk_by_title, elements_to_json, reformat_paged_text_data

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
        # languages=["chi_tra"],
        # model_name="yolox",
    )
    
    
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
    
    
    pdf_bytes = file.read()
    table_layouts_data = pdf_to_pages_as_tables(pdf_bytes, filename, each=pil_img_find_tables, scale=0.75)
    
    
    ##
    ## LOAD text_data
    
    sparse_dict = create_sparse_dict_of_overall_table_layouts(text_data, table_layouts_data)
    
    # export_sparse_dict_representation_as_csv(sparse_dict, filename)
        
    estimate_tables_and_update_text_data_by_sparse_dict(sparse_dict)
    
    filtered_text_data = obtain_filtered_text_data(text_data)

    text = reformat_paged_text_data(
        filtered_text_data, 
        document_file_name = filename,
        document_file_url = "",
        meta_data_mapping = meta_data_mapping,
    )

    return filtered_text_data, text


