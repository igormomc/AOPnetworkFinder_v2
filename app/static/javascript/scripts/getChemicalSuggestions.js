async function getChemicalSuggestions(aop_id) {
    const url = `/api/get_chemical_suggestions?aop_id=${aop_id}`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Bioactivity assays fetched:', data);
        return data;
    } catch (error) {
        console.error('Error fetching bioactivity assays:', error);
        return null;
    }
}
