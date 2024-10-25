import logging
from collections import defaultdict
import networkx
import app.SPARQL_QUERIES.visualizer_queries as sq
import app.model.aop as aop
import app.service.plot_aop_service as plot_aop
import re
import textdistance


def visualize_aop_user_input(aop_ids, checkbox_gene, under_development_chx, endorsed_chx, under_review_chx,
                             approved_chx, existing_ke_objects):
    list_of_aop_objects = []
    list_of_ke_objects = []
    list_ke_objects = list(existing_ke_objects)
    # list_of_ke_objects = []
    if len(list_ke_objects) > 0:
        for ke_object in list_ke_objects:
            ke_id = str(ke_object.get_ke_numerical_id())
            list_of_ke_objects.append((ke_object, ke_id))

    genesCheckedFlag = checkbox_gene == '1'  # Will be false if it's not 1
    # TODO: Temporarily hardcoded in, making some adjustments in front end
    genesCheckedFlag = True
    under_development_flag = under_development_chx == '1'
    endorsed_flag = endorsed_chx == '1'
    under_review_flag = under_review_chx == '1'
    approved_flag = approved_chx == '1'

    # remove duplicates
    set_of_unique_aops = set(aop_ids)

    only_valid_aops = filter_aops(under_development_flag, endorsed_flag, under_review_flag, approved_flag)
    # return None if no aops are valid and some filter has been checked
    if any([under_development_flag, endorsed_flag, under_review_flag, approved_flag]) and not only_valid_aops:
        return None, []

    if len(only_valid_aops) != 0:
        # Filter the list of aops
        filtered_aop_list = {x for x in set_of_unique_aops if x in only_valid_aops}
        # if filtered_aop_list is empty, the aops that the user requested was filtered out. return none and do nothing
        if len(filtered_aop_list) == 0:
            return None, []
        # update set_of_unique_aops with filtred aops
        set_of_unique_aops = filtered_aop_list

    # One AOP
    if len(set_of_unique_aops) == 1:
        #logging.error(f"set_of_unique_aops: {sq.aop_dump(next(iter(set_of_unique_aops)))}")

        aop_rdf_data = sq.aop_dump(next(iter(set_of_unique_aops)))
        if len(aop_rdf_data['results']['bindings']) != 0:
            tmp_aop = aop.aop(aop_rdf_data, list_of_ke_objects, False)
            list_of_aop_objects.append(tmp_aop)

            aop_networkx_graph = plot_aop.plot(list_of_aop_objects, list_of_ke_objects)

            relabeled_graph = plot_aop.ke_obj_to_str(aop_networkx_graph, genesCheckedFlag)

            # can convert the networkx graph to a valid Cytoscape graph. Which is used to display the graph to the user in the front-end
            aop_cytoscape = networkx.cytoscape_data(relabeled_graph)
            return aop_cytoscape, list(set_of_unique_aops)
    elif len(set_of_unique_aops) >= 1:

        return visualize_multiple_aops_v2(set_of_unique_aops, genesCheckedFlag, list_of_ke_objects), list(
            set_of_unique_aops)

    return None, []


def visualize_only_ke_degrees(existing_ke_objects):
    list_of_aop_objects = []
    list_of_ke_objects = []
    list_ke_objects = list(existing_ke_objects)
    # list_of_ke_objects = []
    if len(list_ke_objects) > 0:
        for ke_object in list_ke_objects:
            ke_id = str(ke_object.get_ke_numerical_id())
            list_of_ke_objects.append((ke_object, ke_id))

    # One AOP
    if len(existing_ke_objects) > 0:
        aop_networkx_graph = plot_aop.plot(list_of_aop_objects, list_of_ke_objects)
        relabeled_graph = plot_aop.ke_obj_to_str(aop_networkx_graph, False)

        # can convert the networkx graph to a valid Cytoscape graph. Which is used to display the graph to the user in the front-end
        aop_cytoscape = networkx.cytoscape_data(relabeled_graph)
        return aop_cytoscape, []

    return None, []


# function for filtering out aop_ids, depending on the checked values in the filtering section of the application.
def filter_aops(under_development_chx, endorsed_chx, under_review_chx, approved_chx):
    """AOP Filter RDF - give aop filter list values"""
    only_valid_aops = []
    list_of_statuses = []

    if under_development_chx:
        list_of_statuses.append('Under Development')
    if endorsed_chx:
        list_of_statuses.append('WPHA/WNT Endorsed')
    if under_review_chx:
        list_of_statuses.append('EAGMST Under Review')
    if approved_chx:
        list_of_statuses.append('EAGMST Approved')

    # If list of statuses still is empty, return empty list and dont do any filtering
    if len(list_of_statuses) == 0:
        return list_of_statuses

    json_aop_filter = sq.aop_status(list_of_statuses)

    '''Regex pattern for only numbers (extract AOP ID)'''
    pattern = r"\d+"

    for aop_data in json_aop_filter['results']['bindings']:
        '''Extract AOP ID from json file using regex'''
        match = re.search(pattern, aop_data['aop_id']['value'])
        aop_id_string = match.group()

        only_valid_aops.append(aop_id_string)

    return only_valid_aops


# DEPRECATED
def visualize_multiple_aops(set_of_unique_aops, genesCheckedFlag):
    aop_rdf_data = sq.multiple_aop_dump(set_of_unique_aops)
    list_of_aop_objects = []
    list_of_unique_ke = []
    for x in set_of_unique_aops:
        # TODO: Dont use aop_dump use multiple_aop_dump instead on final version
        tmp_aop_date = sq.aop_dump(x)
        if len(aop_rdf_data['results']['bindings']) != 0:
            new_aop = aop.aop(tmp_aop_date, list_of_unique_ke, False)
            list_of_aop_objects.append(new_aop)

    aop_networkx_graph = plot_aop.plot(list_of_aop_objects, list_of_unique_ke)

    relabeled_graph = plot_aop.ke_obj_to_str(aop_networkx_graph, genesCheckedFlag)

    # can convert the networkx graph to a valid Cytoscape graph. Which is used to display the graph to the user in the front-end
    aop_cytoscape = networkx.cytoscape_data(relabeled_graph)
    return aop_cytoscape


def visualize_multiple_aops_v2(set_of_unique_aops, genesCheckedFlag, existing_ke_objects):
    aop_rdf_data = sq.multiple_aop_dump(set_of_unique_aops)
    list_of_aop_objects = []
    list_of_unique_ke = []
    if len(existing_ke_objects) > 0:
        list_of_unique_ke = existing_ke_objects
    # Initialize a dictionary to group entries by AOP identifier
    grouped_by_aop = defaultdict(
        lambda: {"head": aop_rdf_data["head"], "results": {"distinct": False, "ordered": True, "bindings": []}})

    # Iterate over each entry in the 'bindings' list
    for entry in aop_rdf_data['results']['bindings']:
        # Extract the AOP identifier from the entry
        aop_id = entry['AOP']['value'].split('/')[-1]  # Extracts the AOP ID
        grouped_by_aop[aop_id]["results"]["bindings"].append(entry)

    for aop_data in grouped_by_aop:
        # initiate aops
        new_aop_object = aop.aop(grouped_by_aop[aop_data], list_of_unique_ke, False)
        list_of_aop_objects.append(new_aop_object)

    aop_networkx_graph = plot_aop.plot(list_of_aop_objects, list_of_unique_ke)

    relabeled_graph = plot_aop.ke_obj_to_str(aop_networkx_graph, genesCheckedFlag)

    # can convert the networkx graph to a valid Cytoscape graph. Which is used to display the graph to the user in the front-end
    aop_cytoscape = networkx.cytoscape_data(relabeled_graph)

    return aop_cytoscape


def merge_activation(unique_key_events):
    '''Merge button activation,
    After generating an AOP/AOP-networks, compare every unique KE with eachother using levenshtein distance
    If the distance is less than 7, activate the button and give the user the option to merge/not merge the KE.'''
    set_matched_tuples = set()
    algo = textdistance.Levenshtein()

    for outer_node in unique_key_events:
        for inner_node in unique_key_events:
            if outer_node == inner_node:
                # skip because we are comparing the same node.
                continue

            lev_distance = algo.distance(outer_node.lower(), inner_node.lower())

            if lev_distance < 7:
                '''Found a possible match, append the ke object'''
                ordered_tuple = tuple(sorted((outer_node, inner_node)))
                set_matched_tuples.add((ordered_tuple[0], ordered_tuple[1]))
    # convert set to list, as json serialization doesnt support sets
    list_matched_tuples = list(set_matched_tuples)
    return list_matched_tuples


def find_all_ke_from_json(json_string):
    ke_from_json = set()

    for node in json_string["elements"]["nodes"]:
        if node["data"]["ke_type"] != 'genes':
            ke_from_json.add(node["data"]["name"])

    return ke_from_json


def extract_all_aops_given_ke_ids(ke_ids):
    ke_ids_split = ke_ids.split(',')
    ke_json = sq.ke_get_aopid(ke_ids_split)
    aop_id = [x['aop_id'] for x in ke_json['results']['bindings']]
    aop_id_2 = [x['value'] for x in aop_id]

    # extract AOP ids
    pattern_id = re.compile(r'\d+')
    aop_ids = [pattern_id.search(x).group() for x in aop_id_2 if pattern_id.search(x)]
    return aop_ids


def get_all_stressors_from_aop_wiki():
    list_of_stressors = []
    # query
    stressor_dict = sq.stressor_dump()
    for x in stressor_dict['results']['bindings']:
        # append to list_of_stressors
        list_of_stressors.append(x['str_title']['value'])
    return list_of_stressors

def get_all_cells_from_aop_wiki():
    list_of_cells = []
    # query
    cell_dict = sq.cell_dump()
    #print("cell_dict", cell_dict)
    for x in cell_dict['results']['bindings']:
        # append to list_of_stressors
        list_of_cells.append(x['cell_title']['value'])
    return list_of_cells

def get_all_organs_from_aop_wiki():
    list_of_organs = []
    # query
    organ_dict = sq.organ_dump()
    for x in organ_dict['results']['bindings']:
        # append to list_of_stressors
        list_of_organs.append(x['organ_title']['value'])
    return list_of_organs

def get_all_taxonomies_from_aop_wiki():
    list_of_taxonomic = []
    # query
    taxonomic_dict = sq.taxonomic_dump()
    for x in taxonomic_dict['results']['bindings']:
        # append to list_of_stressors
        list_of_taxonomic.append(x['tax_title']['value'])
    return list_of_taxonomic

def get_all_sex_from_aop_wiki():
    list_of_sex = []
    # query
    sex_dict = sq.sex_dump()
    #print(sex_dict)
    for x in sex_dict['results']['bindings']:
        list_of_sex.append(x['sexObject']['value'])
    return list_of_sex

def get_all_life_stage_from_aop_wiki():
    list_of_life_stage = []
    # query
    life_stage_dict = sq.lifeStage_dump()
    for x in life_stage_dict['results']['bindings']:
        list_of_life_stage.append(x['lifeStageObject']['value'])
    return list_of_life_stage


def extract_all_aop_id_from_given_stressor_name(stressor_name):
    aop_ids = []

    if stressor_name == '' or stressor_name is None:
        return aop_ids

    stressor_json = sq.stressor_AOP_finder(stressor_name)

    if len(stressor_json['results']['bindings']) >= 1:
        aop_id = [x['aop_id'] for x in stressor_json['results']['bindings']]
        aop_id_2 = [x['value'] for x in aop_id]
        # extract numbers
        pattern_id = re.compile(r'\d+')
        aop_ids = [pattern_id.search(x).group() for x in aop_id_2 if pattern_id.search(x)]
        return aop_ids

    return aop_ids

def check_if_life_stage_exist_in_aop(aop_id, life_stage):
    life_stage_json = sq.life_stage_filter_search(aop_id, life_stage)
    logging.error(f"life_stage_json: {life_stage_json}, {aop_id}, {life_stage}")
    if len(life_stage_json['results']['bindings']) >= 1:
        return True
    return False

def check_if_sex_exist_in_aop(aop_id, sex):
    sex_json = sq.sex_filter_search(aop_id, sex)
    logging.error(f"sex_json_JSON: {sex_json}, {aop_id}, {sex}")
    if len(sex_json['results']['bindings']) >= 1:
        return True
    return False

def check_if_organ_exist_in_aop(aop_id, organ):
    organ_json = sq.organ_filter_search(aop_id, organ)
    logging.error(f"organ_json: {organ_json}, {aop_id}, {organ}")
    if len(organ_json['results']['bindings']) >= 1:
        return True
    return False

def check_if_cell_exist_in_aop(aop_id, cell):
    cell_json = sq.cell_filter_search(aop_id, cell)
    logging.error(f"cell_json: {cell_json}, {aop_id}, {cell}")
    if len(cell_json['results']['bindings']) >= 1:
        return True
    return False

def check_if_taxonomic_exist_in_aop(aop_id, taxonomic):
    taxonomic_json = sq.taxonomic_filter_search(aop_id, taxonomic)
    logging.error(f"taxonomic_json: {taxonomic_json}, {aop_id}, {taxonomic}")
    if len(taxonomic_json['results']['bindings']) >= 1:
        return True
    return False