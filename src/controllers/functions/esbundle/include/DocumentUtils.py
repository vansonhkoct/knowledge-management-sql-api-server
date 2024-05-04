
from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter

from .py_any2text_parser.pdf2text import extract_pdf_file_to_text

from datetime import datetime

import re

from pathlib import Path


class DocumentUtils:

    @staticmethod
    def pdf_to_text_file(pdf_filepath, meta_data_mapping = None):
        # return ""
        text_data, text = extract_pdf_file_to_text(
            pdf_filepath, 
            meta_data_mapping = meta_data_mapping,
        )

        path = Path(pdf_filepath)
        filename = path.stem
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        txt_filepath = f"output_txts/txt_{filename}_{timestamp}.txt"

        
        regex = r'([\u4e00-\u9fff])[ ]([\u4e00-\u9fff])'

        updated_text = re.sub(regex, r'\1\2', text)
        updated_text = re.sub(regex, r'\1\2', updated_text)

        
        with open(txt_filepath, "w", encoding='utf-8') as f:
            f.write(updated_text)

        return text_data, text, txt_filepath

    
    @staticmethod
    def load_file(filepath, chunk_size, chunk_overlap):
        loader = TextLoader(filepath, encoding='utf-8')
        documents = loader.load()
        text_splitter = CharacterTextSplitter(separator='\n', chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        docs = text_splitter.split_documents(documents)
        return docs

    
    @staticmethod
    def load_oc_text_file(filepath, chunk_size=300, chunk_overlap=10, use_text_splitter=True):               
        # loader = TextLoader(filepath, encoding='utf-8')
        # documents = loader.load()
        documents = parse_oc_text_filepath_to_documents(filepath)
        if (use_text_splitter):
            text_splitter = CharacterTextSplitter(separator='\n', chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            docs = text_splitter.split_documents(documents)
        else:
            docs = documents
        return docs



    @staticmethod
    def parse_text(text_data, text):

        regex = r'([\u4e00-\u9fff])[ ]([\u4e00-\u9fff])'

        updated_text = re.sub(regex, r'\1\2', text)
        updated_text = re.sub(regex, r'\1\2', updated_text)

        return text_data, updated_text

    
    
    @staticmethod
    def load_oc_text(text, chunk_size=300, chunk_overlap=10, use_text_splitter=True):               
        # loader = TextLoader(filepath, encoding='utf-8')
        # documents = loader.load()
        documents = parse_oc_text_to_documents(text)
        if (use_text_splitter):
            text_splitter = CharacterTextSplitter(separator='\n', chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            docs = text_splitter.split_documents(documents)
        else:
            docs = documents
        return docs





from bs4 import BeautifulSoup



def parse_oc_text_to_documents(
    content,
):
    
    documents = []

    # 原始 HTML 程式碼
    html_doc = content
    
    # 以 Beautiful Soup 解析 HTML 程式碼
    soup = BeautifulSoup(html_doc, 'html.parser')
    
    # 輸出排版後的 HTML 程式碼
    # print(soup.prettify())
    
    document = soup.find('oc_document')
    document_file_name = document.attrs["file_name"]
    document_file_url = document.attrs["file_url"]
    metas = soup.find_all('oc_meta')
    headers = soup.find_all('oc_header')
    pages = soup.find_all('oc_page')
    
    # print(document_file_name)
    # print(document_file_url)
    
    # print(document.attrs)
    
    for meta in metas:
        # print(meta.attrs)
        pass
    
    for page in pages:
        # print(page.attrs)
        pass
    
    for header in headers:
        # print(header.get_text().strip())
    
        metadata = {
            "document_file_name": document_file_name,
            "document_file_url": document_file_url,
        }
    
        for meta in metas:
            metakey = meta.attrs["key"]
            metavalue = meta.attrs["value"]
            metadata[metakey] = metavalue
    
        metadata["page"] = 0
        
        documents.append(
            Document(
                page_content = header.get_text().strip(),
                metadata = metadata,
            )
        )
    
    for page in pages:
        # print(page.get_text().strip())
    
        metadata = {
            "document_file_name": document_file_name,
            "document_file_url": document_file_url,
        }
    
        for meta in metas:
            metakey = meta.attrs["key"]
            metavalue = meta.attrs["value"]
            metadata[metakey] = metavalue
    
        metadata["page"] = page.attrs["page"]
        
        documents.append(
            Document(
                page_content = page.get_text().strip(),
                metadata = metadata,
            )
        )
    
      # documents.append(Document(
      #   page_content = page_text,
      #   metadata = {
      #       "source": filepath,
      #   }
      # ))
    
    
    return documents




def parse_oc_text_filepath_to_documents(
    oc_text_filepath,
):

    file = open(oc_text_filepath, "r", encoding='utf-8')
    content = file.read()
    # print(content)
    file.close()

    return parse_oc_text_to_documents(content=content)


