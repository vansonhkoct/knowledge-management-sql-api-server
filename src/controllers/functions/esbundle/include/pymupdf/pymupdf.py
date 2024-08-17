import pymupdf4llm
import pymupdf
import re
import io

from typing import (
    BinaryIO,
    Optional,
    Union,
)

from tempfile import SpooledTemporaryFile

import asyncio

import unicodedata

def _is_standard_char(char):
    try:
        name = unicodedata.name(char)
        return ord(char) <= 127 or name.startswith("LATIN") or name.startswith("GREEK") or name.startswith("CYRILLIC")
    except (ValueError, TypeError):
        return False

def _containment_proportion_of_non_standard_chars(text):
    total_count = 0
    abnormal_count = 0
    for char in text:
        total_count += 1
        if not _is_standard_char(char):
            abnormal_count += 1

    return abnormal_count / total_count




def extract_pdf_file_to_text(
    filename: str = None,
    file: Optional[Union[BinaryIO, SpooledTemporaryFile]] = None,
    meta_data_mapping = None,
):
    page_content_array = []
    pdf_binary_io = io.BytesIO(file.read())
    doc = pymupdf.Document(stream=pdf_binary_io)
    for index, page in enumerate(doc):
        try:
            md_text = pymupdf4llm.to_markdown(doc=doc, pages=[index], write_images = False)
            md_text = re.sub(r'\*\*', '', md_text)
            if (_containment_proportion_of_non_standard_chars(md_text) > 0.60):
                page_content_array.append("")
            else:
                page_content_array.append(md_text)
        except Exception as e:
            print(e)
            print("Continue....")
            plain_text = page.get_text()
            plain_text = re.sub(r'\*\*', '', plain_text)
            if (_containment_proportion_of_non_standard_chars(plain_text) > 0.60):
                page_content_array.append("")
            else:
                page_content_array.append(plain_text)

    page_content_array, text = _reformat_paged_text_data(
        page_content_array=page_content_array,
        document_file_name=filename,
        meta_data_mapping=meta_data_mapping,
    )
    
    return page_content_array, text


def _reformat_paged_text_data(
    page_content_array = [],
    document_file_name: str = None,
    document_file_url: str = None,
    meta_data_mapping = None,
):
    text = ""

    text += f"<oc_document file_name=\"{document_file_name}\" file_url=\"{document_file_url}\" >"

    if meta_data_mapping is not None:
        for key, value in meta_data_mapping.items():
            text += f"\n<oc_meta key=\"{key}\" value=\"{value}\" />"

    for index, content in enumerate(page_content_array):
        text += f"\n\n\n<oc_page page={index}>{content}</oc_page>\n"

    text += "\n</oc_document>"

    pattern = r"[\u4e00-\u9fff]+\d+\.\s"
    text = re.sub(pattern, "", text)

    pattern = r"[\u4e00-\u9fff]+[\s]+\d+\.\s"
    text = re.sub(pattern, "", text)

    return page_content_array, text



async def async_extract_pdf_file_to_text(
    filename: str = None,
    file: Optional[Union[BinaryIO, SpooledTemporaryFile]] = None,
    meta_data_mapping = None,
):
    def fn():
        page_content_array, text = extract_pdf_file_to_text(
            filename=filename,
            file=file,
            meta_data_mapping=meta_data_mapping,
        )
        return page_content_array, text

    loop = asyncio.get_running_loop()
    page_content_array, text = await loop.run_in_executor(
        None, 
        fn, 
        )
    return page_content_array, text

