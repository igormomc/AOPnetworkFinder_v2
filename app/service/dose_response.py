import pymc as pm
import numpy as np
import pandas as pd
import json
import requests
from app.service.convertExcelToJsonAc50 import get_excel_data


def run_dose_response(doseOfSubstance, chemical, ke_assay_dict, handleDataNodesMode):
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
        print("assay_info_list", assay_info_list)

        for assay in assay_info_list:
            if isinstance(assay, str):
                print("Processing assay name:", assay)
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
            print("ac50_values", ac50_values)
            if(handleDataNodesMode == "toggleAverage"):
                ke_values_ac50[ke_number] = np.mean(ac50_values)
            elif(handleDataNodesMode == "toggleMedian"):
                ke_values_ac50[ke_number] = np.median(ac50_values)
            elif(handleDataNodesMode == "toggleMinimum"):
                ke_values_ac50[ke_number] = np.min(ac50_values)
        else:
            ke_values_ac50[ke_number] = None

    # --------------------------------------------------
    # 5. Compute the Hill-likelihood for each KE
    # --------------------------------------------------
    ke_likelihoods = {}
    ke_with_no_ac50Data = {}
    all_values = list(ke_values_ac50.values()) #this looks like [0.123, 0.345, 0.567, None, 0.789]
    avg_off_all_values = np.mean([val for val in all_values if val is not None])
    median_ac50 = np.median([val for val in all_values if val is not None])
    min_ac50 = np.min([val for val in all_values if val is not None])
    for ke_number, ac50_value in ke_values_ac50.items():
        if ac50_value is not None:
            likelihood = hill_equation_likelihood(doseOfSubstance, ac50_value)
            ke_likelihoods[ke_number] = likelihood
        else:
            if(handleDataNodesMode == "toggleAverage"):
                ke_likelihoods[ke_number] = hill_equation_likelihood(doseOfSubstance, avg_off_all_values)
            elif(handleDataNodesMode == "toggleMedian"):
                ke_likelihoods[ke_number] = hill_equation_likelihood(doseOfSubstance, median_ac50)
            elif(handleDataNodesMode == "toggleMinimum"):
                ke_likelihoods[ke_number] = hill_equation_likelihood(doseOfSubstance, min_ac50)
            else:
                ke_likelihoods[ke_number] = None
            ke_with_no_ac50Data[ke_number] = "No AC50 data available"


    # --------------------------------------------------
    # 6. Build and sample the Bayesian model (illustrative)
    # --------------------------------------------------
    with pm.Model() as model:
        # Create a Beta prior for each KE
        ke_priors = {}
        for ke_number in ke_values_ac50.keys():
            ke_priors[ke_number] = pm.Beta(ke_number, alpha=2, beta=5)
        # A single Beta prior for "AO"
        ao_prior = pm.Beta("AO", alpha=5, beta=1)

        # Sample from the posterior
        trace = pm.sample(500, return_inferencedata=True, progressbar=False)

    # --------------------------------------------------
    # 7. Extract means from the posterior
    # --------------------------------------------------
    ke_prior_means = {}
    for ke_number in ke_values_ac50.keys():
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
        "ke_with_no_ac50Data": ke_with_no_ac50Data
    }
