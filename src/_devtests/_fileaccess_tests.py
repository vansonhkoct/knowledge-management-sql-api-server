
# mypy: no-disallow-untyped-decorators
# pylint: disable=E0611,E0401
from fastapi.testclient import TestClient

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../")


from apiapp.APIApplication import app

client = TestClient(app)


def test_file_upload():
    try:
      with open("test_file_SAKJDBFJKASBDJKASD.txt", "w") as f:
          f.write("File content")
      
      with open("test_file_SAKJDBFJKASBDJKASD.txt", "rb") as f:
          response = client.post("/api/v1/files/upload", files={"file": f})
      
      assert response.status_code == 200
      print(response.json())
      # assert response.json() == {
      #     "success": True,
      #     "message": "C_F001",
      #     "data": {"filename": "test_file_SAKJDBFJKASBDJKASD.txt", "size": 12}
      # }

    # Clean up the test file
    finally:
      if os.path.exists("test_file_SAKJDBFJKASBDJKASD.txt"):
          os.remove("test_file_SAKJDBFJKASBDJKASD.txt")