import json

import requests

API_KEY = ''


def get_all_assay():
    url = 'https://api-ccte.epa.gov/bioactivity/assay/'
    headers = {'Content-Type': 'application/json', 'X-Api-Key': API_KEY}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            assays = response.json()
            return assays
        else:
            print('Error fetching assays:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error fetching assays:', e)
        return None


if __name__ == '__main__':
    all_assay_values = get_all_assay()
    assays_to_write = []
    for index, assay in enumerate(all_assay_values, start=1):
        aeid = assay.get('aeid')
        assay_name = assay.get('assayComponentEndpointName')
        if aeid is None:
            print("Skipping assay with missing 'aeid'.")
            continue
        assays_to_write.append({'aeid': aeid, 'assay_name': assay_name})
    with open('all_assays.json', 'w') as f:
        json.dump(assays_to_write, f, indent=4)
