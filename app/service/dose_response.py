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

            Examples:
            {"55": ["BSK_BT_xTNFa", "BSK_LPS_TNFa", "LTEA_HepaRG_BCL2"]}
            {"386": [{"gene":"CA1","ac50":"5","chemical":"Azoxystrobin"}]}

    Returns:
        dict: Results of the Bayesian dose-response, including KE likelihoods, etc.
    """

    # --------------------------------------------------
    # 1. Load your Excel data once (if not already)
    # --------------------------------------------------
    df, json_data = get_excel_data()
    with open('app/localDataFiles/chemNameToDsstoxid.json', 'r') as file:
        chem_to_dsstoxi = json.load(file)
    with open('app/localDataFiles/allAssays.json', 'r') as file2:
        all_assays_json = json.load(file2)
    with open('app/localDataFiles/testdata.json', 'r') as file3:
        testdata = json.load(file3)





    # --------------------------------------------------
    # 2. Helper: Get AC50 for a single assay from Excel/CSV
    # --------------------------------------------------
    def get_ac50_for_assay(assay_id, chemical_name):
        #testData looks like:
        """
        [
            {
                "aeid": 2574,
                "assayComponentEndpointName": "ERF_CR_ENZ_hELANE",
                "m4id": 1205680,
                "data": [
                    {
                        "ac50": 0.3839979849326894,
                        "dtxsid": "DTXSID8031077"
                    },
                    {
                        "ac50": 5,
                        "dtxsid": "DTXSID3041035"
                    },
                    {
                        "ac50": 9.338029682116078,
                        "dtxsid": "DTXSID00872663"
                    },
                    {
                        "ac50": 5,
                        "dtxsid": "DTXSID30865801"
                    }
                ]
            },
            """
        for item in testdata:
            if item['aeid'] == assay_id:
                for data in item['data']:
                    if data['dtxsid'] == chemical_name:
                        print("AC DATA HER: ", data['ac50'])
                        return data['ac50']
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
        """
        We might have:

          case A) assay_info_list = ["BSK_BT_xTNFa","BSK_LPS_TNFa",...]  (array of strings)
          case B) assay_info_list = [{"gene": "CA1", "ac50": "5", "chemical": "Azoxystrobin"}, ...]
        """
        if not assay_info_list:
            # If it's an empty list, nothing to do
            ke_avg_ac50[ke_number] = None
            continue

        # Identify whether the first item is a string (case A) or a dict (case B)
        first_item = assay_info_list[0]

        # We'll store all valid AC50 values for this KE in a list, then average them.
        ac50_values = []

        if isinstance(first_item, str):
            # --- Case A: array of assay names --- #
            for assay_name in assay_info_list:
                assay_aeid = None
                for item in all_assays_json:
                    if item['assayComponentEndpointName'] == assay_name:
                        assay_aeid = item['aeid']
                        break
                if assay_aeid is None:
                    print(f"Could not find aeid for assay '{assay_name}'")
                    return None

                ac50_val = get_ac50_for_assay(assay_aeid, dsstox_substance_id)
                if ac50_val is not None:
                    ac50_values.append(ac50_val)

        elif isinstance(first_item, dict):
            # --- Case B: array of objects that already contain AC50 --- #
            for obj in assay_info_list:
                # We assume each dict has { "ac50": "5", "chemical": "Azoxystrobin", ... }
                # If "chemical" must match the user-supplied chemical, check that here:
                if obj.get("chemical") == chemical:
                    ac50_str = obj.get("ac50")
                    try:
                        ac50_val = float(ac50_str)
                        ac50_values.append(ac50_val)
                    except (ValueError, TypeError):
                        print(f"[WARN] Could not convert '{ac50_str}' to float AC50.")
                else:
                    # If you only want to use matches for the same chemical
                    print(f"[INFO] Skipping object with different chemical: {obj.get('chemical')}")
        else:
            print(f"[WARN] Unexpected item type in ke_assay_dict for KE '{ke_number}'. Skipping.")
            ke_avg_ac50[ke_number] = None
            continue

        # Now average any found AC50 values
        if ac50_values:
            print("ac50_values", ac50_values)
            ac50_avg = sum(ac50_values) / len(ac50_values)
            #ac50_min_value = min(ac50_values)
            #ac50_median = np.median(ac50_values)
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
        # Create a Beta prior for each KE (regardless of AC50)
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
    # If a KE has likelihood=None, it means we skip it (like a factor of 1.0).
    valid_likelihoods = [lk for lk in ke_likelihoods.values() if lk is not None]
    if valid_likelihoods:
        P_AO_at_dose = np.prod(valid_likelihoods)
    else:
        # If we have no valid KE likelihoods, set this to 0 or some fallback
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
        if(v is not None):
            rounded_ke_likelihoods[k] = round(v, 3)
        else:
            rounded_ke_likelihoods[k] = None

    rounded_ke_prior_means = {
        k: round(v, 3) for k, v in ke_prior_means.items()
    }

    return {
        "dose": doseOfSubstance,
        "ke_likelihoods": rounded_ke_likelihoods,
        "probability_AO": round(P_AO_at_dose, 3),
        "activated_events": activated_events,
        "ke_prior_means": rounded_ke_prior_means,
        "ao_prior_mean": round(mean_prior_ao, 3),
    }
