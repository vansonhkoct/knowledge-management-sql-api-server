
from .pdfcoordhelper import is_inside, is_inside_by_center_pt_of_elem

# import csv





def try_to_locate_text_data_in_any_table_layout(data, table_layouts_data):
    page_number = data["metadata"]["page_number"] - 1
    page_table_layouts_data = table_layouts_data[page_number]
    # print(page_number)

    # sparse_items = []

    target_item_accurate = None
    target_item_by_center_pt = None
    target_item_loose = None
    
    
    itable = 0
    for table in page_table_layouts_data:
        
        
        irow = 0
        for row in table:
            icol = 0
            for col in row:
                
                if is_inside(
                    data, 
                    col["x1"] * data["metadata"]["coordinates"]["layout_width"] - 20, 
                    col["x2"] * data["metadata"]["coordinates"]["layout_width"] + 20, 
                    col["y1"] * data["metadata"]["coordinates"]["layout_height"] - 20, 
                    col["y2"] * data["metadata"]["coordinates"]["layout_height"] + 20,
                ):
                    target_item_accurate = {
                        "itable": itable,
                        "irow": irow, 
                        "icol": icol, 
                        "text": data["text"],
                        "ref": data,
                        "max_rows": len(table),
                        "max_cols": len(row),
                    }
                    break
                    # print(itable, irow, icol, data["text"])

                if is_inside_by_center_pt_of_elem(
                    data, 
                    col["x1"] * data["metadata"]["coordinates"]["layout_width"] - 20, 
                    col["x2"] * data["metadata"]["coordinates"]["layout_width"] + 20, 
                    col["y1"] * data["metadata"]["coordinates"]["layout_height"] - 20, 
                    col["y2"] * data["metadata"]["coordinates"]["layout_height"] + 20,
                ):
                    target_item_by_center_pt = {
                        "itable": itable,
                        "irow": irow, 
                        "icol": icol, 
                        "text": data["text"],
                        "ref": data,
                        "max_rows": len(table),
                        "max_cols": len(row),
                    }

                if is_inside(
                    data, 
                    col["x1"] * data["metadata"]["coordinates"]["layout_width"] - 100, 
                    col["x2"] * data["metadata"]["coordinates"]["layout_width"] + 100, 
                    col["y1"] * data["metadata"]["coordinates"]["layout_height"] - 100, 
                    col["y2"] * data["metadata"]["coordinates"]["layout_height"] + 100,
                ):
                    target_item_loose = {
                        "itable": itable,
                        "irow": irow, 
                        "icol": icol, 
                        "text": data["text"],
                        "ref": data,
                        "max_rows": len(table),
                        "max_cols": len(row),
                    }
                    

                icol += 1
            irow += 1
        itable += 1

    # return sparse_items
    if target_item_accurate != None:
        return target_item_accurate
        
    if target_item_by_center_pt != None:
        return target_item_by_center_pt
        
    # if target_item_loose != None:
    #     return target_item_loose
    
    # print("FAIL", data["text"], data["metadata"]["coordinates"]["points"])
    return None







# In[ ]:


import pandas as pd
import copy


def create_sparse_dict_of_overall_table_layouts(text_data, table_layouts_data):

    sparse_dict = {}
    
    for data in text_data:
        page_number = data["metadata"]["page_number"] - 1
        cell_data = try_to_locate_text_data_in_any_table_layout(data, table_layouts_data)
    
        if (cell_data != None):
            TK = f"{page_number}_{cell_data['itable']}"
            
            if TK not in sparse_dict:
                sparse_dict[TK] = []
                for i in range(cell_data["max_rows"]):
                    sparse_dict[TK].append([])
                    for j in range(cell_data["max_cols"]):
                        sparse_dict[TK][i].append([])
    
            if sparse_dict[TK][cell_data["irow"]][cell_data["icol"]] == None:
                sparse_dict[TK][cell_data["irow"]][cell_data["icol"]] = []
    
            sparse_dict[TK][cell_data["irow"]][cell_data["icol"]].append(cell_data)

    return sparse_dict


# def export_sparse_dict_representation_as_csv(sparse_dict, filename):

#     sparse_dict_representation = copy.deepcopy(sparse_dict)
    
#     for key in sparse_dict_representation.keys():
#         for i in range(len(sparse_dict_representation[key])):
#             for j in range(len(sparse_dict_representation[key][i])):
#                 sparse_dict_representation[key][i][j] = "\n".join(  
#                     list( map( lambda it: it["text"], sparse_dict_representation[key][i][j] ) ) 
#                 )
    
    
#         data = sparse_dict_representation[key]
    
#         csv_filename = f"./csv_table_mappings/__csv_{filename}_{key}.csv"
        
#         with open(csv_filename, 'w', encoding='utf-8') as f:
#           writer = csv.writer(f)
#           writer.writerows(data)
    
#         df = pd.read_csv(csv_filename)
#         print(f"====== CSV: {csv_filename}")
#         print(df)
#         print(f"====== ")


# In[ ]:


def estimate_tables_and_update_text_data_by_sparse_dict(sparse_dict):

    for key in sparse_dict.keys():
        est_table_data_anchor = None
        est_header_row_data = None
        est_body_rows_data = None
            
        for i in range(len(sparse_dict[key])):
    
            for j in range(len(sparse_dict[key][i])):
    
                data = sparse_dict[key][i][j]
                if data != None:
                    txt = "".join(  
                        list( map( lambda it: it["text"], data ) ) 
                    )
        
                    if txt != None and (txt) != "":
                        if est_header_row_data == None:
                            est_header_row_data = []
    
                            for m in range(len(sparse_dict[key][i])):
            
                                for n in range(len(sparse_dict[key][i][m])):
                                    sparse_dict[key][i][m][n]["ref"]["data_sparse_dict_page_table_ref"] = f"{key}_{i}_{j}"
                                    sparse_dict[key][i][m][n]["ref"]["is_pending_clear_text"] = True
    
                                if (est_table_data_anchor == None):
                                    if (len(sparse_dict[key][i][m]) > 0
                                        and sparse_dict[key][i][m][0] != None
                                        and sparse_dict[key][i][m][0]["ref"] != None):
                                        est_table_data_anchor = sparse_dict[key][i][m][0]["ref"]
                                
                                txt = " ".join(  
                                    list( map( lambda it: it["text"], sparse_dict[key][i][m] ) ) 
                                )
                                est_header_row_data.append(txt)
    
                            break
        
                        else:
                            if est_body_rows_data == None:
                                est_body_rows_data = []
    
                            row_items = []
                            for m in range(len(sparse_dict[key][i])):
    
                                for n in range(len(sparse_dict[key][i][m])):
                                    sparse_dict[key][i][m][n]["ref"]["data_sparse_dict_page_table_ref"] = f"{key}_{i}_{j}"
                                    sparse_dict[key][i][m][n]["ref"]["is_pending_clear_text"] = True
                                
                                txt = " ".join(  
                                    list( map( lambda it: it["text"], sparse_dict[key][i][m] ) ) 
                                )
                                row_items.append(txt)
    
        
                            est_body_rows_data.append(row_items)
                            break
    
        # print(est_header_row_data)
        # print(est_body_rows_data)
        est_table_data_anchor["original_text"] = est_table_data_anchor["text"]
        est_table_data_anchor["text"] = ""
        est_table_data_anchor["is_pending_clear_text"] = False
        est_table_data_anchor["is_data_sparse_dict_page_table_anchor"] = True
    
        summary_text = []
    
        if est_header_row_data != None:
            if est_body_rows_data == None:
                summary_text.append( ", ".join(
                    list( filter( lambda it: len(it.strip()) > 0, est_header_row_data ) )
                ) )
            else:
                header_partial = ", ".join(
                    list( filter( lambda it: len(it.strip()) > 0, est_header_row_data ) )
                )
                summary_text.append(f"\n以下是一個列表：\n")
    
                for i in range(len(est_body_rows_data)):
                    row = est_body_rows_data[i]
                    body_head = f"\n - 項目 {i}: \n"
                    body_partial_items = []
                    
                    for m in range(len(row)):
                        celltext = row[m]
                        if len(celltext.strip()) > 0:
                            body_partial_items.append(f"     - {est_header_row_data[m]}: {celltext}\n")
                    
                    body_partial = "\n".join(body_partial_items)
                    summary_text.append(f"{body_head}{body_partial};\n")
    
        
                
        # page_text_data = list(filter(partial(is_in_page_number, page_number=2), text_data))
    
        
        est_table_data_anchor["text"] = "\n".join(summary_text)
        
        # print("\n".join(summary_text))
        # print("")
        # print(est_table_data_anchor)
        # print("")
        # print("")
        # print("")



def obtain_filtered_text_data(text_data):        
    filtered_text_data = list( filter( lambda it: "is_pending_clear_text" not in it or not it["is_pending_clear_text"], text_data ))
    return filtered_text_data

