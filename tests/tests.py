import unittest

from app import app


class BaseTestCase(unittest.TestCase):
    """
    Base test case to set up the common test client configuration.
    """

    def setUp(self):
        # Enable testing mode for the Flask application.
        app.config['TESTING'] = True
        self.client = app.test_client()


# -----------------------------------------------------------------------------
# Dose Response Endpoint Tests
# -----------------------------------------------------------------------------
class TestDoseResponseEndpoint(BaseTestCase):
    """
    Tests for the /api/dose_response endpoint.
    """

    def setUp(self):
        """
        Set up test configuration for dose response endpoint tests.
        Disables CSRF for testing purposes.
        """
        super().setUp()
        app.config['WTF_CSRF_ENABLED'] = False

    def test_dose_response(self):
        # Prepare test payload
        payload = {
            "doseOfSubstance": 100,
            "chemical": "Phenolphthalein",
            "ke_assay_list": {
                "55": ["BSK_BT_xTNFa", "BSK_LPS_TNFa", "LTEA_HepaRG_BCL2"],
                "188": ["BSK_BT_xTNFa", "BSK_LPS_TNFa", "BSK_BT_xIL6", "LTEA_HepaRG_IL6", "BSK_CASM3C_IL6"],
                "386": None,
                "1392": ["LTEA_HepaRG_CAT"],
                "1487": None,
                "1488": None,
                "1492": ["BSK_BT_xTNFa", "BSK_LPS_TNFa", "BSK_BT_xIL6", "LTEA_HepaRG_IL6", "BSK_CASM3C_IL6"],
                "1493": [
                    "BSK_BT_xIL17A", "BSK_BT_xIL2", "BSK_BT_xIL6", "LTEA_HepaRG_IL6", "BSK_CASM3C_IL6",
                    "BSK_BF4T_MCP1", "BSK_hDFCGF_MCP1", "BSK_IMphg_MCP1", "BSK_3C_MCP1", "BSK_4H_MCP1",
                    "BSK_CASM3C_IL6", "BSK_KF3CT_MCP1", "BSK_LPS_MCP1", "BSK_SAg_MCP1", "ATG_C_EBP_CIS",
                    "BSK_MyoF_IL8", "BSK_BF4T_IL8", "BSK_BE3C_IL8", "BSK_KF3CT_IL8", "BSK_IMphg_IL8",
                    "BSK_3C_IL8", "BSK_CASM3C_IL8", "BSK_hDFCGF_IL8", "BSK_LPS_IL8", "BSK_SAg_IL8"
                ],
                "1538": [
                    "ERF_CR_NR_binding_hGR", "CEETOX_H295R_11DCORT_noMTC", "CEETOX_H295R_CORTIC_noMTC",
                    "CEETOX_H295R_CORTISOL_noMTC", "CEETOX_H295R_DOC_noMTC", "ATG_GRE_CIS", "NVS_NR_hGR",
                    "ATG_GR_TRANS", "TOX21_GR_BLA_Agonist_ratio", "TOX21_GR_BLA_Antagonist_ratio",
                    "CEETOX_H295R_11DCORT", "CEETOX_H295R_CORTIC", "CEETOX_H295R_CORTISOL", "CEETOX_H295R_DOC"
                ]
            },
            "handleNoneDataNodesMode": "toggleMedian",
            "aop_id": "17"
        }

        # Send the POST request
        response = self.client.post('/api/dose_response', json=payload)
        self.assertEqual(response.status_code, 200, "Expected status code 200 for dose response endpoint")

        data = response.get_json()
        self.assertIsInstance(data, dict, "Response should be a dictionary")

        # Check that the top-level keys are present
        for key in ['dose', 'ke_with_no_ac50Data', 'AOP']:
            self.assertIn(key, data, f"Response should include '{key}'")

        # Validate the dose value
        self.assertEqual(data['dose'], 100.0, "Dose should be 100.0")

        # Validate ke_with_no_ac50Data
        expected_no_ac50_data = {
            "1487": "True",
            "1488": "True",
            "386": "True"
        }
        self.assertEqual(data['ke_with_no_ac50Data'], expected_no_ac50_data,
                         "ke_with_no_ac50Data should match the expected dictionary")

        # Validate the structure of the AOP section
        aop = data['AOP']
        expected_aop_keys = {"AO0", "KE1", "KE2", "KE3", "KE4", "KE5", "KE6", "KE7", "KE8", "MIE0"}
        self.assertEqual(set(aop.keys()), expected_aop_keys, "AOP keys do not match expected keys")

        # For example, validate the MIE0 entry
        mie0 = aop.get('MIE0')
        self.assertIsNotNone(mie0, "MIE0 should be present in AOP")
        for field in ['AC50', 'KE_id', 'P(prior|event)', 'connections', 'cumulative probability', 'genes', 'name']:
            self.assertIn(field, mie0, f"MIE0 should include '{field}'")

        # Validate specific values in MIE0 (if these are known)
        self.assertEqual(mie0['KE_id'], "1487", "MIE0 KE_id should be '1487'")
        self.assertAlmostEqual(mie0['AC50'], 20.0, msg="MIE0 AC50 should be 20.0")
        self.assertAlmostEqual(mie0['P(prior|event)'], 0.8333333333333334, places=5,
                               msg="MIE0 probability should be approximately 0.83333")

    def test_invalid_dose_value(self):
        """
        Test that a POST request with an invalid dose value (non-numeric) returns a 400 status code
        and that the error message is present in the response JSON.
        """
        payload = {
            "doseOfSubstance": "not_a_number",
            "chemical": "Phenolphthalein",
            "ke_assay_list": {"55": ["BSK_BT_xTNFa", "BSK_LPS_TNFa"]},
            "handleNoneDataNodesMode": "toggleMedian",
            "aop_id": "17"
        }
        response = self.client.post('/api/dose_response', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)

    def test_missing_required_field_doseOfSubstance(self):
        """
        Test that a POST request missing the required 'doseOfSubstance' field returns a 400 status code
        and that an error message is provided in the response JSON.
        """
        payload = {
            "chemical": "Phenolphthalein",
            "ke_assay_list": {"55": ["BSK_BT_xTNFa", "BSK_LPS_TNFa"]},
            "handleNoneDataNodesMode": "toggleMedian",
            "aop_id": "17"
        }
        response = self.client.post('/api/dose_response', json=payload)
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn("error", data)


# -----------------------------------------------------------------------------
# Other Smaller Endpoints Tests
# -----------------------------------------------------------------------------
class TestOtherEndpoints(BaseTestCase):
    """
    Tests for various other endpoints in the application.
    """

    def setUp(self):
        """
        Set up test configuration for other endpoints.
        Ensures exceptions are handled during testing.
        """
        super().setUp()
        app.config['PROPAGATE_EXCEPTIONS'] = False

    def test_get_cells(self):
        """
        Test that GET /get_cells returns a 200 status code and a non-empty dictionary.
        """
        response = self.client.get('/get_cells')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(len(data) > 0, "The cells endpoint should return a non-empty dictionary.")

    def test_get_organs(self):
        """
        Test that GET /get_organs returns a 200 status code and a non-empty dictionary.
        """
        response = self.client.get('/get_organs')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(len(data) > 0, "The organs endpoint should return a non-empty dictionary.")

    def test_get_taxonomies(self):
        """
        Test that GET /get_taxonomies returns a 200 status code and a non-empty dictionary.
        """
        response = self.client.get('/get_taxonomies')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(len(data) > 0, "The taxonomies endpoint should return a non-empty dictionary.")

    def test_get_sexes(self):
        """
        Test that GET /get_sexes returns a 200 status code and a list or dictionary.
        """
        response = self.client.get('/get_sexes')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(isinstance(data, list) or isinstance(data, dict),
                        "The sexes endpoint should return a list or a dictionary.")

    def test_get_life_stages(self):
        """
        Test that GET /get_life_stages returns a 200 status code and a non-empty dictionary.
        """
        response = self.client.get('/get_life_stages')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict)
        self.assertTrue(len(data) > 0, "The life stages endpoint should return a non-empty dictionary.")

    def test_get_chemical_suggestions(self):
        """
        Test that GET /api/get_chemical_suggestions with query parameter aop_id returns a 200 status code
        and a list of chemical suggestions that is 3 elements or fewer.
        """
        response = self.client.get('/api/get_chemical_suggestions', query_string={'aop_id': '17'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, list)
        if data:
            self.assertTrue(len(data) == 3 or len(data) < 3,
                            "Chemical suggestions should be 3 elements or fewer if not enough chemicals.")

    def test_gene_enrichment_valid(self):
        """
        Test that GET /api/gene_enrichment with valid keList query parameter returns a 200 status code
        and that the response contains the expected structure for each key.
        """
        response = self.client.get('/api/gene_enrichment', query_string={'keList': '386,1487,1488'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIsInstance(data, dict, "Expected response to be a dictionary.")
        for ke in ['386', '1487', '1488']:
            self.assertIn(ke, data, f"Response should include key '{ke}'.")
            if data[ke] is not None:
                self.assertIsInstance(data[ke], dict, f"Value for key '{ke}' should be a dictionary.")
                self.assertIn("KE", data[ke], f"Dictionary for key '{ke}' should contain a 'KE' field.")
                self.assertIn("assays", data[ke], f"Dictionary for key '{ke}' should contain an 'assays' field.")
                self.assertIsInstance(data[ke]["assays"], list, f"'assays' for key '{ke}' should be a list.")


if __name__ == "__main__":
    unittest.main()
