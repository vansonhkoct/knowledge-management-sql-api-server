import http.client
import json
import time
import os
import csv
from datetime import datetime

index_name = "56e0a540-fb4f-40b6-acdd-d325d3d0fd65"
document_category = "ed6042cf-17ac-4e9c-b224-23273f8a5f80"

qtemplates = [
    "會議紀錄中[QSUBJECT]相關資料",
    "[QSUBJECT]由那一個機構主辦？",
    "[QSUBJECT]的詳情？",
    "[QSUBJECT]相關注意事項",
    "[QSUBJECT]相關資料？",
    "[QSUBJECT]的學校行政指引",
    "[QSUBJECT]日程時間表？",
    "[QSUBJECT]的活動日程？",
    "[QSUBJECT]籌辦時須注意的事項",
    "請列舉出[QSUBJECT]相關的活動",
]

qsubjects = [
    "多元智能躍進計劃",
    "國民教育",
    "國安法教育",
    # "國安法",
    # "2023/24校務會議",
    # "2023/24公民與社會發展科網上閱讀獎勵計劃",
]


qstrategycombinations = {
  "S1": ("1", None, 2),
  "S2_PAGE_V1": ("2", "PAGE", 1),
  "S2_CHUNK_V1": ("2", "CHUNK", 1),
  "S2_CHUNK990_V1": ("2", "CHUNK990", 1),
  "S2_PAGE_V4": ("2", "PAGE", 4),
  "S2_CHUNK_V4": ("2", "CHUNK", 4),
  "S2_CHUNK990_V4": ("2", "CHUNK990", 4),
}


k = 10
num_candidates = 100


def _call_test_api(body):
    conn = http.client.HTTPConnection("192.168.2.107", 27891)
    payload = json.dumps(body)
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer 9adfbf38-2a2c-48d6-b4d7-4e0c9d5fa9c1",
    }
    conn.request(
        "POST",
        "/api/v1/file_estest/test_llm_ask_question",
        payload,
        headers,
    )
    res = conn.getresponse()
    data = res.read()
    return data.decode("utf-8")
    


def test_search_A(
  question,
  data_strategy,
  data_portion_type = None,
  data_vector_query_strategy = 1,
):
    return _call_test_api(
        {
            "index_name": f"{index_name}",
            "document_category": f"{document_category}",
            "question": question,
            "data_strategy": data_strategy,
            "data_portion_type": data_portion_type,
            "data_vector_query_strategy": data_vector_query_strategy,
            "skip_llm": True,
        }
    )


timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

csv_data_bundle = {}

for qsubjectIndex, qsubject in enumerate(qsubjects):
    for qtemplateIndex, qtemplate in enumerate(qtemplates):
        for qstrat in qstrategycombinations.keys():
          
          data_strategy, data_portion_type, data_vector_query_strategy = qstrategycombinations[qstrat]
          
          question = qtemplate.replace("[QSUBJECT]", qsubject)
          print(f"Ask: {qsubjectIndex} - {qtemplateIndex} - {question}")

          # Specify the folder and file path
          folder_path = f"tests/res_t11/result_{timestamp}/qs{qsubjectIndex}/qt{qtemplateIndex}"

          # Create the folder if it doesn't exist
          if not os.path.exists(folder_path):
              os.makedirs(folder_path)


          # Write the JSON data to a file
          with open(
              os.path.join(folder_path, f"result_test_search_{qstrat}.json"), "w", encoding="utf-8"
          ) as file:
              res = test_search_A(question, data_strategy, data_portion_type, data_vector_query_strategy)
              json.dump(json.loads(res)["es_result"], file, ensure_ascii=False, indent=4)

          with open(
              os.path.join(folder_path, f"simple_page_result_test_search_{qstrat}.json"), "w", encoding="utf-8"
          ) as file:
              extracted_data = json.loads(test_search_A(question, data_strategy, data_portion_type, data_vector_query_strategy))["es_result"]
              extracted_small_data = [ {"score": data["score"], "page": data["metadata"]["page"], "filename": data["metadata"]["document_file_name"] } for data in extracted_data ]
              json.dump( extracted_small_data , file, ensure_ascii=False, indent=4)
              
              csv_data_bundle[qsubjectIndex] = csv_data_bundle[qsubjectIndex] if qsubjectIndex in csv_data_bundle else {}
              csv_data_bundle[qsubjectIndex][qtemplateIndex] = csv_data_bundle[qsubjectIndex][qtemplateIndex] if qtemplateIndex in csv_data_bundle[qsubjectIndex] else {}
              csv_data_bundle[qsubjectIndex][qtemplateIndex][qstrat] = csv_data_bundle[qsubjectIndex][qtemplateIndex][qstrat] if qstrat in csv_data_bundle[qsubjectIndex][qtemplateIndex] else [
                ["qsubjectIndex", "qtemplateIndex", "score", "page", "filename", "question", "header", "content", ],
              ]

              for edataIndex, edata in enumerate(extracted_small_data):
                  csv_data_bundle[qsubjectIndex][qtemplateIndex][qstrat].append([ qsubjectIndex, qtemplateIndex, edata["score"], edata["page"], edata["filename"], question, extracted_data[edataIndex]["header"] if "header" in extracted_data[edataIndex] else "",   extracted_data[edataIndex]["content"], ])


for qsubjectIndex, qsubject in enumerate(qsubjects):
    for qtemplateIndex, qtemplate in enumerate(qtemplates):
      for qstrat in qstrategycombinations.keys():
        # Write the data to a CSV file
        with open(f"tests/res_t11/result_{timestamp}/report_{qsubjectIndex}_{qtemplateIndex}_{qstrat}.csv", 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(csv_data_bundle[qsubjectIndex][qtemplateIndex][qstrat])
        
print('CSV file created successfully!')

