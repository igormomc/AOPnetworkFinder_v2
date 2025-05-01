import os
import requests
import pandas as pd
from dotenv import load_dotenv

#api credentials
load_dotenv(".env")
host = os.getenv("ctx_api_host")
api_key = os.getenv("ctx_api_x_api_key")

#headers for sending toxcast requests
headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json',
    'x-api-key': api_key
}

#get all the assay endpoints from the ToxCast API
def all_assay(headers: dict) -> str:
    assays_url = 'https://api-ccte.epa.gov/bioactivity/assay/'
    response = requests.get(assays_url, headers = headers)
    if response.status_code == 200:
        odata = response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
    return odata


#convert to a dataframe
all_assay_json = all_assay(headers)
df = pd.DataFrame(all_assay_json, dtype=object)

#keep only the columns of interest
info = df[['aeid', 'assayComponentEndpointName', 'organismId','assaySourceLongName','organism', 'tissue', 'cellFreeComponentSource', 'assayFormatType', 'citations','gene', 'assayDesignType', 'assayDesignTypeSub', 'biologicalProcessTarget', 'detectionTechnologyType', 'detectionTechnology','assayName']]

#split the gene information into separate columns
info_genes = pd.concat([info.drop(['gene'], axis=1), info['gene'].apply(pd.Series, dtype="object").drop(labels= 'organismId', axis = 1)], axis=1)
print(info_genes.groupby(['organismId', 'organism']).size().reset_index(name='counts').sort_values(['organismId', 'counts'], ascending=[True, False])) #stats
info_genes.to_csv('toxcast_assays_genes.csv', encoding='utf-8', index=False)

#import the KE data from AOP wiki
ke_doa = pd.read_csv('aopwiki_KE_da.csv', dtype = 'object').drop(columns=['index','title'], axis=1)
toxcast_df = pd.read_csv('toxcast_assays_genes.csv',  dtype={'organismId': object, 'geneId': float, 'entrezGeneId': float})

#fix the data types
toxcast_df['geneId'] = toxcast_df['geneId'].fillna(0).astype('int64')
toxcast_df['entrezGeneId'] = toxcast_df['entrezGeneId'].fillna(0).astype('int64')

#merge and keep the unique entries
organism_df = pd.merge(ke_doa, toxcast_df, how = 'inner', left_on=['organismId','organ'], right_on=['organismId','tissue'])
organism_df_dedup = organism_df.drop_duplicates(subset=['organismId','organ','entrezGeneId'], keep='first')
organism_df_dedup.to_csv('organism_organ_doa.csv', index = False)