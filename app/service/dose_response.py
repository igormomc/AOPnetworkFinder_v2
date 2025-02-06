import pymc as pm
import numpy as np
import pandas as pd
import json
import requests
from app.service.convertExcelToJsonAc50 import get_excel_data


def run_dose_response(doseOfSubstance, chemical, ke_assay_dict):
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
    with open('app/localDataFiles/chemNameToDsstoxid.json', 'r') as file:
        chem_to_dsstoxi = json.load(file)
    with open('app/localDataFiles/allAssays.json', 'r') as file2:
        all_assays_json = json.load(file2)
    with open('app/localDataFiles/structured_filename.json', 'r') as file3:
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
                print("AC DATA HERE:", ac50_value)
                # If the value is in a list, return the first element
                return ac50_value[0] if isinstance(ac50_value, list) else ac50_value
        return None

    # --------------------------------------------------
    # 3. Hill-equation-based likelihood
    # --------------------------------------------------
    def hill_equation_likelihood(dose, ac50):
        """Simple Hill-like equation: response = dose / (dose + AC50)."""
        return dose / (dose + ac50) if (dose >= 0 and ac50 is not None) else 0

    # --------------------------------------------------
    # 4. Compute (or retrieve) the average AC50 for each KE
    # --------------------------------------------------
    ke_avg_ac50 = {}
    dsstox_substance_id = None
    for item in chem_to_dsstoxi:
        if item['chnm'] == chemical:
            dsstox_substance_id = item['dsstox_substance_id']
            break
    if dsstox_substance_id is None:
        print(f"Could not find dsstox_substance_id for chemical '{chemical}'")
        return None

    for ke_number, assay_info_list in ke_assay_dict.items():
        # The assay_info_list can be either:
        #   - Case A: a list of assay names, e.g., ["BSK_BT_xTNFa", "BSK_LPS_TNFa", ...]
        #   - Case B: a list of dictionaries that already include AC50 values.
        if not assay_info_list:
            ke_avg_ac50[ke_number] = None
            continue

        first_item = assay_info_list[0]
        ac50_values = []

        if isinstance(first_item, str):
            # --- Case A: array of assay names --- #
            for assay_name in assay_info_list:
                ac50_val = get_ac50_for_assay(assay_name, dsstox_substance_id)
                if ac50_val is not None:
                    ac50_values.append(ac50_val)

        elif isinstance(first_item, dict):
            # --- Case B: array of objects that already contain AC50 --- #
            for obj in assay_info_list:
                if obj.get("chemical") == chemical:
                    ac50_str = obj.get("ac50")
                    try:
                        ac50_val = float(ac50_str)
                        ac50_values.append(ac50_val)
                    except (ValueError, TypeError):
                        print(f"[WARN] Could not convert '{ac50_str}' to float AC50.")
                else:
                    print(f"[INFO] Skipping object with different chemical: {obj.get('chemical')}")
        else:
            print(f"[WARN] Unexpected item type in ke_assay_dict for KE '{ke_number}'. Skipping.")
            ke_avg_ac50[ke_number] = None
            continue

        if ac50_values:
            print("ac50_values", ac50_values)
            ac50_avg = sum(ac50_values) / len(ac50_values)
            ke_avg_ac50[ke_number] = ac50_avg
        else:
            ke_avg_ac50[ke_number] = None

    # --------------------------------------------------
    # 5. Compute the Hill-likelihood for each KE
    # --------------------------------------------------
    ke_likelihoods = {}
    for ke_number, ac50_value in ke_avg_ac50.items():
        if ac50_value is not None:
            likelihood = hill_equation_likelihood(doseOfSubstance, ac50_value)
            ke_likelihoods[ke_number] = likelihood
        else:
            print(f"[INFO] ac50_value is None for KE '{ke_number}'. Setting likelihood to None.")
            ke_likelihoods[ke_number] = None

    # --------------------------------------------------
    # 6. Build and sample the Bayesian model (illustrative)
    # --------------------------------------------------
    with pm.Model() as model:
        # Create a Beta prior for each KE
        ke_priors = {}
        for ke_number in ke_avg_ac50.keys():
            ke_priors[ke_number] = pm.Beta(ke_number, alpha=2, beta=5)
        # A single Beta prior for "AO"
        ao_prior = pm.Beta("AO", alpha=5, beta=1)

        # Sample from the posterior
        trace = pm.sample(500, return_inferencedata=True, progressbar=False)

    # --------------------------------------------------
    # 7. Extract means from the posterior
    # --------------------------------------------------
    ke_prior_means = {}
    for ke_number in ke_avg_ac50.keys():
        ke_prior_means[ke_number] = np.mean(trace.posterior[ke_number].values)

    mean_prior_ao = np.mean(trace.posterior["AO"].values)

    # --------------------------------------------------
    # 8. Calculate Probability of AO at this dose
    # --------------------------------------------------
    valid_likelihoods = [lk for lk in ke_likelihoods.values() if lk is not None]
    if valid_likelihoods:
        P_AO_at_dose = np.prod(valid_likelihoods)
    else:
        P_AO_at_dose = 0

    # --------------------------------------------------
    # 9. Determine which events exceed a threshold
    # --------------------------------------------------
    threshold = 0.5
    activated_events = []
    for ke_number, likelihood_value in ke_likelihoods.items():
        if (likelihood_value is not None) and (likelihood_value >= threshold):
            activated_events.append(ke_number)
    if P_AO_at_dose >= threshold:
        activated_events.append("AO")

    # --------------------------------------------------
    # 10. Return final results
    # --------------------------------------------------
    rounded_ke_likelihoods = {}
    for k, v in ke_likelihoods.items():
        rounded_ke_likelihoods[k] = round(v, 3) if v is not None else None

    rounded_ke_prior_means = {k: round(v, 3) for k, v in ke_prior_means.items()}

    return {
        "dose": doseOfSubstance,
        "ke_likelihoods": rounded_ke_likelihoods,
        "probability_AO": round(P_AO_at_dose, 3),
        "activated_events": activated_events,
        "ke_prior_means": rounded_ke_prior_means,
        "ao_prior_mean": round(mean_prior_ao, 3),
    }
