import httpx  # type: ignore Required for fastapi testing
import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.mark.parametrize(
    "status_code,path",
    [
        (400, "/roll"),
        (200, "/roll?expression=1d6"),
        (200, "/roll?expression=1d6&advantage=advantage"),
        (400, "/roll?expression=1d6&advantage=invalid"),
    ],
)
def test_status_codes(client: TestClient, path: str, status_code: int):
    result = client.get(path)
    assert result.status_code == status_code
