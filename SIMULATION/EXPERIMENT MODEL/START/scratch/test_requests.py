import requests
import json

base_url = "http://router.project-osrm.org"
coords = "112.62633,-7.98182;112.52306,-7.88694"
url = f"{base_url}/route/v1/driving/{coords}?overview=false&alternatives=false&steps=false"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}

try:
    resp = requests.get(url, headers=headers, timeout=10)
    print("Status code:", resp.status_code)
    data = resp.json()
    print("Code:", data.get("code"))
    print("Routes:", len(data.get("routes", [])))
except Exception as e:
    print("Exception:", e)
