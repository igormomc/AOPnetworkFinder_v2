from SPARQLWrapper import SPARQLWrapper, JSON


### Sparql queries ###

##only identify with AOP id (integer).
def one_aop(aop_id):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    if aop_id.isdigit():
        # use dc:identifier
        sparql.setReturnFormat(JSON)
        sparql.setQuery("""
                    SELECT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?genes
                    WHERE{
                        ?AOP a aopo:AdverseOutcomePathway ;
                            dc:identifier aop:""" + aop_id + """ ;
                            aopo:has_molecular_initiating_event ?MIE ;
                            aopo:has_key_event_relationship ?KER ;
                            aopo:has_key_event ?KE_up ;
                            aopo:has_adverse_outcome ?AO .

                        ?KER a aopo:KeyEventRelationship ;
                            aopo:has_upstream_key_event ?KE_up ;
                            aopo:has_downstream_key_event ?KE_dwn ;
                            edam:data_1025 ?genes .
                    }
                    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def stressor_AOP_finder(bin_stress):
    # binary_stressor can either be the name of the stressor 'dc:title' or the identifier 'dc:identifier'.

    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    # check if it is eiter a number or a string.
    if bin_stress.isdigit():
        # dc:identifier
        sparql.setReturnFormat(JSON)
        sparql.setQuery("""SELECT ?stressor ?AOP ?stressor_name ?chem_name
                    WHERE{
	                    ?stressor a nci:C54571 ;
                            dc:title ?stressor_name ;
                            dcterms:isPartOf ?AOP ;
                            dc:identifier aop.stressor:""" + bin_stress + """ ;
                            aopo:has_chemical_entity ?chem .

  	                    #include '?AOP is instance of AdverseOutcomePathway' to only include AOP and not KE.
  	                    ?AOP a aopo:AdverseOutcomePathway .

  	                    ?chem a cheminf:000446 ;
  	                        dc:title ?chem_name .
                    }
                    """)
    else:
        # dc:title
        stressor = '\'' + bin_stress + '\''
        sparql.setReturnFormat(JSON)
        query = """SELECT ?stressor ?AOP ?aop_id
                            WHERE{
        	                    ?stressor a nci:C54571 ;
                                    dc:title """ + stressor + """ ;
                                    dcterms:isPartOf ?AOP .

          	                    #include '?AOP is instance of AdverseOutcomePathway' to only include AOP and not KE.
          	                    ?AOP a aopo:AdverseOutcomePathway ;
          	                        rdfs:label ?aop_id .
                            }
                            """
        sparql.setQuery(query)

    try:

        ret = sparql.query()
        json_format = ret.convert()
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def stressor_and_AOP_finder(binary_stressor, aop_id):
    # binary_stressor can either be the name of the stressor 'dc:title' or the identifier 'dc:identifier'.

    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    # check if it is eiter a number or a string.
    if binary_stressor.isdigit():
        # dc:identifier
        sparql.setReturnFormat(JSON)
        sparql.setQuery("""SELECT ?stressor ?stressor_name ?chem_name ?MIE ?KE_up ?KE_dwn ?genes
                    WHERE{

                    ?stressor a nci:C54571 ;
                    	dc:title ?stressor_name ;
                    	dcterms:isPartOf ?AOP ;
                    	aopo:has_chemical_entity ?chem ;
                    	dc:identifier aop.stressor:""" + binary_stressor + """ .

                    ?chem a cheminf:000446 ;
                    	dc:title ?chem_name .

                    ?AOP a aopo:AdverseOutcomePathway ;
                        dc:identifier aop:""" + aop_id + """ ;
                        aopo:has_molecular_initiating_event ?MIE ;
                        aopo:has_key_event_relationship ?KER ;
                        aopo:has_key_event ?KE_up ;
                        aopo:has_adverse_outcome ?AO .

                    ?KER a aopo:KeyEventRelationship ;
                        aopo:has_upstream_key_event ?KE_up ;
                        aopo:has_downstream_key_event ?KE_dwn .
                        edam:data_1025 ?genes .                                  
                    }
                        """)
    else:
        # dc:title
        stressor = '\'' + binary_stressor + '\''
        sparql.setReturnFormat(JSON)
        sparql.setQuery("""SELECT ?stressor ?stressor_name ?chem_name ?MIE ?KE_up ?KE_dwn ?genes
                    WHERE{

                    BIND(""" + stressor + """ AS ?stressor_name)

                    ?stressor a nci:C54571 ;
                    	dc:title ?stressor_name ;
                    	dcterms:isPartOf ?AOP ;
                    	aopo:has_chemical_entity ?chem .

                    ?chem a cheminf:000446 ;
                    	dc:title ?chem_name .

                    ?AOP a aopo:AdverseOutcomePathway ;
                        dc:identifier aop:""" + aop_id + """ ;
                        aopo:has_molecular_initiating_event ?MIE ;
                        aopo:has_key_event_relationship ?KER ;
                        aopo:has_key_event ?KE_up ;
                        aopo:has_adverse_outcome ?AO .

                    ?KER a aopo:KeyEventRelationship ;
                        aopo:has_upstream_key_event ?KE_up ;
                        aopo:has_downstream_key_event ?KE_dwn ;
                        edam:data_1025 ?genes .                                  
                    }
                        """)

    try:

        ret = sparql.query()
        json_format = ret.convert()
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


##query that runs when the program starts. 'name of all stressors'
# TODO: implement this query

##query that finds all data of a single KEY

##query for aop class

# TODO: aop_dump query needs updating, (?ke_genes and ?ke_dwn_genes -> empty) - if the aop_dump gets updated
# Update also the query in the function multiple_aop_dump

# Dump all AOP data for a given aop, including KE and KER -> query 1 time
def aop_dump(aop_id):
    # endpoint sparql
    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")

    if aop_id.isdigit():
        sparql.setReturnFormat(JSON)
        sparql.setQuery(f"""
SELECT DISTINCT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?ker_genes ?aop_id ?aop_label ?ke_id ?ke_label ?ke_title ?ke_genes ?ke_dwn_label ?ke_dwn_id ?ke_dwn_title ?ke_dwn_genes
WHERE
{{
  BIND(aop:{aop_id} AS ?aop_id)

  ?AOP a aopo:AdverseOutcomePathway ;
       dc:identifier ?aop_id;
       rdfs:label ?aop_label .

  OPTIONAL {{ ?AOP aopo:has_molecular_initiating_event ?MIE . }}
  OPTIONAL {{ ?AOP aopo:has_adverse_outcome ?AO . }}

  ?AOP aopo:has_key_event ?KE_up .
  ?KE_up dc:identifier ?ke_id ;
         rdfs:label ?ke_label ;
         dc:title ?ke_title .
  OPTIONAL {{ ?KE_up edam:data_1025 ?ke_genes . }}

  OPTIONAL {{
    ?AOP aopo:has_key_event_relationship ?KER .
    ?KER a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?KE_up ;
         aopo:has_downstream_key_event ?KE_dwn .
    #OPTIONAL {{ ?KER edam:data_1025 ?ker_genes . }}

    ?KE_dwn dc:identifier ?ke_dwn_id ;
            rdfs:label ?ke_dwn_label ;
            dc:title ?ke_dwn_title .
    OPTIONAL {{ ?KE_dwn edam:data_1025 ?ke_dwn_genes . }}
  }}
}}
""")
        try:
            ret = sparql.query()
            json_format = ret.convert()
            return json_format
        except Exception as e:
            print(e)


###def aop_dump(aop_id):
###    # endpoint sparql
###    sparql = SPARQLWrapper(
###        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
###    )
###
###    if aop_id.isdigit():
###        # use dc:identifier
###        print('AOP_datadump aop_id: {}'.format(aop_id))
###        sparql.setReturnFormat(JSON)
###        sparql.setQuery("""
###SELECT DISTINCT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?ker_genes ?aop_id ?aop_label ?ke_id ?ke_label ?ke_title ?ke_genes ?ke_dwn_label ?ke_dwn_id ?ke_dwn_title ?ke_dwn_genes
###WHERE
###{
###  BIND(aop:""" + aop_id + """ AS ?aop_id)
###
###  ?AOP a aopo:AdverseOutcomePathway ;
###         dc:identifier ?aop_id;
###         #aopo:has_molecular_initiating_event ?MIE ;
###         rdfs:label ?aop_label ;
###         aopo:has_key_event_relationship ?KER ;
###         aopo:has_key_event ?KE_up .
###         #aopo:has_adverse_outcome ?AO .
###
###  OPTIONAL{?AOP aopo:has_molecular_initiating_event ?MIE .}
###  OPTIONAL{?AOP aopo:has_adverse_outcome ?AO .}
###
###  ?KER a aopo:KeyEventRelationship ;
###         aopo:has_upstream_key_event ?KE_up ;
###         aopo:has_downstream_key_event ?KE_dwn .
###         #edam:data_1025 ?genes .
###  OPTIONAL { ?KER edam:data_1025 ?ker_genes .}
###
###  #ke, data dump - all except AO, need to make one for AO
###  ?KE_up dc:identifier ?ke_id ;
###         rdfs:label ?ke_label ;
###         dc:title ?ke_title .
###
###  OPTIONAL { ?KE_up edam:data_1025 ?ke_genes .}
###
###  ?KE_dwn dc:identifier ?ke_dwn_id ;
###         rdfs:label ?ke_dwn_label ;
###         dc:title ?ke_dwn_title .
###
###  OPTIONAL { ?KE_dwn edam:data_1025 ?ke_dwn_genes .}
###
###}
###
###                    """)
###
###    try:
###        ret = sparql.query()
###        json_format = ret.convert()
###        ###print(csv_format)
###        '''for x in json_format['results']['bindings']:
###            print(x)'''
###        # if needed convert JSON to CSV.
###        # TODO: return the dictionary for data manipulation
###        return json_format
###    except Exception as e:
###        print(e)


# Multiple AOP dump, takes a single string variable that contains multiple AOPs.
# Use the string to query 2 or more AOPs
# TODO: query needs updating, need to make mie, and aop optional. Not all AOPs have a MIE or AO
###def multiple_aop_dump(list_of_aop_id):
###    # endpoint sparql
###    sparql = SPARQLWrapper(
###        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
###    )
###
###    if len(list_of_aop_id) > 1:
###        # use dc:identifier
###        print('AOP_datadump aop_id: {}'.format(list_of_aop_id))
###        multiple_aop = ''
###        skip_or = True
###        # concatinate multiple_aop, used inside the query
###        for single_aop in list_of_aop_id:
###            if skip_or:
###                multiple_aop += '?aop_id = aop:' + single_aop
###                skip_or = False
###            else:
###                multiple_aop += ' || ?aop_id = aop:' + single_aop
###        print('variable inside query: {}'.format(multiple_aop))
###        sparql.setReturnFormat(JSON)
###        sparql.setQuery("""
###SELECT DISTINCT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?aop_id ?aop_label ?ke_id ?ke_label ?ke_title ?ke_genes ?ke_dwn_label ?ke_dwn_id ?ke_dwn_title ?ke_dwn_genes
###WHERE
###{
###
###  ?AOP a aopo:AdverseOutcomePathway ;
###         dc:identifier ?aop_id;
###         rdfs:label ?aop_label ;
###         aopo:has_key_event_relationship ?KER ;
###         aopo:has_key_event ?KE_up .
###
###  OPTIONAL{?AOP aopo:has_molecular_initiating_event ?MIE .}
###  OPTIONAL{?AOP aopo:has_adverse_outcome ?AO .}
###
###  ?KER a aopo:KeyEventRelationship ;
###         aopo:has_upstream_key_event ?KE_up ;
###         aopo:has_downstream_key_event ?KE_dwn .
###         #edam:data_1025 ?genes .
###
###  #ke, data dump - all except AO, need to make one for AO
###  ?KE_up dc:identifier ?ke_id ;
###         rdfs:label ?ke_label ;
###         dc:title ?ke_title .
###
###  OPTIONAL { ?KE_up edam:data_1025 ?ke_genes .}
###
###  ?KE_dwn dc:identifier ?ke_dwn_id ;
###         rdfs:label ?ke_dwn_label ;
###         dc:title ?ke_dwn_title .
###
###  OPTIONAL { ?KE_dwn edam:data_1025 ?ke_dwn_genes .}
###  FILTER (""" + multiple_aop + """)
###} ORDER BY(?AOP)
###                    """)
###
###    try:
###        ret = sparql.query()
###        json_format = ret.convert()
###        ###print(csv_format)
###        '''for x in json_format['results']['bindings']:
###            print(x)'''
###        # if needed convert JSON to CSV.
###        # TODO: return the dictionary for data manipulation
###        return json_format
###    except Exception as e:
###        print(e)

def multiple_aop_dump(list_of_aop_id):
    # endpoint sparql
    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")

    if len(list_of_aop_id) > 0:
        # Constructing the FILTER condition dynamically
        filter_conditions = " || ".join([f"?aop_id = aop:{aop}" for aop in list_of_aop_id])
        sparql.setReturnFormat(JSON)
        query = f"""
SELECT DISTINCT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?ker_genes ?aop_id ?aop_label ?ke_id ?ke_label ?ke_title ?ke_genes ?ke_dwn_label ?ke_dwn_id ?ke_dwn_title ?ke_dwn_genes
WHERE
{{
  ?AOP a aopo:AdverseOutcomePathway ;
       dc:identifier ?aop_id;
       rdfs:label ?aop_label .

  OPTIONAL {{ ?AOP aopo:has_molecular_initiating_event ?MIE . }}
  OPTIONAL {{ ?AOP aopo:has_adverse_outcome ?AO . }}

  ?AOP aopo:has_key_event ?KE_up .
  ?KE_up dc:identifier ?ke_id ;
         rdfs:label ?ke_label ;
         dc:title ?ke_title .
  OPTIONAL {{ ?KE_up edam:data_1025 ?ke_genes . }}

  OPTIONAL {{
    ?AOP aopo:has_key_event_relationship ?KER .
    ?KER a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?KE_up ;
         aopo:has_downstream_key_event ?KE_dwn .
    #OPTIONAL {{ ?KER edam:data_1025 ?ker_genes . }}

    ?KE_dwn dc:identifier ?ke_dwn_id ;
            rdfs:label ?ke_dwn_label ;
            dc:title ?ke_dwn_title .
    OPTIONAL {{ ?KE_dwn edam:data_1025 ?ke_dwn_genes . }}
  }}
  FILTER ({filter_conditions})
}}
ORDER BY(?AOP)
"""
        sparql.setQuery(query)

        try:
            ret = sparql.query()
            json_format = ret.convert()
            return json_format
        except Exception as e:
            print(e)


# if AOP-dump is used, call this method. (retrieve AO data)
def ao_dump(aop_id):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    if aop_id.isdigit():
        # use dc:identifier
        sparql.setReturnFormat(JSON)
        sparql.setQuery("""
SELECT distinct ?ao ?ao_id ?label ?name ?genes ?aop_id
WHERE{

  BIND(aop:""" + aop_id + """ AS ?aop_id)

  ?aop a aopo:AdverseOutcomePathway ;
         dc:identifier ?aop_id ;
         aopo:has_adverse_outcome ?ao .

  ?ao a aopo:KeyEvent;
      dc:identifier ?ao_id ;
      rdfs:label ?label ;
      dc:title ?name .

  OPTIONAL { ?ao edam:data_1025 ?genes .}   
}

                    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


# run at the start of the program, and store all stressor in a list. (used for stressor lookup)
def stressor_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
    SELECT ?stressor ?str_id ?str_label ?str_title
WHERE
{
  ?stressor a nci:C54571 ;
              dc:identifier ?str_id ;
              rdfs:label ?str_label ;
              dc:title ?str_title .
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def cell_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
    SELECT DISTINCT ?cellObject ?cell_title
    WHERE {
	  
    ?ke aopo:CellTypeContext ?cellObject .
  	?cellObject dc:title ?cell_title
    }
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def organ_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
    SELECT DISTINCT ?organObject ?organ_title
    WHERE {

    ?ke aopo:OrganContext ?organObject .
  	?organObject dc:title ?organ_title
    }
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def taxonomic_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
     SELECT DISTINCT ?taxObject ?tax_title
    WHERE {
	  
    ?ke ncbitaxon:131567 ?taxObject .
  	?taxObject dc:title ?tax_title
    }
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def sex_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
     SELECT DISTINCT ?sexObject
    WHERE {
	  
    ?ke pato:0000047 ?sexObject .
    }
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def lifeStage_dump():
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
     SELECT DISTINCT ?lifeStageObject
    WHERE {
	  
    ?ke aopo:LifeStageContext ?lifeStageObject .
    }
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


'''Return all AOP ID linked to a given KE/KEs.'''


def ke_get_aopid(list_of_ke_id):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    multiple_ke = ''
    skip_or = True
    # concatenate multiple_ke, used inside the query
    for single_ke in list_of_ke_id:
        if skip_or:
            multiple_ke += '?ke_id = aop.events:' + single_ke
            skip_or = False
        else:
            multiple_ke += ' || ?ke_id = aop.events:' + single_ke

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
    SELECT ?aop_id
WHERE
{
    ?ke a aopo:KeyEvent ;
        dc:identifier ?ke_id .

    ?aop a aopo:AdverseOutcomePathway ;
         dc:identifier ?aop_id ;
         aopo:has_key_event ?ke .

    FILTER (""" + multiple_ke + """)
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def aop_text_dump():
    '''This query is used for Data mining, (IR Page)'''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT distinct ?aop_label ?aop_abstract (GROUP_CONCAT(DISTINCT ?aop_description; separator=", ") as ?description) ?aop_context ?aop_evidence ?aop_operation ?aop_potential_application ?aop_asssessment ?aop_key_event_essentiality
WHERE{

  ?aop a aopo:AdverseOutcomePathway ;
       rdfs:label ?aop_label .

  OPTIONAL{?aop dcterms:abstract ?aop_abstract .}
  OPTIONAL{?aop dc:description ?aop_description .}
  OPTIONAL{?aop aopo:AopContext ?aop_context .}
  OPTIONAL{?aop aopo:has_evidence ?aop_evidence .}
  OPTIONAL{?aop edam:operation_3799 ?aop_operation .}
  OPTIONAL{?aop nci:C25725 ?aop_potential_application .}
  OPTIONAL{?aop nci:C25217 ?aop_asssessment .}
  OPTIONAL{?aop nci:C48192 ?aop_key_event_essentiality .}

  }
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_text_dump():
    '''This Query is used for Data mining (IR Page)'''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT distinct ?ke_label (GROUP_CONCAT(DISTINCT ?ke_description; separator=", ") as ?description) ?ke_context ?ke_s_appl ?ke_bio_process ?ke_cell_context ?ke_organ_context ?ke_bio_action ?ke_bio_obj ?ke_measurement
WHERE{

  ?ke a aopo:KeyEvent ;
       rdfs:label ?ke_label .

  #OPTIONAL{?aop dcterms:abstract ?ke_abstract .}
  OPTIONAL{?ke dc:description ?ke_description .}
  OPTIONAL{?ke aopo:LifeStageContext ?ke_context .}
  OPTIONAL{?ke pato:0000047 ?ke_s_appl .}
  OPTIONAL{?ke edam:operation_3799 ?aop_operation .}
  OPTIONAL{?ke go:0008150 ?ke_bio_process .}
  OPTIONAL{?ke aopo:CellTypeContext ?ke_cell_context .}
  OPTIONAL{?ke aopo:OrganContext ?ke_organ_context .}
  OPTIONAL{?ke pato:0000001 ?ke_bio_action .}
  OPTIONAL{?ke pato:0000001 ?ke_bio_obj .}
  OPTIONAL{?ke mmo:0000000 ?ke_measurement .}
  }
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_degree_1_dump(ke_id):
    '''Degree 1 of a given KE'''
    # endpoint sparql
    ke_id_int = str(ke_id)
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT ?ker ?ke_id ?keRoot_name ?keRoot_label ?ke_dwn ?keDwn_name ?keDwn_label ?ke_up ?keUp_name ?keUp_label
WHERE {
  BIND(aop.events:""" + ke_id_int + """ AS ?ke_id)

  ?keRoot a aopo:KeyEvent;
           dc:identifier ?ke_id;
           dc:title ?keRoot_name ;
           rdfs:label ?keRoot_label .
  {
     ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?ke_id ;
           aopo:has_downstream_key_event ?ke_dwn .

             OPTIONAL{?keDwn a aopo:KeyEvent;
           dc:identifier ?ke_dwn;
           dc:title ?keDwn_name ;
           rdfs:label ?keDwn_label .}
  }
  UNION
  {
      ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?ke_up ;
           aopo:has_downstream_key_event ?ke_id .

         OPTIONAL{?keUp a aopo:KeyEvent;
           dc:identifier ?ke_up;
           dc:title ?keUp_name ;
           rdfs:label ?keUp_label .}
  }

}
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_degree_2_dump(ke_id):
    '''Degree 2 of a given KE'''
    # endpoint sparql
    ke_id_int = str(ke_id)
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT ?ker ?ke_id ?keRoot_name ?keRoot_label ?lvl_1_up ?lvl_1_up_name ?lvl_1_up_label ?lvl_1_dwn ?lvl_1_dwn_name ?lvl_1_dwn_label ?lvl_2_up ?lvl_2_up_name ?lvl_2_up_label ?lvl_2_dwn ?lvl_2_dwn_name ?lvl_2_dwn_label
WHERE {
  #Degree 2
   {
     ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?lvl_2_up ;
           aopo:has_downstream_key_event ?lvl_1_dwn .

                  OPTIONAL{?keUp_2 a aopo:KeyEvent;
           dc:identifier ?lvl_2_up;
           dc:title ?lvl_2_up_name ;
           rdfs:label ?lvl_2_up_label .}
   }
      UNION
  {
    ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?lvl_1_up ;
           aopo:has_downstream_key_event ?lvl_2_dwn .

                 OPTIONAL{?keDwn_2 a aopo:KeyEvent;
           dc:identifier ?lvl_2_dwn;
           dc:title ?lvl_2_dwn_name ;
           rdfs:label ?lvl_2_dwn_label .}
  }

  {
    SELECT ?ke_id ?keRoot_name ?keRoot_label ?lvl_1_up ?lvl_1_up_name ?lvl_1_up_label ?lvl_1_dwn ?lvl_1_dwn_name ?lvl_1_dwn_label
    WHERE {
      # Degree 1
      BIND(aop.events:""" + ke_id_int + """ AS ?ke_id)

      ?keRoot a aopo:KeyEvent;
           dc:identifier ?ke_id;
           dc:title ?keRoot_name ;
           rdfs:label ?keRoot_label .

        {
                  ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?ke_id ;
           aopo:has_downstream_key_event ?lvl_1_dwn .

             OPTIONAL{?keDwn a aopo:KeyEvent;
           dc:identifier ?lvl_1_dwn;
           dc:title ?lvl_1_dwn_name ;
           rdfs:label ?lvl_1_dwn_label .}

          }
          UNION
          {
              ?ker a aopo:KeyEventRelationship ;
                      aopo:has_upstream_key_event ?lvl_1_up ;
                      aopo:has_downstream_key_event ?ke_id .

              OPTIONAL{?keUp a aopo:KeyEvent;
           dc:identifier ?lvl_1_up;
           dc:title ?lvl_1_up_name ;
           rdfs:label ?lvl_1_up_label .}
          }
    }
  }
}
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_degree_1_multiple_dump(ke_ids):
    '''Degree 1 of given KEs'''
    # Convert ke_id list to a SPARQL VALUES string
    ke_ids_values = " ".join([f"(aop.events:{ke_id})" for ke_id in ke_ids])

    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")
    sparql.setReturnFormat(JSON)
    query = f"""
        SELECT ?ker ?ke_id ?keRoot_name ?keRoot_label ?ke_dwn ?keDwn_name ?keDwn_label ?ke_up ?keUp_name ?keUp_label
        WHERE {{
          VALUES (?ke_id) {{
            {ke_ids_values}
          }}
          ?keRoot a aopo:KeyEvent;
                  dc:identifier ?ke_id;
                  dc:title ?keRoot_name ;
                  rdfs:label ?keRoot_label .
          {{
             ?ker a aopo:KeyEventRelationship ;
                   aopo:has_upstream_key_event ?ke_id ;
                   aopo:has_downstream_key_event ?ke_dwn .

                 OPTIONAL{{?keDwn a aopo:KeyEvent;
               dc:identifier ?ke_dwn;
               dc:title ?keDwn_name ;
               rdfs:label ?keDwn_label .}}
          }}
          UNION
          {{
              ?ker a aopo:KeyEventRelationship ;
                   aopo:has_upstream_key_event ?ke_up ;
                   aopo:has_downstream_key_event ?ke_id .

             OPTIONAL{{?keUp a aopo:KeyEvent;
               dc:identifier ?ke_up;
               dc:title ?keUp_name ;
               rdfs:label ?keUp_label .}}
          }}
        }}
    """

    sparql.setQuery(query)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def ke_degree_2_multiple_dump(ke_ids):
    '''Degree 2 of given KEs'''
    # Convert ke_ids list to a SPARQL VALUES string
    ke_id_values = " ".join([f"(aop.events:{ke_id})" for ke_id in ke_ids])

    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")
    sparql.setReturnFormat(JSON)
    query_template = """
                    SELECT ?ker ?ke_id ?keRoot_name ?keRoot_label ?lvl_1_up ?lvl_1_up_name ?lvl_1_up_label ?lvl_1_dwn ?lvl_1_dwn_name ?lvl_1_dwn_label ?lvl_2_up ?lvl_2_up_name ?lvl_2_up_label ?lvl_2_dwn ?lvl_2_dwn_name ?lvl_2_dwn_label
WHERE {
  VALUES (?ke_id) {{values}}
  #Degree 2
   {
     ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?lvl_2_up ;
           aopo:has_downstream_key_event ?lvl_1_dwn .

                  OPTIONAL{?keUp_2 a aopo:KeyEvent;
           dc:identifier ?lvl_2_up;
           dc:title ?lvl_2_up_name ;
           rdfs:label ?lvl_2_up_label .}
   }
      UNION
  {
    ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?lvl_1_up ;
           aopo:has_downstream_key_event ?lvl_2_dwn .

                 OPTIONAL{?keDwn_2 a aopo:KeyEvent;
           dc:identifier ?lvl_2_dwn;
           dc:title ?lvl_2_dwn_name ;
           rdfs:label ?lvl_2_dwn_label .}
  }

  {
    SELECT ?ke_id ?keRoot_name ?keRoot_label ?lvl_1_up ?lvl_1_up_name ?lvl_1_up_label ?lvl_1_dwn ?lvl_1_dwn_name ?lvl_1_dwn_label
    WHERE {
      # Degree 1

      ?keRoot a aopo:KeyEvent;
           dc:identifier ?ke_id;
           dc:title ?keRoot_name ;
           rdfs:label ?keRoot_label .

        {
                  ?ker a aopo:KeyEventRelationship ;
           aopo:has_upstream_key_event ?ke_id ;
           aopo:has_downstream_key_event ?lvl_1_dwn .

             OPTIONAL{?keDwn a aopo:KeyEvent;
           dc:identifier ?lvl_1_dwn;
           dc:title ?lvl_1_dwn_name ;
           rdfs:label ?lvl_1_dwn_label .}

          }
          UNION
          {
              ?ker a aopo:KeyEventRelationship ;
                      aopo:has_upstream_key_event ?lvl_1_up ;
                      aopo:has_downstream_key_event ?ke_id .

              OPTIONAL{?keUp a aopo:KeyEvent;
           dc:identifier ?lvl_1_up;
           dc:title ?lvl_1_up_name ;
           rdfs:label ?lvl_1_up_label .}
          }
    }
  }
}
                    """
    # Inject the VALUES string into the query
    sparql_query = query_template.replace("{values}", ke_id_values)
    sparql.setQuery(sparql_query)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)
        return None


def ke_degree_3_dump(ke_id):
    '''Degree 3 of a given KE'''
    # endpoint sparql
    ke_id_int = str(ke_id)
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT ?ker ?ke_id ?lvl_1_up ?lvl_1_dwn ?lvl_2_up ?lvl_2_dwn ?lvl_3_up ?lvl_3_dwn
WHERE {

  # Degree 3
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_3_up ;
         aopo:has_downstream_key_event ?lvl_2_dwn .
  }
  UNION
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_2_up ;
         aopo:has_downstream_key_event ?lvl_3_dwn .
  }

  {
    SELECT ?lvl_1_up ?lvl_1_dwn ?lvl_2_up ?lvl_2_dwn
    WHERE {
  # Degree 2
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_2_up ;
         aopo:has_downstream_key_event ?lvl_1_dwn .
  }
  UNION
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_1_up ;
         aopo:has_downstream_key_event ?lvl_2_dwn .
  }

  # Degree 1
  {
    SELECT ?lvl_1_up ?lvl_1_dwn
    WHERE {
      BIND(aop.events:""" + ke_id_int + """ AS ?ke_id)

      {
        ?ker a aopo:KeyEventRelationship ;
             aopo:has_upstream_key_event ?ke_id ;
             aopo:has_downstream_key_event ?lvl_1_dwn .
      }
      UNION
      {
        ?ker a aopo:KeyEventRelationship ;
             aopo:has_upstream_key_event ?lvl_1_up ;
             aopo:has_downstream_key_event ?ke_id .
      }
    }
  }
      }
    }
}
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_degree_4_dump(ke_id):
    '''Degree 4 of a given KE'''
    # endpoint sparql
    ke_id_int = str(ke_id)
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )
    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
                    SELECT ?ker ?ke_id ?lvl_1_up ?lvl_1_dwn ?lvl_2_up ?lvl_2_dwn ?lvl_3_up ?lvl_3_dwn ?lvl_4_up ?lvl_4_dwn
WHERE {

  # Degree 4
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_4_up ;
         aopo:has_downstream_key_event ?lvl_3_dwn .
  }
  UNION
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_3_up ;
         aopo:has_downstream_key_event ?lvl_4_dwn .
  }

  {
    SELECT ?lvl_2_up ?lvl_2_dwn ?lvl_3_up ?lvl_3_dwn
    WHERE {
        # Degree 3
      {
        ?ker a aopo:KeyEventRelationship ;
                aopo:has_upstream_key_event ?lvl_3_up ;
               aopo:has_downstream_key_event ?lvl_2_dwn .
    }
    UNION
    {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_2_up ;
         aopo:has_downstream_key_event ?lvl_3_dwn .
    }

  {
    SELECT ?lvl_1_up ?lvl_1_dwn ?lvl_2_up ?lvl_2_dwn
    WHERE {
  # Degree 2
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_2_up ;
         aopo:has_downstream_key_event ?lvl_1_dwn .
  }
  UNION
  {
    ?ker a aopo:KeyEventRelationship ;
         aopo:has_upstream_key_event ?lvl_1_up ;
         aopo:has_downstream_key_event ?lvl_2_dwn .
  }

  # Degree 1
  {
    SELECT ?lvl_1_up ?lvl_1_dwn
    WHERE {
      BIND(aop.events:""" + ke_id_int + """ AS ?ke_id)

      {
        ?ker a aopo:KeyEventRelationship ;
             aopo:has_upstream_key_event ?ke_id ;
             aopo:has_downstream_key_event ?lvl_1_dwn .
      }
      UNION
      {
        ?ker a aopo:KeyEventRelationship ;
             aopo:has_upstream_key_event ?lvl_1_up ;
             aopo:has_downstream_key_event ?ke_id .
      }
    }
  }
      }
    }
      }
    }
}
                    """)
    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


'''Return all AOP ID linked to a given KE/KEs.'''


def ke_get_ao(list_of_ke_id):
    '''This is used to identify if a ke is ao or not.
     meant to supplement KE degree'''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    multiple_ke = ''
    skip_or = True
    # concatenate multiple_ke, used inside the query
    for single_ke in list_of_ke_id:
        if skip_or:
            multiple_ke += '?ke_type = aop.events:' + single_ke
            skip_or = False
        else:
            multiple_ke += ' || ?ke_type = aop.events:' + single_ke

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
SELECT ?ke ?ao
WHERE {

  ?aop a aopo:AdverseOutcomePathway ;
       aopo:has_adverse_outcome ?ke .

  ?ke a aopo:KeyEvent ;
      dc:identifier ?ke_type ;
      rdfs:label ?ao .

  FILTER (""" + multiple_ke + """)
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def ke_get_mie(list_of_ke_id):
    '''This is used to identify if a ke is ao or not.
     meant to supplement KE degree'''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    multiple_ke = ''
    skip_or = True
    # concatenate multiple_ke, used inside the query
    for single_ke in list_of_ke_id:
        if skip_or:
            multiple_ke += '?ke_type = aop.events:' + single_ke
            skip_or = False
        else:
            multiple_ke += ' || ?ke_type = aop.events:' + single_ke

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
SELECT ?ke ?mie
WHERE {

  ?aop a aopo:AdverseOutcomePathway ;
       aopo:has_molecular_initiating_event ?ke .

  ?ke a aopo:KeyEvent ;
      dc:identifier ?ke_type ;
      rdfs:label ?mie .

  FILTER (""" + multiple_ke + """)
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def aop_status(list_of_statuses):
    '''Filter AOPs '''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    aop_filter = ''
    skip_or = True
    # concatenate multiple_ke, used inside the query
    for one_filter in list_of_statuses:
        if skip_or:
            aop_filter += "?status = '" + one_filter + "'"
            skip_or = False
        else:
            aop_filter += " || ?status = '" + one_filter + "'"

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
SELECT ?aop ?aop_title ?status ?aop_id
WHERE {

  ?aop a aopo:AdverseOutcomePathway ;
       dc:title ?aop_title ;
       rdfs:label ?aop_id ;
       nci:C25688 ?status .

  FILTER (""" + aop_filter + """)
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def aop_status_initialization():
    '''Filter AOPs '''
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
SELECT ?aop ?aop_title ?status ?aop_id
WHERE {

  ?aop a aopo:AdverseOutcomePathway ;
       dc:title ?aop_title ;
       rdfs:label ?aop_id ;
       nci:C25688 ?status .

  FILTER (?status = 'EAGMST Under Review' || ?status = 'WPHA/WNT Endorsed' || ?status = 'EAGMST Approved' || ?status = 'Under Development')
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        ###print(csv_format)
        '''for x in json_format['results']['bindings']:
            print(x)'''
        # if needed convert JSON to CSV.
        # TODO: return the dictionary for data manipulation
        return json_format
    except Exception as e:
        print(e)


def life_stage_filter_search(aop_id, life_stages):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    # Join life stages into a SPARQL-compatible filter
    life_stage_filter = " || ".join(
        ["?lifeStage = '" + stage + "'" for stage in life_stages]
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery(f"""
SELECT DISTINCT ?aop
WHERE {{
  ?aop a aopo:AdverseOutcomePathway ;
       dc:identifier aop:{aop_id} ;
       aopo:LifeStageContext ?lifeStage .
  FILTER ({life_stage_filter})
}}
    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def sex_filter_search(aop_id, sex):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery("""
SELECT DISTINCT ?aop
WHERE {

  ?aop a aopo:AdverseOutcomePathway ;
       dc:identifier aop:""" + aop_id + """ ;
       pato:0000047 '""" + sex + """' .
}
                        """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def organ_filter_search(aop_id, organs):
    # endpoint sparql
    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")

    organ_filter = " || ".join(["?organTitle = '" + organ + "'" for organ in organs])

    sparql.setReturnFormat(JSON)
    sparql.setQuery(f"""
    SELECT DISTINCT ?AOP
    WHERE {{
      ?AOP a aopo:AdverseOutcomePathway;
           dc:identifier aop:{aop_id} ;
           aopo:has_key_event ?ke .
      ?ke aopo:OrganContext ?organ .
      ?organ dc:title ?organTitle .
      FILTER ({organ_filter})
    }}
    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def cell_filter_search(aop_id, cells):
    # endpoint sparql
    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")

    cell_filter = " || ".join(["?cellTitle = '" + cell + "'" for cell in cells])

    sparql.setReturnFormat(JSON)
    sparql.setQuery(f"""
    SELECT DISTINCT ?AOP
    WHERE {{
      ?AOP a aopo:AdverseOutcomePathway;
           dc:identifier aop:{aop_id} ;
           aopo:has_key_event ?ke .
      ?ke aopo:CellTypeContext ?cell .
      ?cell dc:title ?cellTitle .
      FILTER ({cell_filter})
    }}
    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)


def taxonomic_filter_search(aop_id, tax_titles):
    # endpoint sparql
    sparql = SPARQLWrapper(
        "https://aopwiki.rdf.bigcat-bioinformatics.org/sparql"
    )

    tax_filter = " || ".join(
        ["?taxTitle = '" + title + "'" for title in tax_titles]
    )

    sparql.setReturnFormat(JSON)
    sparql.setQuery(f"""
SELECT DISTINCT ?AOP
WHERE {{
  ?AOP a aopo:AdverseOutcomePathway ;
       dc:identifier aop:{aop_id} ;
       aopo:has_key_event ?ke .
  ?ke ncbitaxon:131567 ?tax .
  ?tax dc:title ?taxTitle .
  FILTER ({tax_filter})
}}
    """)

    try:
        ret = sparql.query()
        json_format = ret.convert()
        return json_format
    except Exception as e:
        print(e)
