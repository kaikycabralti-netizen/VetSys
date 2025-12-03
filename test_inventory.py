import requests
import sys

def test_inventory_flow():
    base_url = "http://127.0.0.1:8000"
    print("--- Testing Inventory Flow ---")

    # 1. Check Dashboard Initial State
    r = requests.get(f"{base_url}/api/dashboard")
    initial_count = r.json()['total_estoque']
    print(f"[INFO] Initial Stock Count: {initial_count}")

    # 2. Add New Item
    item_data = {
        "item": "Test Item 123",
        "categoria": "Medicamentos",
        "quantidade": 50,
        "validade": "2026-01-01",
        "status": "OK"
    }
    r = requests.post(f"{base_url}/api/estoque", json=item_data)
    if r.status_code == 201:
        print("[OK] Item Created")
    else:
        print(f"[FAIL] Create Item: {r.text}")
        return

    # 3. Check Dashboard Update
    r = requests.get(f"{base_url}/api/dashboard")
    new_count = r.json()['total_estoque']
    if new_count == initial_count + 1:
        print(f"[OK] Dashboard Updated: {new_count}")
    else:
        print(f"[FAIL] Dashboard Count Mismatch: Expected {initial_count + 1}, Got {new_count}")

    # 4. List Items
    r = requests.get(f"{base_url}/api/estoque")
    items = r.json()
    found = any(i['item'] == "Test Item 123" for i in items)
    if found:
        print("[OK] Item found in list")
    else:
        print("[FAIL] Item not found in list")

if __name__ == "__main__":
    try:
        test_inventory_flow()
    except Exception as e:
        print(f"[ERROR] {e}")
