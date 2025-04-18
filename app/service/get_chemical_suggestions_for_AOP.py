import json
import random


def get_chemical_suggestions_for_aop(aop_id):
    try:
        with open('app/localDataFiles/aop_chem_counts.json', 'r') as file:
            aop_chem_counts = json.load(file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return None

    aop_data = aop_chem_counts.get(aop_id, {})
    if not aop_data:
        return []

    all_chemicals = []
    for assay_id, chemical_list in aop_data.items():
        if isinstance(chemical_list, list):
            all_chemicals.extend(chemical_list)

    filtered_chemicals = [chem for chem in all_chemicals if len(chem) <= 30]

    if len(filtered_chemicals) < 3:
        return filtered_chemicals

    return random.sample(filtered_chemicals, 3)
