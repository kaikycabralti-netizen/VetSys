import requests
import sys

def test_crud():
    base_url = "http://127.0.0.1:8000"
    
    print("--- Testing Patients CRUD ---")
    # 1. Create a Patient
    patient_data = {
        "nome": "CRUD Test Dog",
        "tutor": "Tester",
        "especie": "Canine",
        "raca": "Poodle",
        "status": "Ativo"
    }
    r = requests.post(f"{base_url}/api/pacientes", json=patient_data)
    if r.status_code != 201:
        print(f"[FAIL] Create Patient: {r.text}")
        return
    
    patient_id = r.json()['id']
    print(f"[OK] Created Patient ID: {patient_id}")

    # 2. Update Patient
    update_data = {
        "nome": "CRUD Test Dog Updated",
        "tutor": "Tester Updated",
        "especie": "Canine",
        "raca": "Poodle",
        "status": "Inativo"
    }
    r = requests.put(f"{base_url}/api/pacientes/{patient_id}", json=update_data)
    if r.status_code == 200:
        print("[OK] Update Patient Passed")
    else:
        print(f"[FAIL] Update Patient Failed: {r.text}")

    # 3. Test Dashboard
    print("\n--- Testing Dashboard ---")
    r = requests.get(f"{base_url}/api/dashboard")
    if r.status_code == 200:
        stats = r.json()
        print(f"[OK] Dashboard Stats: {stats}")
    else:
        print(f"[FAIL] Dashboard Failed: {r.text}")

    # 4. Test Inventory
    print("\n--- Testing Inventory ---")
    item_data = {
        "item": "Vacina Teste",
        "categoria": "Vacinas",
        "quantidade": 100,
        "validade": "2025-12-31",
        "status": "OK"
    }
    r = requests.post(f"{base_url}/api/estoque", json=item_data)
    if r.status_code == 201:
        print(f"[OK] Created Inventory Item ID: {r.json()['id']}")
    else:
        print(f"[FAIL] Create Inventory Item: {r.text}")
    
    r = requests.get(f"{base_url}/api/estoque")
    if r.status_code == 200:
        print(f"[OK] Inventory List Size: {len(r.json())}")
    else:
        print(f"[FAIL] Get Inventory: {r.text}")

    # 5. Delete Patient (Cleanup)
    print("\n--- Cleanup ---")
    r = requests.delete(f"{base_url}/api/pacientes/{patient_id}")
    if r.status_code == 204:
        print("[OK] Delete Patient Passed")
    else:
        print(f"[FAIL] Delete Patient Failed: {r.text}")

if __name__ == "__main__":
    try:
        test_crud()
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to backend. Is it running on port 8000?")
