
import io

import cv2.ximgproc
from pdf2image import convert_from_path, convert_from_bytes

from pdf2image.exceptions import (
    PDFInfoNotInstalledError,
    PDFPageCountError,
    PDFSyntaxError
)

from img2table.document import Image

import cv2
import numpy as np

import json



def pdf_to_pages_as_tables(input_pdf_bytes, name, each, scale=0.75):
    pdf_page_tables = []
    pdf_images = convert_from_bytes(input_pdf_bytes)
    n_pages = len(pdf_images)
    
    for page_number in range(n_pages):
        pil_image = pdf_images[page_number]

        # output_img_tables = each(name, page_number, pil_image)
        output_img_tables = each(pil_image)

        width, height = pil_image.size
        output_tables = []

        # Result of table identification
        for table in output_img_tables:
            new_table = []
            
            for id_row, row in enumerate(table.content.values()):
                # print(f"{id_row}")
                new_row = []
                
                for id_col, cell in enumerate(row):
                    new_col = {
                        "x1": cell.bbox.x1 / width,
                        "y1": cell.bbox.y1 / height,
                        "x2": cell.bbox.x2 / width,
                        "y2": cell.bbox.y2 / height,
                    }

                    new_row.append(new_col)
                    
                new_table.append(new_row)

            output_tables.append(new_table)
            
        pdf_page_tables.append(output_tables)

    return pdf_page_tables




def pil_img_find_tables(pil_image):

    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_byte_arr = img_byte_arr.getvalue()
    cv_img = cv2.imdecode(np.frombuffer(img_byte_arr, np.uint8), cv2.IMREAD_COLOR)

    _, img_byte_array = cv2.imencode('.png', cv_img)
    img = Image(img_byte_arr)


    # Table identification
    img_tables = img.extract_tables()
    
    # Result of table identification
    for table in img_tables:
    
        for id_row, row in enumerate(table.content.values()):
            # print(f"{id_row}")
            for id_col, cell in enumerate(row):
                x1 = cell.bbox.x1
                y1 = cell.bbox.y1
                x2 = cell.bbox.x2
                y2 = cell.bbox.y2
                value = cell.value
                # print(f"{id_col} {x1}, {y1}, {x2}, {y2},     {value}")
        
                # Draw lines for each cell
                cv2.line(cv_img, (x1, y1), (x1, y2), (0,255,0), thickness=2)
                cv2.line(cv_img, (x1, y2), (x2, y2), (0,255,0), thickness=2)
                cv2.line(cv_img, (x2, y2), (x2, y1), (0,255,0), thickness=2)
                cv2.line(cv_img, (x2, y1), (x1, y1), (0,255,0), thickness=2)

                

    # cv2.imwrite(f'./screenshots/{name}-{page_number}-image.png', cv_img) 


    return img_tables



