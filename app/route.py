import json
import logging
import os

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

        organs = cache.get('get_organs')
        if organs is None:
            organs = visualizer_sv.get_all_organs_from_aop_wiki()
            cache.set('get_organs', organs, timeout=6000)

        taxonomies = cache.get('get_taxonomies')
        if taxonomies is None:
            taxonomies = visualizer_sv.get_all_taxonomies_from_aop_wiki()
            cache.set('get_taxonomies', taxonomies, timeout=6000)

        sexes = cache.get('get_sexes')
        if sexes is None:
            sexes = visualizer_sv.get_all_sex_from_aop_wiki()
            cache.set('get_sexes', sexes, timeout=6000)

        lifeStages = cache.get('get_life_stages')
        if lifeStages is None:
            lifeStages = visualizer_sv.get_all_life_stage_from_aop_wiki()
            cache.set('get_life_stages', lifeStages, timeout=6000)

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
                    all_filters_match = False
                    for life_stage in life_stage_query.split(','):
                        if visualizer_sv.check_if_life_stage_exist_in_aop(aop_id, life_stage):
                            all_filters_match = True

                if (len(sex_query) > 0):
                    all_filters_match = False
                    for sex in sex_query.split(','):
                        if visualizer_sv.check_if_sex_exist_in_aop(aop_id, sex):
                            all_filters_match = True

                if (len(organ_query) > 0):
                    all_filters_match = False
                    for organ in organ_query.split(','):
                        if visualizer_sv.check_if_organ_exist_in_aop(aop_id, organ):
                            all_filters_match = True

                if len(cell_query) > 0:
                    all_filters_match = False
                    for cell in cell_query.split(','):
                        if visualizer_sv.check_if_cell_exist_in_aop(aop_id, cell):
                            all_filters_match = True

                if len(taxonomy_query) > 0:
                    all_filters_match = False
                    for taxonomy in taxonomy_query.split(','):
                        if visualizer_sv.check_if_taxonomic_exist_in_aop(aop_id, taxonomy):
                            all_filters_match = True

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

        final_response = {
            'elements': aop_cytoscape['elements'],
            'merge_options:': ke_merge_possiblity,
            'aop_before_filter': aop_list_filtered,
            'aop_after_filter': aop_after_filter
        }
        json_result = jsonify(final_response)
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


@app.route('/get_organs')
@cache.cached(timeout=6000)
def get_organs():
    # Populate data with stressor name
    organ_list = visualizer_sv.get_all_organs_from_aop_wiki()

    return jsonify(organ_list)


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
    try:
        response = requests.get(EPA_API_URL, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes
        data = response.json()
        ASSAY_CACHE = data
        return jsonify(data)  # Serve the data as JSON
    except requests.exceptions.RequestException as e:
        return jsonify({'error': str(e)}), 500  # Return error message with 500 status code


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

    print("-------------------------")
    print("ke_assay_dict:", ke_assay_dict)
    print("doseOfSubstance:", doseOfSubstance)
    print("chemical:", chemical)
    print("handleDataNodesMode:", handleDataNodesMode)
    print("-------------------------")

    results = run_dose_response(doseOfSubstance, chemical, ke_assay_dict, handleDataNodesMode, aop_id)

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

    with open('app/localDataFiles/GenesToKe_minified.json') as f:
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

    print("Gene Enrichment Results:", results)
    return jsonify(results)
