

from unstructured.chunking.title import chunk_by_title
from unstructured.documents.elements import DataSourceMetadata
from unstructured.partition.json import partition_json
from sentence_transformers import SentenceTransformer
from unstructured.partition.pdf import partition_pdf
from unstructured.staging.base import elements_to_json
from unstructured.partition.auto import partition
from unstructured.partition.html import partition_html

from .pdfcoordhelper import compare_page_numbers_and_coords, filter_empty_text, is_intersecting, calc_distances, is_footer_page_number

import functools
import re



def reformat_text_data(text_data):
    text_data.sort(key=functools.cmp_to_key(compare_page_numbers_and_coords))
    text_data = filter_empty_text(text_data)
    
    text = ""
    for i in range(len(text_data)):
        elem = text_data[i]
        elem_text = elem['text']
        
        connector = """
    
    
    
    
"""
    
        if (i > 0):
            prev_elem = text_data[i - 1]
            next_elem = None
            
            if len(text_data) > i + 1:
                next_elem = text_data[i + 1]
    
            is_valid_is_intersecting = False
            is_valid_is_aligned_horizontally = False
            is_valid_is_aligned_vertically = False
            is_valid_is_just_nearby = False
            is_valid_is_just_below_prev = False
            is_valid_is_just_adjacent_to_prev = False
            is_valid_is_footer_page_number = False
    
            if (is_intersecting(elem, prev_elem)):
                is_valid_is_intersecting = True
    
            if (calc_distances(elem, prev_elem)['x'] < 20
                 and calc_distances(elem, prev_elem)['y'] < 20):
                is_valid_is_just_nearby = True
    
            if (is_intersecting(elem, prev_elem, only_vertically=True)
                and calc_distances(elem, prev_elem)['x'] < 30):
                is_valid_is_just_adjacent_to_prev = True
    
            if (is_intersecting(elem, prev_elem, only_horizontally=True)
                and calc_distances(elem, prev_elem)['y'] < 20):
                is_valid_is_just_below_prev = True
    
            if (is_intersecting(elem, prev_elem, only_vertically=True)):
                is_valid_is_aligned_horizontally = True
    
            if (is_intersecting(elem, prev_elem, only_horizontally=True)):
                is_valid_is_aligned_vertically = True
    
            if (
                next_elem != None
                and
                is_footer_page_number(elem) 
               ):            
                is_valid_is_footer_page_number = True
            

            if (is_valid_is_footer_page_number):
                elem['text'] = f" {next_elem['text']} "
                connector = " "
                
            elif (is_valid_is_intersecting):
                connector = " "
    
            elif (is_valid_is_just_below_prev):
                connector = " "
    
            elif (is_valid_is_just_adjacent_to_prev):
                connector = ", "
            
            elif (is_valid_is_aligned_horizontally):
                connector = """
"""
    
            elif (is_valid_is_aligned_vertically):
                connector = """
    
    
"""

    
            dict = {
                "is_valid_is_intersecting": is_valid_is_intersecting,
                "is_valid_is_aligned_horizontally": is_valid_is_aligned_horizontally,
                "is_valid_is_aligned_vertically": is_valid_is_aligned_vertically,
                "is_valid_is_just_nearby": is_valid_is_just_nearby,
                "is_valid_is_just_below_prev": is_valid_is_just_below_prev,
                "is_valid_is_just_adjacent_to_prev": is_valid_is_just_adjacent_to_prev,
                "is_valid_is_footer_page_number": is_valid_is_footer_page_number,
            }
            
            print(f"{i}: {dict}, connector={connector} text={elem['text']}")
        
        elem['connector'] = connector
    
    
    
    for i in range(len(text_data)):
        elem = text_data[i]
        print(f"{i}: elem: RECT={elem['metadata']['coordinates']['points'][0][0]}, {elem['metadata']['coordinates']['points'][0][1]} -- {elem['metadata']['coordinates']['points'][2][0]}, {elem['metadata']['coordinates']['points'][2][1]}, text={elem['text']}")
    
    
    text = ""
    for elem in text_data:
        # print(elem['connector'] + elem['text'])
        text += elem['connector'] + elem['text']
    

    pattern = r"[\u4e00-\u9fff]+\d+\.\s"
    text = re.sub(pattern, "", text)

    pattern = r"[\u4e00-\u9fff]+[\s]+\d+\.\s"
    text = re.sub(pattern, "", text)

    
    return text










def reformat_paged_text_data(
    text_data, 
    document_file_name = "",
    document_file_url = "",
    meta_data_mapping = None,
):
    text_data.sort(key=functools.cmp_to_key(compare_page_numbers_and_coords))
    text_data = filter_empty_text(text_data)
    
    text = ""

    is_first_page = True
    
    elem_page_number = -1
    
    for i in range(len(text_data)):
        elem = text_data[i]
        elem_text = elem['text']
        new_elem_page_number = elem['metadata']['page_number']

        is_new_page = False
        connector_is_close_sentence = False
        connector = """
    
    
    
    
"""
    
        if (i > 0):
            prev_elem = text_data[i - 1]
            next_elem = None
            
            if len(text_data) > i + 1:
                next_elem = text_data[i + 1]
    
            is_valid_is_intersecting = False
            is_valid_is_aligned_horizontally = False
            is_valid_is_aligned_vertically = False
            is_valid_is_just_nearby = False
            is_valid_is_just_below_prev = False
            is_valid_is_just_adjacent_to_prev = False
            is_valid_is_footer_page_number = False

            if (is_intersecting(elem, prev_elem)):
                is_valid_is_intersecting = True
    
            if (calc_distances(elem, prev_elem)['x'] < 20
                 and calc_distances(elem, prev_elem)['y'] < 20):
                is_valid_is_just_nearby = True
    
            if (is_intersecting(elem, prev_elem, only_vertically=True)
                and calc_distances(elem, prev_elem)['x'] < 30):
                is_valid_is_just_adjacent_to_prev = True
    
            if (is_intersecting(elem, prev_elem, only_horizontally=True)
                and calc_distances(elem, prev_elem)['y'] < 20):
                is_valid_is_just_below_prev = True
    
            if (is_intersecting(elem, prev_elem, only_vertically=True)):
                is_valid_is_aligned_horizontally = True
    
            if (is_intersecting(elem, prev_elem, only_horizontally=True)):
                is_valid_is_aligned_vertically = True
    
            if (
                next_elem != None
                and
                is_footer_page_number(elem) 
               ):            
                is_valid_is_footer_page_number = True
            

            if (is_valid_is_footer_page_number):
                elem['text'] = f" {next_elem['text']} "
                connector = " "
    
            elif (is_valid_is_intersecting):
                connector_is_close_sentence = True
                connector = " "
    
            elif (is_valid_is_just_below_prev):
                connector_is_close_sentence = True
                connector = " "
    
            elif (is_valid_is_just_adjacent_to_prev):
                connector_is_close_sentence = True
                connector = ", "
            
            elif (is_valid_is_aligned_horizontally):
                connector_is_close_sentence = False
                connector = """
"""
    
            elif (is_valid_is_aligned_vertically):
                connector_is_close_sentence = False
                connector = """
    
    
"""

            if not connector_is_close_sentence:
                is_new_page = (new_elem_page_number != elem_page_number)
                elem_page_number = new_elem_page_number
            else:
                is_new_page = False
            
            
            dict = {
                "is_valid_is_intersecting": is_valid_is_intersecting,
                "is_valid_is_aligned_horizontally": is_valid_is_aligned_horizontally,
                "is_valid_is_aligned_vertically": is_valid_is_aligned_vertically,
                "is_valid_is_just_nearby": is_valid_is_just_nearby,
                "is_valid_is_just_below_prev": is_valid_is_just_below_prev,
                "is_valid_is_just_adjacent_to_prev": is_valid_is_just_adjacent_to_prev,
                "is_valid_is_footer_page_number": is_valid_is_footer_page_number,
                "connector_is_close_sentence": connector_is_close_sentence,
                "elem_page_number": elem_page_number,
                "is_new_page": is_new_page,
            }
            
            # print(f"{i}: {dict}, connector={connector} text={elem['text']}")
        
        elem['connector'] = connector
        elem['elem_page_number'] = elem_page_number
        elem['is_new_page'] = is_new_page
    
    
    
    for i in range(len(text_data)):
        elem = text_data[i]
        # print(f"{i}: elem: RECT={elem['metadata']['coordinates']['points'][0][0]}, {elem['metadata']['coordinates']['points'][0][1]} -- {elem['metadata']['coordinates']['points'][2][0]}, {elem['metadata']['coordinates']['points'][2][1]}, text={elem['text']}")
    
    
    text = ""

    text += f"<oc_document file_name=\"{document_file_name}\" file_url=\"{document_file_url}\" >"



    if meta_data_mapping != None:
        for key, value in meta_data_mapping.items():
            text += f"\n<oc_meta key=\"{key}\" value=\"{value}\" />"

    
    text += f"\n\n\n<oc_header>\n"
    
    for elem in text_data:
        # print(elem['connector'] + elem['text'])

        if elem['is_new_page']:
            if is_first_page:
                is_first_page = False
                text += f"\n\n\n</oc_header>\n"
                text += f"\n\n\n<oc_page page={elem['elem_page_number']} >\n\n\n"
            else:
                text += f"\n\n\n</oc_page>\n"
                text += f"\n\n\n<oc_page page={elem['elem_page_number']} >\n\n\n"
        
        text += elem['connector'] + elem['text']

    if is_first_page:
        is_first_page = False
        text += f"\n\n\n</oc_header>\n"
    else:
        text += f"\n\n\n</oc_page>\n"

    
    text += f"\n\n\n</oc_document>"

    

    pattern = r"[\u4e00-\u9fff]+\d+\.\s"
    text = re.sub(pattern, "", text)

    pattern = r"[\u4e00-\u9fff]+[\s]+\d+\.\s"
    text = re.sub(pattern, "", text)

    
    return text






