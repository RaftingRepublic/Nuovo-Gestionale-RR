import requests
import json
import uuid
from datetime import datetime
import time

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    print("🚀 Starting Reservation Logic Verification...")
    
    # 1. Setup Data
    today = datetime.now().strftime("%Y-%m-%d")
    test_time = "10:00"
    activity = "CLASSICA"
    
    print(f"📅 Testing Date: {today}, Time: {test_time}")

    # 0. Ensure Rule Exists
    print("👉 Creating Test Activity Rule...")
    rule_payload = {
        "activity_type": activity,
        "name": "TEST_RULE",
        "valid_from": today,
        "valid_to": today,
        "days_of_week": [0,1,2,3,4,5,6], # All days
        "start_times": [test_time]
    }
    rule = requests.post(f"{BASE_URL}/resources/activity-rules", json=rule_payload).json()
    rule_id = rule['id']

    try:
        # Clean up previous overrides
        ovrs = requests.get(f"{BASE_URL}/reservations/overrides", params={"date": today}).json()
        for o in ovrs:
            if o['time'] == test_time: 
                requests.delete(f"{BASE_URL}/reservations/overrides/{o['id']}")

        # 2. Get Initial Status (Should be GREEN or already partially booked)
        def get_slot_status():
            sched = requests.get(f"{BASE_URL}/resources/daily-schedule", params={"date": today}).json()
            for s in sched:
                if s['time'] == test_time and s['activity_type'] == activity:
                    return s
            return None

        # Wait a bit for potential file IO if needed (though API is sync)
        time.sleep(0.5) 

        initial_slot = get_slot_status()
        if not initial_slot:
            print("❌ Slot STILL not found in schedule. Check API.")
            return

        print(f"ℹ️ Initial Status: {initial_slot['status']} ({initial_slot['status_desc']}) - Booked: {initial_slot['booked_pax']}")
        
        # 3. Create Reservation (Small) -> Expect GREEN ('A')
        res_payload = {
            "date": today, "time": test_time, "activity_type": activity,
            "pax": 2, "customer_name": "Test User 1"
        }
        r1 = requests.post(f"{BASE_URL}/reservations/", json=res_payload).json()
        res_id1 = r1['id']
        print(f"✅ Created Reservation 1 (2 pax). ID: {res_id1}")
        
        slot_after_1 = get_slot_status()
        print(f"   Status: {slot_after_1['status']} - Booked: {slot_after_1['booked_pax']}")
        
        # 4. Create Reservation (Large) -> Expect BLUE ('D') (Confirmed)
        res_payload['pax'] = 4
        res_payload['customer_name'] = "Test User 2"
        r2 = requests.post(f"{BASE_URL}/reservations/", json=res_payload).json()
        res_id2 = r2['id']
        print(f"✅ Created Reservation 2 (4 pax). ID: {res_id2}")
        
        slot_after_2 = get_slot_status()
        print(f"   Status: {slot_after_2['status']} - Booked: {slot_after_2['booked_pax']}")
        if slot_after_2['status'] == 'D':
            print("   ✅ CORRECT: Status became Blue (Confirmed)")
        else:
             print(f"   ⚠️ WARNING: Expected Blue (D), got {slot_after_2['status']}")

        # 5. Fill Capacity -> Expect RED ('C')
        res_payload['pax'] = 100 # Force Overflow
        res_payload['customer_name'] = "Test User 3"
        r3 = requests.post(f"{BASE_URL}/reservations/", json=res_payload).json()
        res_id3 = r3['id']
        
        slot_after_3 = get_slot_status()
        print(f"   Status: {slot_after_3['status']} - Booked: {slot_after_3['booked_pax']}")
        if slot_after_3['status'] == 'C':
            print("   ✅ CORRECT: Status became Red (Full)")
        elif slot_after_3['status'] == 'B':
            print("   ⚠️ Note: Status is Yellow/Almost Full (Maybe capacity is higher than expected)")
            
        # 6. Manual Override -> Force GREEN ('A')
        print("👉 Testing Manual Override...")
        ovr_payload = {
            "date": today, "time": test_time, "activity_type": activity,
            "forced_status": "A"
        }
        ovr = requests.post(f"{BASE_URL}/reservations/overrides", json=ovr_payload).json()
        ovr_id = ovr['id']
        
        slot_override = get_slot_status()
        print(f"   Status: {slot_override['status']} ({slot_override['status_desc']})")
        
        if slot_override['status'] == 'A':
            print("   ✅ CORRECT: Override forced status to Green (A)")
        else:
            print("   ❌ FAILED: Override did not work.")

        # Cleanup Loop
        print("🧹 Cleaning up Reservations...")
        requests.delete(f"{BASE_URL}/reservations/{res_id1}")
        requests.delete(f"{BASE_URL}/reservations/{res_id2}")
        requests.delete(f"{BASE_URL}/reservations/{res_id3}")
        requests.delete(f"{BASE_URL}/reservations/overrides/{ovr_id}")
        
    finally:
        print("🧹 Cleaning up Rule...")
        requests.delete(f"{BASE_URL}/resources/activity-rules/{rule_id}")
        
    print("✅ Test Complete.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"❌ Error running test: {e}")
