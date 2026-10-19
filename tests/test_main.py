from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_root_returns_successful_response():
     response = client.get("/")

     assert response.status_code == 200
     assert response.json() == {
     "message": "AI Business Intelligence Copilot is running",
     "version": "0.1.0",
     }

def test_health_check_returns_healthy_status():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == { 
           "status": "healthy",
   }
