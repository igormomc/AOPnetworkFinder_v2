import ast
import csv
import json
import logging
import os

import pandas as pd
import requests
from flask import render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

import app.security_config.input_validation as input_validation
import app.service.aop_visualizer_service as visualizer_sv
import app.service.aop_wiki_data_extraction_service as data_extraction_sv
import app.service.ke_degree_reader_service as ke_reader
from app import app
from . import cache
from .security_config.AopKeFormDataExctarctionValidation import AopKeFormDataExtractionValidation, \
    sanitize_form_extraction
from .security_config.AopKeFormValidation import AopKeFormValidation, sanitize_form
from .service.dose_response import run_dose_response
from .service.get_chemical_suggestions_for_AOP import get_chemical_suggestions_for_aop


def parse_list_string(value):
    """
    Attempts to parse a string that may represent a list.
    If it does, return a set of stripped items.
    Otherwise, return a set with the original stripped value.
    """
    try:
        parsed = ast.literal_eval(value)
        if isinstance(parsed, list):
            return {str(item).strip() for item in parsed if str(item).strip()}
        else:
            return {str(parsed).strip()}
    except Exception:
        return {value.strip()}


aopwiki_ke_info = []


def load_csv_data():
    global aopwiki_ke_info
    with open("app/localDataFiles/aopwiki_KE_info.csv", mode="r", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        aopwiki_ke_info = [row for row in reader]


# Load the CSV data when the application starts
load_csv_data()


# Page Routing
@app.route("/")
@app.route("/AOP_Visualizer")
def visualizer_page():
    return render_template('visualizer_page_one.html')


@app.route("/page1")
def page_two():
    return render_template('data_displayer_page_two.html')


@app.route("/page2")
def page_three():
    return render_template('part2.html')


# Post requests
@app.route("/searchAops", methods=['POST'])
def search_aops():
    unique_ke_set = set()
    tmp_ke_id_set = set()
    filtered_aop_list = []
    aop_list = []

    # Validate the form data
    form = AopKeFormValidation(formdata=request.form)

    if form.validate_on_submit():
        # Sanitize aop_query and ke_query forms
        sanitize_form(form)
        # Retrieve the query from the form
        aop_query = form.searchFieldAOP.data
        ke_query = form.searchFieldKE.data
        stressor_query = form.stressorDropdown.data
        organ_query = form.organDropdown.data
        life_stage_query = form.lifeStageDropdown.data
        sex_query = form.sexDropdown.data
        cell_query = form.cellValue.data
        taxonomy_query = form.taxValue.data

        gene_checkbox = request.form.get('checkboxGene')
        filter_development_chx = request.form.get('checkboxDevelopment')
        filter_endorsed_chx = request.form.get('checkboxEndorsed')
        filter_review_chx = request.form.get('checkboxReview')
        filter_approved_chx = request.form.get('checkboxApproved')
        ke_degree = request.form.get("keDegree")

        logging.debug(f"aop_query from the search field in front-end {aop_query}")

        # Attempt to retrieve the stressor list from cache
        stressors = cache.get('get_stressors')
        stressor_query_validation = False

        aop_query_list = aop_query.split(',')
        if stressors is None:
            # Cache miss, so fetch the stressors again and cache them
            stressors = visualizer_sv.get_all_stressors_from_aop_wiki()
            cache.set('get_stressors', stressors, timeout=6000)

        cells = cache.get('get_cells')
        if cells is None:
            cells = visualizer_sv.get_all_cells_from_aop_wiki()
            cache.set('get_cells', cells, timeout=6000)

        # Check if the submitted stressor is in the list of stressors
        if stressor_query in stressors:
            # Valid stressor submission
            stressor_query_validation = True

        # Input validation and sanitation
        aop_query_validation = input_validation.validate_aop_ke_inputs(aop_query)
        ke_query_validation = input_validation.validate_aop_ke_inputs(ke_query)

        if aop_query_validation is False and ke_query_validation is False and stressor_query_validation is False:
            return render_template('visualizer_page_one.html', data=None)

        # Handle if there is no data
        if aop_query is None and ke_query is None and stressor_query is None:
            return render_template('visualizer_page_one.html', data=None)

        if (ke_degree == '1' or ke_degree == '2') and ke_query != '':
            # ke_degree is either 1 or 2
            list_of_ke_ids = ke_query.split(',')
            unique_ke_set = ke_reader.read_ke_degree(ke_degree, list_of_ke_ids)
            if len(unique_ke_set) > 0:
                for ke_obj in unique_ke_set:
                    tmp_ke_id_set.add(ke_obj.get_ke_numerical_id())
            tmp_ke_id_list = list(tmp_ke_id_set)
            mie_json_ke = ke_reader.mie_json_sparql(tmp_ke_id_list)
            ao_json_ke = ke_reader.ao_json_sparql(tmp_ke_id_list)
            mie_set = ke_reader.mie_reader_json(mie_json_ke)
            ao_set = ke_reader.ao_reader_json(ao_json_ke)
            for ke_obj in unique_ke_set:
                for mie_id in mie_set:
                    if ke_obj.get_identifier() == mie_id:
                        ke_obj.set_mie()
                        break
                for ao_id in ao_set:
                    if ke_obj.get_identifier() == ao_id:
                        ke_obj.set_ao()
                        break
                if ke_obj.print_ke_type() == 'None, need to declare type of key event':
                    '''Ke type is KE'''
                    ke_obj.set_ke()
        else:
            aop_list = visualizer_sv.extract_all_aops_given_ke_ids(ke_query)

        # merge aop_list with aop_query
        aop_query_list.extend(aop_list)
        if len(aop_query_list) > 0:
            for aop_id in aop_query_list:
                all_filters_match = True
                if (len(life_stage_query) > 0):
                    all_filters_match = True
                    for life_stage in life_stage_query.split(','):
                        print("life_stage", life_stage)

                if (len(sex_query) > 0):
                    all_filters_match = True
                    for sex in sex_query.split(','):
                        print("sex", sex)

                if len(cell_query) > 0:
                    all_filters_match = False
                    for cell in cell_query.split(','):
                        if visualizer_sv.check_if_cell_exist_in_aop(aop_id, cell):
                            all_filters_match = True

                if len(taxonomy_query) > 0:
                    all_filters_match = True
                    for taxonomy in taxonomy_query.split(','):
                        print("taxonomy", taxonomy)

                if all_filters_match:
                    filtered_aop_list.append(aop_id)

            if len(filtered_aop_list) == 0:
                return render_template('visualizer_page_one.html', data=None)

        aop_query_list = aop_query.split(',')
        aop_stressor_list = visualizer_sv.extract_all_aop_id_from_given_stressor_name(stressor_query)
        aop_list.extend(aop_query_list)
        aop_list.extend(aop_stressor_list)
        # Remove empty strings
        aop_list_filtered = [aop for aop in filtered_aop_list if aop != '']

        if len(aop_list_filtered) == 0 and len(unique_ke_set) > 0:
            aop_cytoscape, aop_after_filter = visualizer_sv.visualize_only_ke_degrees(unique_ke_set)
        else:
            aop_cytoscape, aop_after_filter = visualizer_sv.visualize_aop_user_input(aop_list_filtered, gene_checkbox,
                                                                                     filter_development_chx,
                                                                                     filter_endorsed_chx,
                                                                                     filter_review_chx,
                                                                                     filter_approved_chx, unique_ke_set)
        if aop_cytoscape is None:
            # Happens if all the aops the user inputted gets filtered out.
            return render_template('visualizer_page_one.html', data=None)

        # Similarity check
        unique_ke = visualizer_sv.find_all_ke_from_json(aop_cytoscape)
        ke_merge_possiblity = visualizer_sv.merge_activation(unique_ke)

        ke_list = []
        print("unique_ke:", unique_ke)

        for node in aop_cytoscape['elements']['nodes']:
            data = node.get('data', {})
            label = data.get('label', None)
            # Only add labels that start with "KE"
            if label and label.startswith("KE"):
                ke_list.append(label)

        organ_set = set()
        sex_set = set()
        lifestage_set = set()
        for row in aopwiki_ke_info:
            index_value = row["index"].strip()
            if index_value in ke_list:
                # Process organ field
                organ_field = row["organ"].strip()
                if organ_field:
                    try:
                        parsed = ast.literal_eval(organ_field)
                        if isinstance(parsed, list):
                            for organ in parsed:
                                organ_set.add(organ.strip())
                        else:
                            organ_set.add(organ_field)
                    except Exception:
                        organ_set.add(organ_field)

                # Process sex field
                sex_field = row["sex"].strip()
                if sex_field:
                    try:
                        parsed = ast.literal_eval(sex_field)
                        if isinstance(parsed, list):
                            for sex in parsed:
                                sex_set.add(sex.strip())
                        else:
                            sex_set.add(sex_field)
                    except Exception:
                        sex_set.add(sex_field)

                # Process lifestage field
                lifestage_field = row["lifestage"].strip()
                if lifestage_field:
                    try:
                        parsed = ast.literal_eval(lifestage_field)
                        if isinstance(parsed, list):
                            for stage in parsed:
                                lifestage_set.add(stage.strip())
                        else:
                            lifestage_set.add(lifestage_field)
                    except Exception:
                        lifestage_set.add(lifestage_field)

        # Convert sets to lists if needed
        organ_list_final = list(organ_set)
        sex_list_final = list(sex_set)
        lifestage_list_final = list(lifestage_set)

        print("organ_set", organ_list_final)
        print("sex", sex_list_final)
        print("lifestage", lifestage_list_final)
        final_response = {
            'elements': aop_cytoscape['elements'],
            'merge_options:': ke_merge_possiblity,
            'aop_before_filter': aop_list_filtered,
            'aop_after_filter': aop_after_filter,
            'organ_set': organ_list_final,
            'sex_set': sex_list_final,
            'lifestage_set': lifestage_list_final,

        }
        json_result = jsonify(final_response)
        print("json_result:::::::", final_response)
        return json_result
    return render_template('visualizer_page_one.html', data=None)


@app.route("/data-extraction-submit", methods=['POST'])
def extract_from_aop_wiki():
    form = AopKeFormDataExtractionValidation(formdata=request.form)
    if form.validate_on_submit():
        aop_input = form.searchFieldAOPs.data
        ke_input = form.searchFieldKEs.data
        sanitize_form_extraction(form)

        if aop_input == '':
            ke_list_tuple = [("In AOP", request.form.get("ke_chx_in_aop")),
                             ("ke stressor", request.form.get("ke_chx_stressor")),
                             ("ke genes", request.form.get("ke_chx_genes")),
                             ("ke cell type context", request.form.get("ke_chx_cell_type")),
                             ("ke description", request.form.get("ke_chx_description")),
                             ("ke measurements", request.form.get("ke_chx_measurements"))]

            json_file, column_header = data_extraction_sv.query_sparql(ke_list_tuple, aop_input, ke_input)

            return jsonify(json_file)
        else:
            aop_list_tuple = [("abstract", request.form.get("aop_chx_abstract")),
                              ("stressor", request.form.get("aop_chx_stressor")),
                              ("ke", request.form.get("aop_chx_ke")),
                              ("mie", request.form.get("aop_chx_mie")),
                              ("ao", request.form.get("aop_chx_ao")),
                              ("KE Genes", request.form.get("aop_chx_ke_genes")),
                              ("aop_author", request.form.get("aop_chx_author"))]

            json_file, column_header = data_extraction_sv.query_sparql(aop_list_tuple, aop_input, ke_input)

            return jsonify(json_file)
    return render_template('data_displayer_page_two.html', data=None)


@app.route('/get_stressors')
@cache.cached(timeout=6000)
def get_stressors():
    # Populate data with stressor name
    stressor_list = visualizer_sv.get_all_stressors_from_aop_wiki()

    return jsonify(stressor_list)


@app.route('/get_cells')
@cache.cached(timeout=6000)
def get_cells():
    # Populate data with stressor name
    cell_list = visualizer_sv.get_all_cells_from_aop_wiki()

    return jsonify(cell_list)


@app.route('/get_organs', methods=['POST'])
@cache.cached(timeout=6000)
def get_organs():
    # Expect a JSON body with a key "ids" that contains a list of IDs.
    data = request.get_json()
    id_list = data.get("ids")
    if not id_list or not isinstance(id_list, list):
        return jsonify({"error": "Please provide a list of IDs in the 'ids' field."}), 400

    # Load the CSV file; adjust the path if necessary.
    try:
        df = pd.read_csv('aopwiki_KE_info.csv')
    except Exception as e:
        return jsonify({"error": f"Could not read CSV file: {str(e)}"}), 500

    # Filter the DataFrame rows by the provided IDs.
    # Then, filter out rows where the 'organ' column is empty or missing.
    df_filtered = df[df['index'].isin(id_list)]
    df_filtered = df_filtered[df_filtered['organ'].notna() & (df_filtered['organ'] != "")]

    # Extract unique organs from the filtered rows.
    organs = df_filtered['organ'].unique().tolist()

    return jsonify(organs)


@app.route('/get_taxonomies')
@cache.cached(timeout=6000)
def get_taxonomies():
    taxonomy_list = visualizer_sv.get_all_taxonomies_from_aop_wiki()

    return jsonify(taxonomy_list)


@app.route('/get_sexes')
@cache.cached(timeout=6000)
def get_sexes():
    sex_list = visualizer_sv.get_all_sex_from_aop_wiki()
    return jsonify(sex_list)


@app.route('/get_life_stages')
@cache.cached(timeout=6000)
def get_life_stages():
    life_stage_list = visualizer_sv.get_all_life_stage_from_aop_wiki()
    return jsonify(life_stage_list)


@app.route('/download/<filename>')
def download_style_file(filename):
    filename = secure_filename(filename)
    directory = "static/cytoscape_style_template"
    return send_from_directory(directory, filename, as_attachment=True)


ASSAY_CACHE = None
ENRICH_GENES_CACHE = None


def fetch_bioactivity_assays_intern():
    global ASSAY_CACHE
    if ASSAY_CACHE:
        return ASSAY_CACHE
    EPA_API_URL = "https://api-ccte.epa.gov/bioactivity/assay/"
    HEADERS = {
        'Accept': 'application/hal+json',
        'x-api-key': os.getenv('EPA_API_KEY')
    }
    try:
        response = requests.get(EPA_API_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        ASSAY_CACHE = data
        return data
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500  # Return error message with 500 status code


@app.route('/api/bioactivity-assays', methods=['GET'])
def fetch_bioactivity_assays():
    global ASSAY_CACHE
    if ASSAY_CACHE:
        return jsonify(ASSAY_CACHE)
    EPA_API_URL = "https://api-ccte.epa.gov/bioactivity/assay/"
    HEADERS = {
        'Accept': 'application/hal+json',
        'x-api-key': os.getenv('EPA_API_KEY')
    }

    #stop if an api key is not specified
    if os.getenv('EPA_API_KEY'):
        try:
            response = requests.get(EPA_API_URL, headers=HEADERS)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            ASSAY_CACHE = data
            return jsonify(data)  # Serve the data as JSON
        except requests.exceptions.RequestException as e:
            return jsonify({'error': str(e)}), 401  # Return error message with 500 status code
    else:
        return jsonify({'error': 'ToxCast API key not specified.'}), 401

@app.route('/api/dose_response', methods=['POST'])
def dose_response():
    data = request.get_json()

    # Process ke_assay_list: if it's a string, try converting it to a dict.
    ke_assay_dict = data.get('ke_assay_list')
    if isinstance(ke_assay_dict, str):
        try:
            ke_assay_dict = json.loads(ke_assay_dict)
        except Exception as e:
            return jsonify({'error': f'Invalid ke_assay_list data: {str(e)}'}), 400

    # Convert doseOfSubstance to float, with error handling.
    try:
        doseOfSubstance = float(data.get('doseOfSubstance'))
    except (TypeError, ValueError) as e:
        return jsonify({'error': f'Invalid doseOfSubstance: {str(e)}'}), 400

    # Make sure that chemical is provided.
    chemical = data.get('chemical')
    if chemical is None:
        return jsonify({'error': 'Missing required field: chemical'}), 400

    handleDataNodesMode = data.get('handleNoneDataNodesMode')
    aop_id = data.get('aop_id')

    organFilter = data.get('organFilter')
    lifeStageFilter = data.get('lifeStageFilter')
    sexFilter = data.get('sexFilter')
    taxonomyFilter = data.get('taxonomyFilter')
    manualKEPaths = data.get('manualKEPaths')
    manualKEEdges = []

    for source, targets in manualKEPaths.items():
        source_clean = source.replace("KE ", "")
        for target in targets:
            target_clean = target.replace("KE ", "")
            manualKEEdges.append((source_clean, target_clean))

    print("organFilter:", organFilter)
    print("lifeStageFilter:", lifeStageFilter)
    print("sexFilter:", sexFilter)
    print("taxonomyFilter::", taxonomyFilter)

    print("-------------------------")
    print("ke_assay_dict::::", ke_assay_dict)
    print("doseOfSubstance:", doseOfSubstance)
    print("chemical:", chemical)
    print("handleDataNodesMode:", handleDataNodesMode)
    print("manualKEPaths::", manualKEEdges)
    print("-------------------------")

    results = run_dose_response(doseOfSubstance, chemical, ke_assay_dict, handleDataNodesMode, aop_id, manualKEEdges)

    print("results:::::::::", results)
    return jsonify(results)


@app.route('/api/get_chemical_suggestions', methods=['GET'])
def get_chemical_suggestions():
    """
    Endpoint to return a list of chemical suggestions based on the query string.
    """
    aop_id = request.args.get('aop_id')
    result = get_chemical_suggestions_for_aop(aop_id)
    return jsonify(result)


def gene_enrichment2():
    global ENRICH_GENES_CACHE
    if ENRICH_GENES_CACHE:
        return ENRICH_GENES_CACHE

    with open('app/localDataFiles/curated_kegene.json') as f:
        data = json.load(f)
        ENRICH_GENES_CACHE = data
        return data


@app.route('/api/gene_enrichment', methods=['GET'])
def gene_enrichment():
    emptyKeEventsValues = request.args.get('keList').split(',')

    ke_to_genes = gene_enrichment2()  # Now returns a dictionary
    assaysIntern = fetch_bioactivity_assays_intern()

    results = {}
    for ke in emptyKeEventsValues:
        keName = 'KE' + ke
        genes = ke_to_genes.get(keName, [])
        matching_assays = []

        for gene in genes:
            for assay in assaysIntern:
                assay_gene = (assay.get("gene") or {}).get("geneSymbol", "")
                if assay_gene and assay_gene.upper() == gene.upper():
                    assay_endpoint = assay.get("assayComponentEndpointName")
                    if assay_endpoint and assay_endpoint not in matching_assays:
                        matching_assays.append(assay_endpoint)

        if matching_assays:
            results[ke] = {
                "KE": ke,
                "assays": matching_assays
            }
        else:
            results[ke] = None

    print("Gene Enrichment Results::::::", results)
    return jsonify(results)


@app.route('/api/read_assays_domainApp', methods=['GET'])
def read_assays_domainApp():
    file_path = 'app/localDataFiles/organism_organ_doa.csv'
    try:
        with open(file_path, mode='r', newline='', encoding='utf8') as csvfile:
            # DictReader automatically uses the first row as the header row
            reader = csv.DictReader(csvfile)
            data = [row for row in reader]
            # Convert to JSON
            json_data = json.dumps(data)
            return json_data
    except Exception as e:
        logging.error(f"Error reading the CSV file: {e}")
        return jsonify({'error': 'Failed to read the CSV file'}), 500
