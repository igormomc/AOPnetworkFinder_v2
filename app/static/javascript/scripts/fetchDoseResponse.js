async function fetchDoseResponse() {
    const url = `/api/dose_response`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Dose-response assays fetched:', data);
        return data;
    } catch (error) {
        console.error('Error fetching dose-response assays:', error);
        return null;
    }
}