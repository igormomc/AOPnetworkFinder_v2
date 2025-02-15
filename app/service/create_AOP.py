from SPARQLWrapper import SPARQLWrapper, JSON
import json
from app.service.visualize_AOP import print


def aop_dump(aop_id):  # endpoint sparql
    sparql = SPARQLWrapper("https://aopwiki.rdf.bigcat-bioinformatics.org/sparql")
    if aop_id.isdigit():
        sparql.setReturnFormat(JSON)
        sparql.setQuery(f"""SELECT DISTINCT ?AOP ?MIE ?KE_up ?KE_dwn ?AO ?ker_genes ?aop_id ?aop_label ?ke_id ?ke_label ?ke_title ?ke_genes ?ke_dwn_label ?ke_dwn_id ?ke_dwn_title ?ke_dwn_genes
                        WHERE{{  BIND(aop:{aop_id} AS ?aop_id)  ?AOP a aopo:AdverseOutcomePathway ;      
                        dc:identifier ?aop_id;      
                        rdfs:label ?aop_label .  OPTIONAL {{ ?AOP aopo:has_molecular_initiating_event ?MIE . }}  OPTIONAL {{ ?AOP aopo:has_adverse_outcome ?AO . }}  ?AOP aopo:has_key_event ?KE_up .  ?KE_up dc:identifier ?ke_id ;
                        rdfs:label ?ke_label ;        
                        dc:title ?ke_title .  OPTIONAL {{ ?KE_up edam:data_1025 ?ke_genes . }}  OPTIONAL {{    ?AOP aopo:has_key_event_relationship ?KER .    
                        ?KER a aopo:KeyEventRelationship ;        
                        aopo:has_upstream_key_event ?KE_up ;        
                        aopo:has_downstream_key_event ?KE_dwn .    #OPTIONAL {{ ?KER edam:data_1025 ?ker_genes . }}    
                        ?KE_dwn dc:identifier ?ke_dwn_id ;            rdfs:label ?ke_dwn_label ;            dc:title ?ke_dwn_title .    OPTIONAL {{ ?KE_dwn edam:data_1025 ?ke_dwn_genes . }}  }}}}""")
        try:
            ret = sparql.query()
            json_format = ret.convert()
            return json_format
        except Exception as e:
            print(e)


def add_AOP_variable_by_keid(AOP, new_var_dict, new_var_name="AC50"):
    for node in AOP:
        for key in new_var_dict:
            if AOP[node]["KE_id"] == key:
                AOP[node][new_var_name] = new_var_dict[key]
    return AOP


def build_AOP(result, MIES, AOS, ordered_nodes):
    AOP = {}
    for i, node in enumerate(ordered_nodes):
        key = f"KE{i}"
        if node in AOS:
            key = f"AO{AOS.index(node)}"
        if node in MIES:
            key = f"MIE{MIES.index(node)}"
        ke_title = ""
        ke_id = node
        ke_genes = []
        genesseen = set()
        for binding in result["results"]["bindings"]:
            label = binding["ke_label"]["value"]
            title = binding["ke_title"]["value"]
            gene = binding["ke_genes"]["value"].split("/")[-1] if "ke_genes" in binding else ""
            if label == f"KE {node}":
                ke_title = title
                if gene not in genesseen:
                    ke_genes.append(gene)
                    genesseen.add(gene)
        AOP[key] = {
            "name": ke_title,
            "connections": [],
            "genes": ke_genes,
            "KE_id": ke_id
        }

    return AOP


def get_nodes_in_apparition_order(result, connections):
    temp_connections = [connection for connection in connections]
    ordered_nodes = [result["results"]["bindings"][0]["MIE"]["value"].split("/")[-1]]
    i = 0
    seen = set()  # This will keep track of items we've already seen
    while temp_connections:
        previous_node = ordered_nodes[i]
        connections_left = []
        for connection in temp_connections:
            if connection[0] == previous_node:
                if connection[1] not in seen:
                    ordered_nodes.append(connection[1])
                    seen.add(connection[1])
            else:
                connections_left.append(connection)

        # Let's not forget the useless ones that don't have MIE as an ancestor
        temp_connections = connections_left
        connections_left = []
        for connection in temp_connections:
            if connection[1] == previous_node:
                if connection[0] not in seen:
                    ordered_nodes.append(connection[0])
                    seen.add(connection[0])
            else:
                connections_left.append(connection)
        temp_connections = connections_left
        i += 1
    return ordered_nodes


def find_AO_and_MIE(result):
    seen_AO = set()
    seen_MIE = set()
    MIES = []
    AOS = []
    for binding in result["results"]["bindings"]:
        node = binding["MIE"]["value"].split("/")[-1]
        if node not in seen_MIE:
            MIES.append(node)
            seen_MIE.add(node)

        node = binding["AO"]["value"].split("/")[-1]
        if node not in seen_AO:
            AOS.append(node)
            seen_AO.add(node)
    return MIES, AOS


def collect_connections_in_AOP(result):
    connections = []
    seen = set()  # This will keep track of items we've already seen

    for binding in result["results"]["bindings"]:
        if "KE_dwn" in binding:
            conn = (binding['KE_up']["value"].split("/")[-1],
                    binding['KE_dwn']["value"].split("/")[-1]
                    )

            if conn not in seen:
                connections.append(conn)
                seen.add(conn)
    return connections


def add_connections_to_AOP(connections, AOP):
    for connection in connections:
        for node in AOP:
            if connection[1] == AOP[node]["KE_id"]:
                connection = (connection[0], node)
        for node in AOP:
            if connection[0] == AOP[node]["KE_id"]:
                AOP[node]["connections"].append(connection[1])


def create_AOP_from_scratch(aop_id):
    result = aop_dump(aop_id)
    connections = collect_connections_in_AOP(result)
    MIES, AOS = find_AO_and_MIE(result)
    ordered_nodes = get_nodes_in_apparition_order(result, connections)
    AOP = build_AOP(result, MIES, AOS, ordered_nodes)
    add_connections_to_AOP(connections, AOP)
    return AOP


def add_proba_by_keid(AOP, proba):
    add_AOP_variable_by_keid(AOP=AOP, new_var_dict=proba, new_var_name="P(prior|event)")
