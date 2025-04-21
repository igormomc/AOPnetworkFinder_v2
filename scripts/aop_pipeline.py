#!/usr/bin/env python3
"""
AOP Pipeline Script
    * If you want to regenerate the grouped_assays ensure to have ran process_assays from getAssaysReadToFIle.py first
    * If you want to regenerate the assayDataForChem.json file, run the toxCastParser.py script
    * If you want to regenerate the aop-key-gene-sparql.json file, run the following command in https://aopwiki.rdf.bigcat-bioinformatics.org/ and downloade the file a JSON file and call it aop-key-gene-sparql.json:
    SELECT ?aop ?label ?keyEventName ?geneOnKeyEvent
        WHERE {
         ?aop a aopo:AdverseOutcomePathway ;
            rdfs:label            ?label ;
            aopo:has_key_event    ?ke .

        ?ke  a aopo:KeyEvent ;
            rdfs:label            ?keyEventName .

        OPTIONAL {
            ?ke edam:data_1025      ?geneOnKeyEvent .
            }
        }

    


  To run all the scripts and produce the final output, run:
  python3 aop_pipeline.py all \
  --assay assayDataForChem.json \
  --chemdata assayWithChemData.json \
  --chemlist chemicalToDsstox.json
"""
import json
import argparse
import sys


def build_mapping(input_sparql_file, output_mapping_file):
    with open(input_sparql_file, 'r') as f:
        data = json.load(f)
    aop_mapping = {}
    for binding in data.get('results', {}).get('bindings', []):
        if 'keyEventName' not in binding:
            continue
        aop_id = binding['label']['value']
        key_event = binding['keyEventName']['value']
        aop_mapping.setdefault(aop_id, {}).setdefault(key_event, [])
        if 'geneOnKeyEvent' in binding:
            gene = binding['geneOnKeyEvent']['value']
            if gene not in aop_mapping[aop_id][key_event]:
                aop_mapping[aop_id][key_event].append(gene)
    with open(output_mapping_file, 'w') as f:
        json.dump(aop_mapping, f, indent=4)
    print(f"Built mapping: {output_mapping_file}")


def filter_mapping(mapping_file, assay_data_file, output_file):
    with open(mapping_file, 'r') as f:
        aop_mapping = json.load(f)
    with open(assay_data_file, 'r') as f:
        assay_data = json.load(f)
    filtered = {}
    for aop, kes in aop_mapping.items():
        filtered[aop] = {}
        for ke, urls in kes.items():
            endpoints = []
            for url in urls:
                symbol = url.rstrip('/').split('/')[-1]
                if symbol in assay_data:
                    for assay in assay_data[symbol]:
                        ep = assay.get('assayComponentEndpointName')
                        if ep and ep not in endpoints:
                            endpoints.append(ep)
            filtered[aop][ke] = endpoints
    with open(output_file, 'w') as f:
        json.dump(filtered, f, indent=4)
    print(f"Filtered mapping: {output_file}")


def chem_summary(filtered_mapping_file, assay_chem_data_file, original_mapping_file, output_file):
    with open(filtered_mapping_file, 'r') as f:
        filtered = json.load(f)
    with open(assay_chem_data_file, 'r') as f:
        chem_data = json.load(f)
    with open(original_mapping_file, 'r') as f:
        original = json.load(f)
    summary = {}
    for aop, kes in filtered.items():
        counts = {}
        events_with = len(kes)
        total_kes = len(original.get(aop, {}))
        for ke, eps in kes.items():
            chems = set()
            for ep in eps:
                if ep in chem_data:
                    chems.update(chem_data[ep].keys())
            for chem in chems:
                counts[chem] = counts.get(chem, 0) + 1
        if counts:
            max_count = max(counts.values())
            best = [c for c, cnt in counts.items() if cnt == max_count]
            key = f"{max_count}/{events_with}/{total_kes}"
            summary[aop] = {key: best}
        else:
            summary[aop] = {}
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=4)
    print(f"Chemical summary: {output_file}")


def replace_ids(test_file, chemical_file, output_file):
    with open(test_file, 'r') as f:
        data = json.load(f)
    with open(chemical_file, 'r') as f:
        chem_list = json.load(f)
    lookup = {e['dsstox_substance_id']: e['chnm'] for e in chem_list if e.get('dsstox_substance_id') and e.get('chnm')}
    for aop, kes in data.items():
        for ke, ids in kes.items():
            data[aop][ke] = [lookup.get('DTXSID'+cid, 'DTXSID'+cid) for cid in ids]
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"Replaced IDs: {output_file}")


def stats(mapping_file):
    with open(mapping_file, 'r') as f:
        mapping = json.load(f)
    total = len(mapping)
    aops_no_genes = []
    kes_no_genes = set()
    for aop, kes in mapping.items():
        has_gene = False
        for ke, genes in kes.items():
            if genes:
                has_gene = True
            else:
                kes_no_genes.add(ke)
        if not has_gene:
            aops_no_genes.append(aop)
    print(f"Total AOPs: {total}")
    print(f"AOPs without genes ({len(aops_no_genes)}): {aops_no_genes}")
    print(f"Key events without genes ({len(kes_no_genes)}): {sorted(kes_no_genes)}")


def main():
    parser = argparse.ArgumentParser(description="AOP analysis pipeline")
    sub = parser.add_subparsers(dest='cmd')

    p_build = sub.add_parser('build', help='Build AOP-gene mapping')
    p_build.add_argument('-i', '--input', default='aop-key-gene-sparql.json')
    p_build.add_argument('-o', '--output', default='aop_mapping.json')

    p_filter = sub.add_parser('filter', help='Filter mapping by assay data')
    p_filter.add_argument('-m', '--mapping', default='aop_mapping.json')
    p_filter.add_argument('-a', '--assay', required=True)
    p_filter.add_argument('-o', '--output', default='aop_mapping_filtered.json')

    p_cs = sub.add_parser('chem-summary', help='Summarize most-tested chemicals')
    p_cs.add_argument('-f', '--filtered', default='aop_mapping_filtered.json')
    p_cs.add_argument('-c', '--chemdata', required=True)
    p_cs.add_argument('-r', '--original', default='aop_mapping.json')
    p_cs.add_argument('-o', '--output', default='aop_chem_summary.json')

    p_rep = sub.add_parser('replace-ids', help='Replace chemical IDs with names')
    p_rep.add_argument('-t', '--test', default='aop_chem_summary.json')
    p_rep.add_argument('-c', '--chemical', required=True)
    p_rep.add_argument('-o', '--output', default='aop_chem_summary_named.json')

    p_stats = sub.add_parser('stats', help='Report AOPs/key events without genes')
    p_stats.add_argument('-m', '--mapping', default='aop_mapping.json')

    p_all = sub.add_parser('all', help='Run all steps in order')
    p_all.add_argument('-s', '--sparql', default='aop-key-gene-sparql.json')
    p_all.add_argument('-a', '--assay', required=True)
    p_all.add_argument('-c', '--chemdata', required=True)
    p_all.add_argument('-l', '--chemlist', required=True)

    args = parser.parse_args()
    if args.cmd == 'build':
        build_mapping(args.input, args.output)
    elif args.cmd == 'filter':
        filter_mapping(args.mapping, args.assay, args.output)
    elif args.cmd == 'chem-summary':
        chem_summary(args.filtered, args.chemdata, args.original, args.output)
    elif args.cmd == 'replace-ids':
        replace_ids(args.test, args.chemical, args.output)
    elif args.cmd == 'stats':
        stats(args.mapping)
    elif args.cmd == 'all':
        build_mapping(args.sparql, 'aop_mapping.json')
        filter_mapping('aop_mapping.json', args.assay, 'aop_mapping_filtered.json')
        chem_summary('aop_mapping_filtered.json', args.chemdata, 'aop_mapping.json', 'aop_chem_summary.json')
        replace_ids('aop_chem_summary.json', args.chemlist, 'aop_chem_summary_named.json')
        stats('aop_mapping.json')
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
