import time
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.services.resources.priority_engine import PriorityEngine

def benchmark():
    engine = PriorityEngine()
    
    print("Starting benchmark for get_month_overview(detailed=True)...")
    start_time = time.time()
    
    # Simulate the heavy call
    data = engine.get_month_overview(2026, 7, detailed=True)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Call finished in {duration:.4f} seconds")
    print(f"Days returned: {len(data)}")
    
    # Check slots count
    total_slots = sum(len(d.get('slots', [])) for d in data)
    print(f"Total slots processed: {total_slots}")

if __name__ == "__main__":
    benchmark()
