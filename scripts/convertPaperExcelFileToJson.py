import json
import re

import mygene
import pandas as pd
from tqdm import tqdm


def main():
    df = pd.read_excel("GenesToKe.xlsx")

    mg = mygene.MyGeneInfo()

    # Get the list of unique Ensembl IDs from the DataFrame first 3 rows
    gene_ids = df["Gene"].unique().tolist()

    results = mg.querymany(gene_ids, scopes="ensembl.gene", fields="symbol", species="human")

    id_to_symbol = {}
    for entry in results:
        ensembl_id = entry.get("query")
        symbol = entry.get("symbol")
        if symbol:
            id_to_symbol[ensembl_id] = symbol

    ke_to_symbols = {}

    for _, row in tqdm(df.iterrows(), total=df.shape[0], desc="Processing rows"):
        ke_raw = row["KE"]
        ensembl_id = row["Gene"]

        # Convert "Event:10" -> "KE10"
        ke_clean = re.sub(r"Event:", "KE", ke_raw)

        symbol = id_to_symbol.get(ensembl_id)

        if ke_clean not in ke_to_symbols:
            ke_to_symbols[ke_clean] = []

        if symbol:
            ke_to_symbols[ke_clean].append(symbol)

    with open("GenesToKe.json", "w") as f:
        json.dump(ke_to_symbols, f, indent=4)

    print("Conversion complete! JSON saved as GenesToKe.json")


def minify_json(input_filepath, output_filepath):
    """
    Reads a JSON file from 'input_filepath' and writes a minified (one-line) version
    to 'output_filepath'.
    
    Parameters:
        input_filepath (str): Path to the input JSON file.
        output_filepath (str): Path to save the minified JSON file.
    """
    with open(input_filepath, 'r') as infile:
        data = json.load(infile)

    with open(output_filepath, 'w') as outfile:
        json.dump(data, outfile, separators=(',', ':'))

    print(f"Minified JSON has been saved to {output_filepath}")


if __name__ == "__main__":
    # firsdt run main() to create the JSON file
    # then run minify_json() to create the minified version
    main()  # This can take a while to run
    # minify_json("GenesToKe.json", "GenesToKe_minified.json")
