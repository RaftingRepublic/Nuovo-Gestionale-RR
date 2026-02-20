import urllib.request
import urllib.error
import urllib.parse
import json
import ssl

# CONFIGURAZIONE
BASE_URL = "https://gestionale.raftingrepublic.com"
API_PREFIX = "/api/v1"

# SSL Context (ignora self-signed)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

COLORS = {
    "HEADER": "\033[95m",
    "OKBLUE": "\033[94m",
    "OKGREEN": "\033[92m",
    "WARNING": "\033[93m",
    "FAIL": "\033[91m",
    "ENDC": "\033[0m",
}

def print_status(method, endpoint, status, extra=""):
    color = COLORS["OKGREEN"] if 200 <= status < 300 else COLORS["FAIL"]
    print(f"{method:<6} {endpoint:<40} {color}{status}{COLORS['ENDC']} {extra}")

def make_request(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    req = urllib.request.Request(url, method=method)
    
    if data is not None:
        json_data = json.dumps(data).encode("utf-8")
        req.add_header("Content-Type", "application/json; charset=utf-8")
        req.data = json_data
    
    req.add_header("User-Agent", "RR-Verifier/1.0")

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            headers = dict(response.info())
            return status, body, headers, None
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        headers = dict(e.headers)
        return e.code, body, headers, str(e)
    except Exception as e:
        return 0, None, {}, str(e)

def run_tests():
    print(f"{COLORS['HEADER']}=== DEBUG 'METHOD NOT ALLOWED' ==={COLORS['ENDC']}")
    
    # 1. TEST POST /registration/submit (Simula invio form)
    print(f"\n{COLORS['HEADER']}1. Test POST Submit{COLORS['ENDC']}")
    payload = {
        "participant": {
            "nome": "Test", "cognome": "Bot", "data_nascita": "1990-01-01",
            "tipo_documento": "CIE", "numero_documento": "CA12345AA",
            "scadenza_documento": "2030-01-01"
        },
        "contact": {"email": "test@bot.com", "telefono": "123456"}
    }
    # Nota: Mando payload incompleto intenzionalmente per vedere se risponde 422 (OK) o 405 (Error)
    status, body, headers, _ = make_request("/registration/submit", method="POST", data=payload)
    
    # Stampa Header Debug
    if headers:
        print(f"DEBUG Headers (All):")
        for k, v in headers.items():
            if k.lower().startswith("x-bridge") or k.lower() == "location":
                 print(f"  {k}: {v}")

    if status == 405:
        print_status("POST", "/registration/submit", 405, f"METHOD NOT ALLOWED!\nBody: {body}")
    elif status == 422:
        print_status("POST", "/registration/submit", 422, "Validation Error (Bene! Endpoint Raggiunto)")
    else:
        print_status("POST", "/registration/submit", status, f"Risposta: {body[:100]}...")

    # 2. TEST OPTIONS (CORS Preflight)
    print(f"\n{COLORS['HEADER']}2. Test OPTIONS (CORS){COLORS['ENDC']}")
    status, body, _, _ = make_request("/registration/submit", method="OPTIONS")
    
    if status == 405:
        print_status("OPTIONS", "/registration/submit", 405, f"CORS Fallito!\nBody: {body}")
    else:
        print_status("OPTIONS", "/registration/submit", status, "CORS OK (probabilmente)")

    # 3. TEST SCAN (POST Multipart simulation - empty)
    print(f"\n{COLORS['HEADER']}3. Test POST Scan{COLORS['ENDC']}")
    status, body, _, _ = make_request("/registration/scan", method="POST", data={}) 
    print_status("POST", "/registration/scan", status, "Check 403 (Scan)")

if __name__ == "__main__":
    run_tests()
