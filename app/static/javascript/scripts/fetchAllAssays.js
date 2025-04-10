async function fetchBioactivityAssays() {
    const url = `/api/bioactivity-assays`; // Use Flask proxy

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching bioactivity assays:', error);
        return null;
    }
}


async function fetchDomainOfApplicationAssays(aop_id) {
    const url = `/api/read_assays_domainApp`;

    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching bioactivity assays:', error);
        return null;
    }
}