from app.service.constants import life_stage_mapping, taxonomic_mapping, cell_groups, organ_groups


def group_cells(cells):
    reverse_lookup = {}
    for primary_term, synonyms in cell_groups.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_cells = {}
    for cell in cells:
        primary_term = reverse_lookup.get(cell, cell)
        if primary_term not in grouped_cells:
            grouped_cells[primary_term] = [cell]
        elif cell != primary_term:
            grouped_cells[primary_term].append(cell)
    return grouped_cells


def group_life_stages(life_stages):
    reverse_lookup = {}
    for primary_term, synonyms in life_stage_mapping.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_life_stages = {}
    for stage in life_stages:
        primary_term = reverse_lookup.get(stage, stage)
        if primary_term not in grouped_life_stages:
            grouped_life_stages[primary_term] = [stage]
        elif stage != primary_term:
            grouped_life_stages[primary_term].append(stage)
    return grouped_life_stages


def group_taxonomic_groups(taxonomic_groups):
    reverse_lookup = {}
    for primary_term, synonyms in taxonomic_mapping.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_taxonomic_groups = {}
    for group in taxonomic_groups:
        primary_term = reverse_lookup.get(group, group)
        if primary_term not in grouped_taxonomic_groups:
            grouped_taxonomic_groups[primary_term] = [group]
        elif group != primary_term:
            grouped_taxonomic_groups[primary_term].append(group)
    return grouped_taxonomic_groups


def group_organs(organs):
    reverse_lookup = {}
    for primary_term, synonyms in organ_groups.items():
        for synonym in synonyms:
            reverse_lookup[synonym] = primary_term

    grouped_organs = {}
    for organ in organs:
        primary_term = reverse_lookup.get(organ, organ)
        if primary_term not in grouped_organs:
            grouped_organs[primary_term] = [organ]
        # Only append if the organ isn't already the primary term (avoids duplicates)
        elif organ != primary_term:
            grouped_organs[primary_term].append(organ)
    return grouped_organs
