function fetchAliasSymbols(geneSymbol) {
    const url = `https://rest.genenames.org/fetch/symbol/${geneSymbol}`;
    const headers = {
        'Accept': 'application/json'
    };

    return fetch(url, { headers })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.response.numFound > 0) {
                return data.response.docs[0].alias_symbol || []; // Return alias symbols or an empty array if none
            } else {
                return [];
            }
        })
        .catch(error => {
            console.error('Error fetching data from HGNC API:', error);
            return [];
        });
}

