import json

import requests

API_KEY = ''


def get_all_assay():
    url = 'https://api-ccte.epa.gov/bioactivity/assay/'
    headers = {'Content-Type': 'application/json', 'X-Api-Key': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print('Error fetching assays:', response.status_code)
            return None
    except requests.exceptions.RequestException as e:
        print('Error fetching assays:', e)
        return None


def get_aied_data(aeid):
    url = f'https://api-ccte.epa.gov/bioactivity/data/search/by-aeid/{aeid}'
    headers = {'Content-Type': 'application/json', 'X-Api-Key': API_KEY}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data if isinstance(data, list) and data else None
        else:
            print(f"Error fetching data for aeid {aeid}: Status code {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Request exception for aeid {aeid}: {e}")
        return None


def main():
    all_assays = get_all_assay()
    if not all_assays:
        return

    result = {}
    total_assays = len(all_assays)
    # Process only a subset (here the first 3 assays) – adjust the slice as needed. Change this if you want to process all assays: THIS TAKES A LONG TIME
    for index, assay in enumerate(all_assays[:3], start=1):
        aeid = assay.get('aeid')
        assay_name = assay.get('assayComponentEndpointName')
        if aeid is None or assay_name is None:
            print("Skipping assay with missing 'aeid' or 'assayComponentEndpointName'.")
            continue

        # Get additional data using the aeid
        aied_data = get_aied_data(aeid)
        if not aied_data:
            print(f"No additional data found for aeid {aeid}.")
            continue

        assay_data = {}
        for entry in aied_data:
            dtxsid = entry.get('dtxsid')
            if not dtxsid:
                print(f"Skipping data entry for aeid {aeid} due to missing dtxsid.")
                continue
            # Remove the "DTXSID" prefix if present.
            id_str = dtxsid[6:] if dtxsid.startswith("DTXSID") else dtxsid

            # Get the AC50 value from the nested 'mc5Param' dictionary.
            mc5Param = entry.get('mc5Param', {})
            ac50 = mc5Param.get('ac50')
            if ac50 is None:
                continue

            # Round ac50 to a maximum of 5 decimals.
            ac50_rounded = round(ac50, 5)
            # Convert whole numbers to int.
            if ac50_rounded == int(ac50_rounded):
                ac50_rounded = int(ac50_rounded)

            # Save the value inside a list.
            if id_str in assay_data:
                assay_data[id_str].append(ac50_rounded)
            else:
                assay_data[id_str] = [ac50_rounded]

        # Only add assay if there is valid data.
        if assay_data:
            result[assay_name] = assay_data

        print(f"Processed assay {index} ({aeid}) of {min(total_assays, 3)}")

    # Write the JSON output on one line (compact representation).
    try:
        with open('assayDataForChem.json', 'w') as json_file:
            json_file.write(json.dumps(result, separators=(',', ':')))
        print(f"Successfully wrote {len(result)} assays to assayDataForChem.json")
    except IOError as e:
        print(f"An error occurred while writing to assayDataForChem.json: {e}")


if __name__ == "__main__":
    main()
