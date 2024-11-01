from app.service.constants import life_stage_mapping, taxonomic_mapping, cell_groups, organ_groups

def group_life_stages(life_stages):
    reverse_lookup = {}
    for primary_term, synonyms in life_stage_mapping.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    # Create the result dictionary, initializing with unique terms from life_stages that don't have synonyms
    grouped_life_stages = {term: [term] for term in life_stages if term not in reverse_lookup}

    # Populate grouped lists based on reverse lookup
    for stage in life_stages:
        primary_term = reverse_lookup.get(stage, stage)  # Defaults to original if no group is found
        grouped_life_stages.setdefault(primary_term, []).append(stage)

    return grouped_life_stages


def group_taxonomic_groups(taxonomic_groups):
    reverse_lookup = {}
    for primary_term, synonyms in taxonomic_mapping.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_taxonomic_groups = {term: [term] for term in taxonomic_groups if term not in reverse_lookup}

    for group in taxonomic_groups:
        primary_term = reverse_lookup.get(group, group)  # Defaults to original if no group is found
        grouped_taxonomic_groups.setdefault(primary_term, []).append(group)

    return grouped_taxonomic_groups

def group_organs(organs):
    reverse_lookup = {}
    for primary_term, synonyms in organ_groups.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_organs = {term: [term] for term in organs if term not in reverse_lookup}

    for organ in organs:
        primary_term = reverse_lookup.get(organ, organ)
        grouped_organs.setdefault(primary_term, []).append(organ)

    return grouped_organs


def group_cells(cells):
    reverse_lookup = {}
    for primary_term, synonyms in cell_groups.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_cells = {term: [term] for term in cells if term not in reverse_lookup}

    for cell in cells:
        primary_term = reverse_lookup.get(cell, cell)
        grouped_cells.setdefault(primary_term, []).append(cell)

    return grouped_cells