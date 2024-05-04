
def compare_page_numbers_and_coords(elem1, elem2):
  if elem1['metadata']['page_number'] < elem2['metadata']['page_number']:
    return -1
  elif elem1['metadata']['page_number'] > elem2['metadata']['page_number']:
    return 1

  if elem1['metadata']['coordinates']['points'][0][1] < elem2['metadata']['coordinates']['points'][0][1]:
    return -1
  elif elem1['metadata']['coordinates']['points'][0][1] > elem2['metadata']['coordinates']['points'][0][1]:  
    return 1
  else:
    if elem1['metadata']['coordinates']['points'][0][0] < elem2['metadata']['coordinates']['points'][0][0]:
      return -1
    else: 
      return 1


def replace_text(data, text_to_replace, replacement_text):
  for item in data:
    if item['text'] == text_to_replace:  
      item['text'] = replacement_text



import math

def is_intersecting(elem1, elem2, only_horizontally=False, only_vertically=False, ):

  x1min = elem1['metadata']['coordinates']['points'][0][0] 
  x1max = elem1['metadata']['coordinates']['points'][2][0]

  y1min = elem1['metadata']['coordinates']['points'][0][1]
  y1max = elem1['metadata']['coordinates']['points'][1][1]

  x2min = elem2['metadata']['coordinates']['points'][0][0]
  x2max = elem2['metadata']['coordinates']['points'][2][0]

  y2min = elem2['metadata']['coordinates']['points'][0][1] 
  y2max = elem2['metadata']['coordinates']['points'][1][1]

  if x1max < x2min or x1min > x2max:
      if not only_vertically:
        return False

  if y1max < y2min or y1min > y2max:
      if not only_horizontally:
        return False

  return True


def is_inside(elem_inner, x2min, x2max, y2min, y2max):

  x1min = elem_inner['metadata']['coordinates']['points'][0][0] 
  x1max = elem_inner['metadata']['coordinates']['points'][2][0]

  y1min = elem_inner['metadata']['coordinates']['points'][0][1]
  y1max = elem_inner['metadata']['coordinates']['points'][1][1]

  if x1min >= x2min and x1max <= x2max:
    if y1min >= y2min and y1max <= y2max:
      return True
    
  return False


def is_inside_by_center_pt_of_elem(elem_inner, x2min, x2max, y2min, y2max):

  x1min = elem_inner['metadata']['coordinates']['points'][0][0] 
  x1max = elem_inner['metadata']['coordinates']['points'][2][0]

  y1min = elem_inner['metadata']['coordinates']['points'][0][1]
  y1max = elem_inner['metadata']['coordinates']['points'][1][1]

  x1center = (x1min + x1max) / 2
  y1center = (y1min + y1max) / 2

  if x1center >= x2min and x1center <= x2max:
    if y1center >= y2min and y1center <= y2max:
      return True
    
  return False


def is_footer_page_number(elem):
  xmin = elem['metadata']['coordinates']['points'][0][0]
  xmax = elem['metadata']['coordinates']['points'][2][0]

  ymin = elem['metadata']['coordinates']['points'][0][1] 
  ymax = elem['metadata']['coordinates']['points'][1][1]

  page_number = elem['metadata']['page_number']
    
  # xmin_prev = elem_prev['metadata']['coordinates']['points'][0][0]
  # xmax_prev = elem_prev['metadata']['coordinates']['points'][2][0]

  # ymin_prev = elem_prev['metadata']['coordinates']['points'][0][1] 
  # ymax_prev = elem_prev['metadata']['coordinates']['points'][1][1]

  # page_number_prev = elem['metadata']['page_number_prev']

  page_width = elem['metadata']['coordinates']['layout_width']
  page_height = elem['metadata']['coordinates']['layout_height']

  if xmax - xmin <= 30:
      if page_height - ymin < 80:
          return True

  return False


def calc_distances(elem1, elem2):

  x1min = elem1['metadata']['coordinates']['points'][0][0]
  x1max = elem1['metadata']['coordinates']['points'][2][0]

  y1min = elem1['metadata']['coordinates']['points'][0][1] 
  y1max = elem1['metadata']['coordinates']['points'][1][1]

  x2min = elem2['metadata']['coordinates']['points'][0][0]
  x2max = elem2['metadata']['coordinates']['points'][2][0]

  y2min = elem2['metadata']['coordinates']['points'][0][1]
  y2max = elem2['metadata']['coordinates']['points'][1][1]

  x_distance = min(abs(x1max - x2min), abs(x1min - x2max))
  y_distance = min(abs(y1max - y2min), abs(y1min - y2max))

  return {'x': x_distance, 'y': y_distance}


def filter_empty_text(data):
  filtered_data = []

  for item in data:
    if item['text'].strip():  
      filtered_data.append(item)

  return filtered_data


def is_in_page_number(elem, page_number):
  return elem["metadata"]["page_number"] == page_number


