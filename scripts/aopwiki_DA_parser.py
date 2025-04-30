import gzip
import json
import requests
import pandas as pd
from tqdm import tqdm
import datetime as date
import xmltodict as xtd

#function to downlod the nightly release file from AOPwiki
def download_nightly_release(url, filename):
    response = requests.get(url, stream=True, verify=False) #bypass SSL certificate verification
    with open(filename, "wb") as handle:
        for data in tqdm(response.iter_content(chunk_size=1024), unit="kB"):
            handle.write(data)

#download the nightly release file from AOPwiki
download_nightly_release('http://aopwiki.org/downloads/aop-wiki-xml.gz', 'aop-wiki-xml.gz')

#read the xml file and convert it to json, save a copy of the json file
date = date.datetime.now().strftime("%d%M%Y")
with gzip.open('aop-wiki-xml.gz', 'rb') as f:
    xml_data = xtd.parse(f.read())
    json_data = json.dumps(xml_data)
    with open(f"aopwiki_{date}.json", "w") as json_file:
        json_file.write(json_data)

#dictionary to map the taxnomy id to the organism name for missing taxons
tax_dict = {
    "insects": "50557",
    "rat": "10116",
    "mouse": "10090",
    "human": "9606",
    "fish": "7955",
    "frog": "8364",
    "all species": "131567",
    "chickens": "9031",
    "rodents": "10116",
    "rodentia": "10116",
    "pig": "9823",
    "human and other cells in culture": "9606",
    "monkey": "9544",
    "ducks": "8839",
    "mammals": "40674",
    "vertebrates": "7742",
    "invertebrates": "50557",
    "double-crested cormorant": "56069",
    "eastern bluebird": "172413",
    "hamster": "10037",
    "turkeys": "9103",
    "hydra": "6083",
    "honey bee": "7460",
    "melibe leonine": "76178",
    "tritonea diomedea": "2780533",
    "chaetanaphothrips orchidii": "1675519",
    "hymenoptera": "7399",
    "lepidoptera": "7088",
    "orius isidiosus": "83647",
    "sprague-dawley": "10116",
    "common starling": "9172"
}


"""
TO DO: 

Create a class for the AOP XML object
class AOPWikiParser?

"""

#AOPwiki data extraction
def extract_id(wiki_data: dict, db_name:str, id: str) -> str:
    term_list = wiki_data.get('vendor-specific').get(db_name)
    for term in term_list:
        if term.get('@id') == id:
            return term.get('@aop-wiki-id')

def extract_taxon(id: str) -> list:
    term_list = xml_data.get('data').get('taxonomy')
    taxon_list = []
    taxon =''
    for term in term_list:
        if term.get('@id') == id:
            taxon = term.get('source-id').replace('WCS_','')
            if taxon.startswith('Wiki'):
                t = term.get('name').split(',')
                x = set()
                for i in t:
                    n = i.lstrip(' ').lower()
                    x.add(tax_dict.get(n))
                    if tax_dict.get(n) is None:
                        print(f'Taxonomy id not found for {n}')
                taxon_list.extend([*x])
            else:
                taxon_list.append(taxon)
    return taxon_list

#KE domain of applicability extraction
def ke_taxonomy(wiki_dict: dict) -> dict:
    ke_tax = {}
    for ke in wiki_dict.get('data').get('key-event'):
        _d = {}
        ke_id = f'KE {extract_id(wiki_dict.get('data'), 'key-event-reference', ke.get('@id'))}'
        _d['title'] = ke.get('title')
        
        #organ information
        if ke.get('organ-term'):
            _d['organ'] = ke.get('organ-term').get('name')
        
        #species information
        doa = ke.get('applicability')
        organism = list()
        sex = list()
        lifestage = list()
        if doa:
            t = doa.get('taxonomy')
            s = doa.get('sex')
            l = doa.get('life-stage')
            
            if t:
                if isinstance(t, list):
                    for x in t:
                        organism.extend(extract_taxon(x.get('@taxonomy-id')))
                else:
                        organism.extend(extract_taxon(t.get('@taxonomy-id')))
            else:
                organism.append('Not specified')
            if s:
                if isinstance(s, list):
                    sex = [x.get('sex') for x in s]
                else:
                        sex = [s.get('sex')]
            else:
                sex.append('Not specified')
            if l:                        
                if isinstance(l, list):
                    lifestage = [x.get('life-stage') for x in l]
                else:
                        lifestage = [l.get('life-stage')]
            else:
                lifestage.append('Not specified')
        else:
            organism.append('Not specified')
            sex.append('Not specified')
            lifestage.append('Not specified')

        _d['organismId'] = organism
        _d['sex'] = sex
        _d['lifestage'] = lifestage 
        ke_tax[ke_id] = _d
    return ke_tax

#extract and test the output
ke_info = ke_taxonomy(xml_data)

#create dataframe from the dictionary
ke_df = pd.DataFrame(ke_info).T.reset_index()
#repeat row for each organism
ke_df = ke_df.explode('organismId').reset_index(drop=True)

#print number of unique key events
print(f'Number of unique key events: {ke_df["index"].nunique()}')

#save the context file in
ke_df.to_csv('aopwiki_KE_da.csv', encoding='utf-8', index=False)