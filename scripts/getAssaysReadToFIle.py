import json
import requests
import sys

API_KEY = '8657de54-453e-4575-a341-e9c63c9f28ef'

def get_all_assay():
    url = 'https://api-ccte.epa.gov/bioactivity/assay/'
    headers = {'Content-Type': 'application/json', 'X-Api-Key': API_KEY}
    r = requests.get(url, headers=headers)
    try:
        r.raise_for_status()
    except requests.HTTPError as e:
        print("Error fetching assays:", e, file=sys.stderr)
        return None
    return r.json()

def write_assays_to_file(filename):
    """Write a list of assay dicts to a JSON file."""
    assays = get_all_assay()
    with open(filename, 'w') as out:
        json.dump(assays, out, indent=4)

def group_assays(assays):
    """Group a list of assay dicts by geneSymbol."""
    grouped = {}
    for a in assays or []:
        if not isinstance(a, dict):
            continue
        gene = a.get('gene')
        if not isinstance(gene, dict):
            continue
        symbol = gene.get('geneSymbol')
        if not symbol:
            continue
        grouped.setdefault(symbol, []).append(a)
    return grouped

def process_assays():
    """Fetch all assays, group them by geneSymbol, and write to JSON."""
    assays = get_all_assay()
    if not isinstance(assays, list):
        print("No assays fetched (got None or non‑list).", file=sys.stderr)
        sys.exit(1)

    grouped = group_assays(assays)

    with open('grouped_assays.json', 'w') as out:
        json.dump(grouped, out, indent=4)

    print(f"Saved {len(grouped)} geneSymbol groups to grouped_assays.json")

if __name__ == '__main__':
    #write_assays_to_file('all_assays.json')
    process_assays()

