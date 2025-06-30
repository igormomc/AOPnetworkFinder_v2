from SPARQLWrapper import SPARQLWrapper, JSON, CSV

"""sparql aop"""

"""Base/default AOP query - Always included for AOP queries
contains optional parameter aop (numerical) if default value == 0, use default query (all aops from the AOPWiki)"""


def base_aop(aop_id='0') -> str:
    if aop_id == '':
        aop_id = '0'

    list_aop = aop_id.split(',')
    set_aop_int = set()

    for aop in list_aop:
        # Remove dups and convert value to int
        set_aop_int.add(int(aop))
    # convert back to list, do access elements with indexing
    list_aop_int = list(set_aop_int)

    if len(list_aop_int) == 1 and list_aop_int[0] > 0:
        # Only one AOP
        non_default_query = """
        ?aop a aopo:AdverseOutcomePathway ;
            dc:identifier aop:""" + aop_id + """ ;
            rdfs:label ?aop_id ;
            dc:title ?aop_name .
        """
        # columns: ?aop, ?aop_id, ?aop_name
        return non_default_query
    elif len(list_aop_int) > 1:
        # Multiple AOP
        multiple_aop = ''
        skip_or = True
        # concatinate multiple_aop, used inside the query
        for single_aop in list_aop_int:
            if skip_or:
                multiple_aop += ' ?aop_id = aop:' + str(single_aop)
                skip_or = False
            else:
                multiple_aop += ' || ?aop_id = aop:' + str(single_aop)

        non_default_query = """
        ?aop a aopo:AdverseOutcomePathway ;
            dc:identifier ?aop_id ;
            rdfs:label ?aop_label ;
            dc:title ?aop_name .

        FILTER ( """ + multiple_aop + """ )
        """
        # columns: ?aop, ?aop_id, ?aop_name
        return non_default_query

    default_query = """
    ?aop a aopo:AdverseOutcomePathway ;
        rdfs:label ?aop_id ;
        dc:title ?aop_name .
    """

    return default_query


"""Base/default KE query - Always included for KE queries
contains optional parameter ke (numerical) if default value == 0, use default query (all ke from the AOPWiki)"""


def base_ke(ke_id='0') -> str:
    if ke_id == '':
        ke_id = '0'

    list_ke = ke_id.split(',')
    set_ke_int = set()

    for ke in list_ke:
        # Remove dups and convert value to int
        set_ke_int.add(int(ke))
    # convert back to list, do access elements with indexing
    list_ke_int = list(set_ke_int)

    if len(list_ke_int) == 1 and list_ke_int[0] > 0:
        non_default_query = """
        ?ke a aopo:KeyEvent ;
            dc:identifier aop.events:""" + ke_id + """ ;
            rdfs:label ?ke_id ;
            dc:title ?ke_name .
        """
        # columns: ?aop, ?aop_id, ?aop_name
        return non_default_query
    elif len(list_ke_int) > 1:
        # Multiple ke
        multiple_ke = ''
        skip_or = True
        # concatinate multiple_ke, used inside the query
        for single_ke in list_ke_int:
            if skip_or:
                multiple_ke += ' ?ke_id = aop.events:' + str(single_ke)
                skip_or = False
            else:
                multiple_ke += ' || ?ke_id = aop.events:' + str(single_ke)

        non_default_query = """
            ?ke a aopo:KeyEvent ;
                dc:identifier ?ke_id ;
                rdfs:label ?ke_label ;
                dc:title ?ke_name .

            FILTER ( """ + multiple_ke + """ )
            """
        # columns: ?aop, ?aop_id, ?aop_name
        return non_default_query

    default_query = """
    ?ke a aopo:KeyEvent ;
        rdfs:label ?ke_id ;
        dc:title ?ke_name .
    """

    return default_query


"""Concatenate Select and Where clause to base_aop"""


def concat_clauses(qry) -> str:
    select_str = """Select """

    """Split qry, and retrieve all terms that have exclamation mark as prefix"""
    list_terms = qry.split()
    # column header only contains terms with exclamation as prefix
    column_header = [term for term in list_terms if '?' in term]
    # remove duplicates from column_header if there are any
    dup_removal_col_header = [*set(column_header)]

    """Concatenate columns to select"""
    for term in dup_removal_col_header:
        select_str += term + ' '

    where_str = """WHERE{""" + '\n' + qry + '\n' + """}"""

    # completed query - The one we are using to retrieve data from AOPWiki
    final_query = select_str + '\n' + where_str

    return final_query, dup_removal_col_header


""" FILTER FOR ONLY AOP START"""


def aop_abstract() -> str:
    abstract_string = 'OPTIONAL { ?aop dcterms:abstract ?aop_abstract .}'
    return abstract_string


def aop_prototypical_stressor() -> str:
    proto_stress_string = """ ?aop nci:C54571 ?stressor_id .
    OPTIONAL { ?stressor_id dc:title ?stressor_name . }"""
    return proto_stress_string


def aop_has_key_events() -> str:
    ke_string = """ ?aop aopo:has_key_event ?ke .
    ?ke rdfs:label ?ke_id ;
        dc:title ?ke_name . """
    return ke_string


def aop_mie() -> str:
    mie_string = """ ?aop aopo:has_molecular_initiating_event ?mie .
    ?mie rdfs:label ?mie_id ;
         dc:title ?mie_name . """
    return mie_string


def aop_ao() -> str:
    ao_string = """ ?aop aopo:has_adverse_outcome ?ao .
    ?ao rdfs:label ?ao_id ;
         dc:title ?ao_name . """
    return ao_string


def genes_in_ke_aop() -> str:
    ke_genes = """ ?aop aopo:has_key_event ?ke .
    ?ke rdfs:label ?ke_label ;
         dc:title ?ke_name .
    OPTIONAL {{ ?ke edam:data_1025 ?ke_genes . }}"""
    return ke_genes


def aop_author() -> str:
    author_string = 'OPTIONAL { ?aop dc:creator ?aop_author .}'
    return author_string


""" FILTER FOR ONLY AOP END"""

"""Query for AOP including filters
parameters: filter (bool), aop_id/aops_id (numerical), check_box_flag (binary flags), stressor (string - OPTIONAL), KE (numerical or name - OPTIONAL)"""


def one_aop(check_box_flag, ke_ids='0', aop_ids='0'):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    tmp_flags = check_box_flag  # TODO: add functionality when checkboxes are implemented.

    '''first check if ke_ids and aop_ids for default value 0'''
    ke_flag = False
    aop_flag = False

    if ke_ids != '':
        ke_flag = True

    if aop_ids != '':
        aop_flag = True

    query_both = ''
    if aop_flag is False and ke_flag is False:
        '''Only show default for aop'''
        incomplete_query = base_aop(aop_ids)
    elif aop_flag is True and ke_flag is True:
        '''need two incomplete queries, one for AOP and one for KE. we concatinates both queries at the end'''
        incomplete_query = base_aop(aop_ids)
        query_both = base_ke(ke_ids)
    elif aop_flag is True and ke_flag is False:
        incomplete_query = base_aop(aop_ids)
    elif aop_flag is False and ke_flag is True:
        incomplete_query = base_ke(ke_ids)

    """if checkboxes is checked, call the corresponding function and append to incomplete query"""
    for chx_name, bool_chx in tmp_flags:
        # abstract checkbox
        if aop_flag is True and ke_flag is False:
            if chx_name == 'abstract' and bool_chx == '1':
                get_abstract = aop_abstract()
                # append to incomplete query
                incomplete_query += '\n' + get_abstract

            # stressor checkbox
            if chx_name == 'stressor' and bool_chx == '1':
                get_stressor = aop_prototypical_stressor()
                # append to incomplete query
                incomplete_query += '\n' + get_stressor

            # ke checkbox
            if chx_name == 'ke' and bool_chx == '1':
                get_ke = aop_has_key_events()
                # append to incomplete query
                incomplete_query += '\n' + get_ke

            # mie checkbox
            if chx_name == 'mie' and bool_chx == '1':
                get_mie = aop_mie()
                # append to incomplete query
                incomplete_query += '\n' + get_mie

            # ao checkbox
            if chx_name == 'ao' and bool_chx == '1':
                get_ao = aop_ao()
                # append to incomplete query
                incomplete_query += '\n' + get_ao

            if chx_name == 'KE Genes' and bool_chx == '1':
                get_ke_genes_aop = genes_in_ke_aop()
                incomplete_query += '\n' + get_ke_genes_aop

            if chx_name == 'aop_author' and bool_chx == '1':
                get_author = aop_author()
                # append to incomplete query
                incomplete_query += '\n' + get_author

        elif aop_flag is False and ke_flag is True:

            if chx_name == 'In AOP' and bool_chx == '1':
                get_in_aop = ke_in_aop()
                incomplete_query += '\n' + get_in_aop

            if chx_name == 'ke stressor' and bool_chx == '1':
                get_ke_stressor = ke_stressor()
                incomplete_query += '\n' + get_ke_stressor

            if chx_name == 'ke genes' and bool_chx == '1':
                get_ke_genes = ke_genes()
                incomplete_query += '\n' + get_ke_genes

            if chx_name == 'ke cell type context' and bool_chx == '1':
                get_ke_cell_type = ke_cell_type()
                incomplete_query += '\n' + get_ke_cell_type

            if chx_name == 'ke description' and bool_chx == '1':
                get_ke_description = ke_description()
                incomplete_query += '\n' + get_ke_description

            if chx_name == 'ke measurements' and bool_chx == '1':
                get_ke_measurements = ke_measurements()
                incomplete_query += '\n' + get_ke_measurements

    complete_query, column_header = concat_clauses(incomplete_query)

    """If filter == True, concatenate filtered queries to query_string"""

    sparql.setReturnFormat(JSON)
    """After doing all the filtering, use the final query as parameter for sparql.setQuery() and get the result"""
    sparql.setQuery(complete_query)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format, column_header
    except Exception as e:
        print(e)


""" FILTER FOR ONLY KE START"""


def ke_in_aop() -> str:
    ke_in_aop_string = '?ke dcterms:isPartOf ?in_aop .'
    return ke_in_aop_string


def ke_stressor() -> str:
    ke_stressor_string = """ OPTIONAL { ?ke nci:C54571 ?ke_stressor_id .
    ?ke_stressor_id dc:title ?ke_stressor_name . }"""
    return ke_stressor_string


def ke_genes() -> str:
    ke_gene = 'OPTIONAL { ?ke edam:data_1025 ?ke_genes . }'
    return ke_gene


def ke_cell_type() -> str:
    ke_cell_type = """OPTIONAL { ?ke aopo:CellTypeContext ?ke_cell_type . } """
    return ke_cell_type


def ke_description() -> str:
    ke_description_string = """OPTIONAL { ?ke dc:description ?ke_description . }"""
    return ke_description_string


def ke_measurements() -> str:
    ke_measurements_string = """OPTIONAL { ?ke mmo:0000000 ?ke_measurements . } """
    return ke_measurements_string


""" FILTER FOR ONLY KE END"""
