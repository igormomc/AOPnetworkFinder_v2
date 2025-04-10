async function fetchGeneEnrichment(keList) {
    const url = `/api/gene_enrichment?keList=${keList}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Genes enrichment fetched:', data);
        return data;
    } catch (error) {
        console.error('Error fetching genes enrichment:', error);
        return null;
    }
}
