from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_tts_endpoint_success():
    response = client.post("/api/tts", json={"text": "Hello, this is Aria from Aura Skincare."})
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert len(response.content) > 5000  # Should be a valid mp3 binary stream

def test_tts_endpoint_empty_text():
    response = client.post("/api/tts", json={"text": "   "})
    assert response.status_code == 400

if __name__ == "__main__":
    test_tts_endpoint_success()
    test_tts_endpoint_empty_text()
    print("ALL TTS TESTS PASSED!")
