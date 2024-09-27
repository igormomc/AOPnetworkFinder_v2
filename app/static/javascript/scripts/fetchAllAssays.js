async function fetchBioactivityAssays() {
    const url = `/api/bioactivity-assays`; // Use Flask proxy

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
