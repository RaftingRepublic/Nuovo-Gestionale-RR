import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    print("🚀 Starting Wizard Logic Verification...")
    
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"📅 Date: {today}")

    # 1. Fetch Schedule (Wizard Step 2)
    print("👉 Fetching Daily Schedule...")
    res = requests.get(f"{BASE_URL}/resources/daily-schedule", params={"date": today})
    
    if res.status_code != 200:
        print(f"❌ Failed to fetch schedule: {res.text}")
        return

    slots = res.json()
    print(f"ℹ️ Found {len(slots)} slots.")
    
    for s in slots:
        print(f"   ⏰ {s['time']} [{s['activity_type']}]")
        print(f"      Status: {s['status']} ({s['status_desc']})")
        print(f"      Booked: {s['booked_pax']}")
        print(f"      Overridden: {s.get('is_overridden', False)}") # Check if our new field is there
        
        # Test Wizard Logic locally
        is_full = (s['status'] == 'C')
        if is_full:
            print("      ⚠️ Slot is FULL (Wizard should disable it)")
        else:
             print("      ✅ Slot is AVAILABLE")

    print("\n✅ Wizard Logic Test Complete.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"❌ Error: {e}")
