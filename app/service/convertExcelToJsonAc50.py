import functools

@functools.lru_cache(maxsize=1)
def get_excel_data():
    # Otherwise, read Excel
    import pandas as pd
    import json

    df = pd.read_excel("app/localDataFiles/tox-ac50.xlsx")
    # Drop rows that are completely empty
    df.dropna(axis=0, how='all', inplace=True)
    # Drop columns that are completely empty
    df.dropna(axis=1, how='all', inplace=True)

    # Clean up
    records = []
    for row_dict in df.to_dict(orient='records'):
        clean_dict = {}
        for k, v in row_dict.items():
            if pd.isna(v):
                continue
            if isinstance(v, (int, float)) and v >= 1000000:
                continue
            clean_dict[k] = v
        if clean_dict:
            records.append(clean_dict)

    json_data = json.dumps(records, indent=4)
    AC50_CACHE = (df, json_data)
    return AC50_CACHE