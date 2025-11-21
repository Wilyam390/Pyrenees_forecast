"""
Integration tests for FastAPI endpoints.
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_areas():
    """Test GET /api/catalog/areas returns list of areas."""
    response = client.get("/api/catalog/areas")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "id" in data[0]
    assert "name" in data[0]


def test_list_massifs_valid_area():
    """Test GET /api/catalog/massifs with valid area."""
    response = client.get("/api/catalog/massifs?area=aragon")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_list_massifs_invalid_area():
    """Test GET /api/catalog/massifs with invalid area returns 404."""
    response = client.get("/api/catalog/massifs?area=invalid")
    
    assert response.status_code == 404


def test_list_peaks_all():
    """Test GET /api/catalog/peaks_all returns all peaks."""
    response = client.get("/api/catalog/peaks_all")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_list_peaks_all_with_search():
    """Test GET /api/catalog/peaks_all with search query."""
    response = client.get("/api/catalog/peaks_all?q=aneto")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert any("aneto" in p["name"].lower() for p in data)


def test_peak_details():
    """Test GET /api/catalog/peaks/{peak_id} returns peak details."""
    response = client.get("/api/catalog/peaks/aneto")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "aneto"
    assert "bands" in data
    assert "base" in data["bands"]
    assert "mid" in data["bands"]
    assert "summit" in data["bands"]


def test_peak_details_not_found():
    """Test GET /api/catalog/peaks/{peak_id} with invalid ID returns 404."""
    response = client.get("/api/catalog/peaks/nonexistent")
    
    assert response.status_code == 404


def test_add_and_list_mountain():
    """Test POST /api/my/mountains adds mountain to list."""
    add_response = client.post("/api/my/mountains/aneto")
    assert add_response.status_code == 200
    assert add_response.json()["ok"] is True
    
    list_response = client.get("/api/my/mountains")
    assert "aneto" in list_response.json()


def test_remove_mountain():
    """Test DELETE /api/my/mountains removes mountain from list."""
    client.post("/api/my/mountains/posets")
    
    delete_response = client.delete("/api/my/mountains/posets")
    assert delete_response.status_code == 200
    
    list_response = client.get("/api/my/mountains")
    assert "posets" not in list_response.json()


def test_add_invalid_mountain():
    """Test POST /api/my/mountains with invalid mountain ID returns 404."""
    response = client.post("/api/my/mountains/invalid")
    
    assert response.status_code == 404


def test_add_duplicate_mountain():
    """Test adding same mountain twice returns ok (idempotent)."""
    client.post("/api/my/mountains/aneto")
    response = client.post("/api/my/mountains/aneto")
    
    assert response.status_code == 200
    assert response.json()["ok"] is True