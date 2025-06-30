import app.SPARQL_QUERIES.data_displayer_queries as dp_queries


def query_sparql(list_of_checkboxes, aop_input, ke_input):
    json_file, column_header = dp_queries.one_aop(list_of_checkboxes,
                                                  ke_input, aop_input)

    prefix_removed = [term.replace('?', '') for term in column_header if '?' in term]

    return json_file, prefix_removed
