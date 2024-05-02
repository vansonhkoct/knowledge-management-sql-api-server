
# mypy: no-disallow-untyped-decorators
# pylint: disable=E0611,E0401
from fastapi.testclient import TestClient

import sys
import os

parent_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(parent_dir + "/../")


from apiapp.APIApplication import app

client = TestClient(app)


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200, response.text
    data = response.json()
    print(data)
    # assert data["username"] == "admin"
    # user_id = data["id"]

    # user_obj = await Users.get(id=user_id)
    # assert user_obj.id == user_id

# async def test_create_user(client: AsyncClient):  # nosec
#     response = await client.post("/api/v1/health", json={"username": "admin"})
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["username"] == "admin"
#     assert "id" in data
#     user_id = data["id"]

#     user_obj = await Users.get(id=user_id)
#     assert user_obj.id == user_id




