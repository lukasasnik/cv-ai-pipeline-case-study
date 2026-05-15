from fastapi import FastAPI
from fastapi.testclient import TestClient

from routers.health import router


def test_health_route_returns_ok_status():
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "CV AI Pipeline API",
    }
