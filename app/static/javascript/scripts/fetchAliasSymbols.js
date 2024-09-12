async function fetchAliasSymbols(geneSymbol) {
    const url = `https://rest.genenames.org/fetch/symbol/${geneSymbol}`;
    const headers = { 'Accept': 'application/json' };

    try {
        const response = await fetch(url, { headers });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const { response: { numFound, docs } } = await response.json();

        if (numFound > 0) {
            const { alias_symbol, prev_symbol } = docs[0];
            return [alias_symbol, prev_symbol];
        }

        return [];

    } catch (error) {
        console.error('Error fetching data from HGNC API:', error);
        return [];
    }
}
