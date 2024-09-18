async function testApi(gene) {
    console.log("Testing API...");
    const url = `https://comptox.epa.gov/dashboard-api/ccdapp1/search/assay/contain/${gene}`;

    try {
        const response = await fetch(url);
        if (response.ok) {
            const data = await response.json();  // Parse the response body as JSON
            console.log('Response Data:', data);  // Log the actual JSON data
            //if data is empty array return false else return true
            if (data.length === 0) {
                return false;
            } else {
                return true;
            }
        } else {
            console.error('Error:', response.statusText);
        }
    } catch (error) {
        console.error('Error fetching assays:', error);
    }
}
