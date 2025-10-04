"""
Simple API test script to verify all endpoints work correctly.
Run: python test_api.py
"""
import requests
import sys

BASE = "http://localhost:8000"

def test_endpoints():
    print("Testing Pyrenees Weather API...\n")
    
    # Test catalog
    print("✓ Testing /api/catalog/areas")
    r = requests.get(f"{BASE}/api/catalog/areas")
    assert r.status_code == 200
    areas = r.json()
    print(f"  Found {len(areas)} areas")
    
    # Test search
    print("✓ Testing /api/catalog/peaks_all")
    r = requests.get(f"{BASE}/api/catalog/peaks_all?q=aneto")
    assert r.status_code == 200
    
    # Test adding mountain
    print("✓ Testing POST /api/my/mountains/aneto")
    r = requests.post(f"{BASE}/api/my/mountains/aneto")
    assert r.status_code == 200
    
    # Test getting list
    print("✓ Testing GET /api/my/mountains")
    r = requests.get(f"{BASE}/api/my/mountains")
    assert r.status_code == 200
    
    # Test weather
    print("✓ Testing GET /api/weather/aneto")
    r = requests.get(f"{BASE}/api/weather/aneto?band=base")
    assert r.status_code == 200
    weather = r.json()
    print(f"  Got {len(weather)} hours of forecast")
    
    print("\n✅ All tests passed!")

if __name__ == "__main__":
    try:
        test_endpoints()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)