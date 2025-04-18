import json

import numpy as np

from app.service.branch_correction import run_goat_dose_response
from app.service.convertExcelToJsonAc50 import get_excel_data


def run_dose_response(doseOfSubstance, chemical, ke_assay_dict, handleDataNodesMode, aop_id, manualKEEdges):
    ke_with_no_ac50Data = {}

    """
    Args:
        doseOfSubstance (float): Dose in μM (or other consistent unit).
        chemical (str): The chemical name to look up or match.
        ke_assay_dict (dict): A dictionary mapping KE number (str) to a list
                              *either* of assay names (str) or objects containing "ac50".
                              e.g.,
                              {"55": ["BSK_BT_xTNFa", "BSK_LPS_TNFa", "LTEA_HepaRG_BCL2"]}
                              {"386": [{"gene": "CA1", "ac50": "5", "chemical": "Azoxystrobin"}]}
    Returns:
        dict: Results of the Bayesian dose-response, including KE likelihoods, etc.
    """

    # --------------------------------------------------
    # 1. Load your Excel data and supporting JSON files
    # --------------------------------------------------
    df, json_data = get_excel_data()
    with open('app/localDataFiles/chem_to_dsstox.json', 'r') as file:
        chem_to_dsstoxi = json.load(file)
    with open('app/localDataFiles/allAssays.json', 'r') as file2:
        all_assays_json = json.load(file2)
    with open('app/localDataFiles/restricted_aop_KeGene.json', 'r') as file3:
        testdata = json.load(file3)

    # --------------------------------------------------
    # 2. Helper: Get AC50 for a single assay from the new JSON testdata
    # --------------------------------------------------
    def get_ac50_for_assay(assay_name, chemical_id):
        """
        With the new testdata structure, for example:
        {
          "ERF_CR_ENZ_hELANE": {
              "8031077": [0.384],
              "3041035": [5]
          },
          ...
        }
        The keys no longer include the "DTXSID" prefix. So if chemical_id
        comes in as "DTXSID8031077", we remove the prefix before lookup.
        """
        # Remove "DTXSID" prefix if present
        lookup_key = chemical_id
        if chemical_id.startswith("DTXSID"):
            lookup_key = chemical_id[len("DTXSID"):]

        assay_data = testdata.get(assay_name)
        if assay_data is not None:
            ac50_value = assay_data.get(lookup_key)
            if ac50_value is not None:
                # If the value is in a list, return the first element
                return ac50_value[0] if isinstance(ac50_value, list) else ac50_value
        return None

    # --------------------------------------------------
    # 3. Hill-equation-based likelihood
    # dose is of concentration in μM
    # --------------------------------------------------
    def hill_equation_likelihood(dose, ac50):
        """Simple Hill-like equation: response = dose / (dose + AC50)."""
        return dose / (dose + ac50) if (dose >= 0 and ac50 is not None) else 0

    # --------------------------------------------------
    # 4. Compute (or retrieve) the average AC50 for each KE
    # --------------------------------------------------
    ke_values_ac50 = {}
    dsstox_substance_id = None
    for item in chem_to_dsstoxi:
        if item['chnm'] == chemical:
            dsstox_substance_id = item['dsstox_substance_id']
            break
    if dsstox_substance_id is None:
        print(f"Could not find dsstox_substance_id for chemical '{chemical}'")
        return None

    for ke_number, assay_info_list in ke_assay_dict.items():
        if not assay_info_list:
            ke_values_ac50[ke_number] = None
            continue

        ac50_values = []

        for assay in assay_info_list:
            if isinstance(assay, str):
                ac50_val = get_ac50_for_assay(assay, dsstox_substance_id)
                if ac50_val is not None:
                    ac50_values.append(ac50_val)

            elif isinstance(assay, dict):
                if assay.get("chemical") == chemical:
                    ac50_str = assay.get("ac50")
                    try:
                        ac50_val = float(ac50_str)
                        ac50_values.append(ac50_val)
                    except (ValueError, TypeError):
                        print(f"[WARN] Could not convert '{ac50_str}' to float AC50.")
                else:
                    print(f"[INFO] Skipping object with different chemical: {assay.get('chemical')}")

            else:
                print(f"[WARN] Unexpected assay type ({type(assay)}) for KE '{ke_number}'. Skipping.")

        if ac50_values:
            if handleDataNodesMode == "toggleAverage":
                ke_values_ac50[ke_number] = float(np.mean(ac50_values))
            elif handleDataNodesMode == "toggleMedian":
                ke_values_ac50[ke_number] = float(np.median(ac50_values))
            elif handleDataNodesMode == "toggleMinimum":
                value = np.min(ac50_values)
                print("np.min(ac50_value)", value)
                ke_values_ac50[ke_number] = int(value)
        else:
            ke_values_ac50[ke_number] = None
            ke_with_no_ac50Data[ke_number] = 'True'

    # for each key in ke_values_ac50 that are None, add to the ke_with_no_ac50Data dict
    for ke in ke_values_ac50:
        if ke_values_ac50[ke] == None:
            ke_with_no_ac50Data[ke] = 'True'

    print("ke_values_ac50::::IGI:", ke_values_ac50)
    AOP, probability = run_goat_dose_response(aop_id, dose=doseOfSubstance, AC50_values=ke_values_ac50,
                                              selected_nodes=None, manualKEEdges=manualKEEdges, )

    return {
        "dose": doseOfSubstance,
        "ke_with_no_ac50Data": ke_with_no_ac50Data,
        "AOP": AOP,
    }
