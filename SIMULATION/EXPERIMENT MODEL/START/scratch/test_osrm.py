import urllib.request
import urllib.error
import json
import ssl

url = "https://router.project-osrm.org/route/v1/driving/112.62633,-7.98182;112.52306,-7.88694?overview=false"
req = urllib.request.Request(
    url,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"}
)

try:
    print("Trying with default SSL context...")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("Success! Status code:", resp.status)
        print("Response:", resp.read()[:200])
except Exception as e:
    print("Failed with exception:", type(e), e)

try:
    print("\nTrying with unverified SSL context...")
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        print("Success! Status code:", resp.status)
        print("Response:", resp.read()[:200])
except Exception as e:
    print("Failed with unverified context exception:", type(e), e)
