//Global variable for storing the graph strucutr

let globalGraphJson = [];
let globalMergeJson = [];
let globalUserActionsLog = [];
let allowHidePopup = false; // Flag to control the hiding of the popup
var cy;
let geneHGNCurl = 'https://www.genenames.org/data/gene-symbol-report/#!/symbol/';
let doseKeyeventsWithInfo = [];
let chemicalSuggestions = [];

let isColorBlindMode = false; // Track the color mode state
const defaultColors = {
    "Molecular Initiating Event": "#00A79D",
    "Adverse Outcome": "#ED1C24",
    "Key Event": "#F7941D",
    "genes": "#27AAE1",
};

const colorBlindColors = {
    "Molecular Initiating Event": "#40E0D0",
    "Adverse Outcome": "#FF00FF",
    "Key Event": "#007FFF",
    "genes": "#708090",
};

let assayGenesDict = null;
let userUploadedData = null;


let lastClickTime = 0;
const doubleClickThreshold = 300; // Milliseconds

let toastTimeout;

function ShowToaster(message, color, autoRemove = true) {
    var x = document.getElementById("ShowToaster");

    if (toastTimeout) {
        clearTimeout(toastTimeout);
        toastTimeout = null;
    }

    x.querySelector("span").textContent = message;
    x.style.backgroundColor = color;
    x.classList.add("show");

    if (autoRemove) {
        toastTimeout = setTimeout(function () {
            x.classList.remove("show");
        }, 5000);
    }

    x.querySelector(".close-toast").onclick = function () {
        x.classList.remove("show");
    };
}


// Function to update gene visibility based on checkbox states
function updateGeneVisibility() {
    const showGenes = document.getElementById('checkedBoxGene').checked;
    const showAssayGenesOnly = document.getElementById('checkedAssayGenes').checked;

    if (showAssayGenesOnly) {
        cy.nodes().filter('[ke_type="genes"]').addClass('hidden');
        cy.edges().filter(function (edge) {
            return edge.source().data('ke_type') === 'genes' || edge.target().data('ke_type') === 'genes';
        }).addClass('hidden');

        cy.nodes().filter(function (node) {
            return node.data('ke_type') === 'genes' && assayGenesDict && assayGenesDict[node.data('name')];
        }).removeClass('hidden');

        cy.edges().filter(function (edge) {
            const sourceIsAssayGene = edge.source().data('ke_type') === 'genes' && assayGenesDict && assayGenesDict[edge.source().data('name')];
            const targetIsAssayGene = edge.target().data('ke_type') === 'genes' && assayGenesDict && assayGenesDict[edge.target().data('name')];
            return sourceIsAssayGene || targetIsAssayGene;
        }).removeClass('hidden');
    } else if (showGenes) {
        cy.nodes().filter('[ke_type="genes"]').removeClass('hidden');
        cy.edges().filter(function (edge) {
            return edge.source().data('ke_type') === 'genes' || edge.target().data('ke_type') === 'genes';
        }).removeClass('hidden');
    } else {
        cy.nodes().filter('[ke_type="genes"]').addClass('hidden');
        cy.edges().filter(function (edge) {
            return edge.source().data('ke_type') === 'genes' || edge.target().data('ke_type') === 'genes';
        }).addClass('hidden');
    }

    cy.style()
        .selector('.hidden')
        .style({
            'display': 'none'
        })
        .update();
}

document.getElementById('checkedBoxGene').addEventListener('change', function () {
    if (this.checked) {
        document.getElementById('checkedAssayGenes').checked = false;
    }
    updateGeneVisibility();
});

document.getElementById('checkedAssayGenes').addEventListener('change', function () {
    if (this.checked) {
        document.getElementById('checkedBoxGene').checked = false;
    }
    updateGeneVisibility();
});


function groupAssaysByGeneSymbol(assays) {
    const geneAssayMap = {};

    assays.forEach(assay => {
        const geneSymbol = assay?.gene?.geneSymbol;
        if (!geneAssayMap[geneSymbol]) {
            geneAssayMap[geneSymbol] = [];
        }
        geneAssayMap[geneSymbol].push(assay);
    });

    return geneAssayMap;
}

//sending the user inputted values to the backend for processing
// Add the bioactivity call within the searchButtonAOP click event listener
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById("searchFieldAOP").addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            event.preventDefault();
            document.getElementById("searchButtonAOP").click();
        }
    });


    document.getElementById("searchButtonAOP").addEventListener("click", async function (event) {
        event.preventDefault();
        document.getElementById("loader").style.display = "flex";

        //reset the graph for each new search
        document.getElementById('cy').innerHTML = '';
        document.getElementById('dynamicButtons').innerHTML = '';
        document.getElementById('nodeInfo').innerHTML = '';
        document.getElementById('nodePopup').style.display = 'none';


        // Global log file should be reset every time user generates a new graph. (new session)
        globalUserActionsLog = [];

        // Data that will be sent to the backend for processing
        var formData = new FormData();

        var searchValueAop = document.getElementById("searchFieldAOP").value;
        var searchValueKe = document.getElementById("searchFieldKE").value;
        var searchValueStressor = document.getElementById("stressorDropdown").value;
        var genesChecked = document.getElementById("checkedBoxGene").checked;
        var keDegreeSelection = document.querySelector('input[name="degree"]:checked').value;
        var organsDropdown = $('#organsDropdown').val();
        var taxonomiDropdown = $('#taxonomiDropdown').val();
        var lifeStageDropdown = $('#lifeStageDropdown').val();
        var sexDropdown = $('#sexDropdown').val();
        var cellsDropdown = $('#cellsDropdown').val();

        document.querySelectorAll('#checkbox-filter input[type="checkbox"]').forEach(function (checkbox) {
            formData.append(checkbox.name, checkbox.checked ? "1" : "0");
        });

        formData.append("checkboxGene", genesChecked ? "1" : "0");
        formData.append("keDegree", keDegreeSelection);

        if (searchValueAop || searchValueKe || searchValueStressor || organsDropdown || taxonomiDropdown || lifeStageDropdown || sexDropdown || cellsDropdown) {
            formData.append("searchFieldAOP", searchValueAop);
            formData.append("searchFieldKE", searchValueKe);
            formData.append("stressorDropdown", searchValueStressor);
            formData.append("organDropdown", organsDropdown);
            formData.append("taxValue", taxonomiDropdown);
            formData.append("lifeStageDropdown", lifeStageDropdown);
            formData.append("sexDropdown", sexDropdown);
            formData.append("cellValue", cellsDropdown);


            // Append the CSRF token to the FormData object
            var csrfToken = document.getElementById('csrf_token').value;
            formData.append('csrf_token', csrfToken);

            logUserInput(formData);

            // Fetch bioactivity assays before rendering the graph
            const bioactivityAssays = await fetchBioactivityAssays();
            if (bioactivityAssays) {
                assayGenesDict = groupAssaysByGeneSymbol(bioactivityAssays);
            }

            render_graph('/searchAops', formData);

        } else {
            ShowToaster("Please enter an AOP ID, KE ID or Stressor Name", "error");

        }
    });
});

async function displayNodeInfo(geneSymbol, node, keTypeColor) {
    try {
        const aliasSymbols = (await fetchAliasSymbols(geneSymbol)).flat().filter(symb => symb !== undefined);
        const assayInfo = assayGenesDict[geneSymbol];
        let connectedKEs = node.connectedEdges().map(edge => {
            // Check connected nodes
            const connectedNode = edge.source().id() === node.id() ? edge.target() : edge.source();
            if (connectedNode.data().ke_type !== 'genes') {
                // Format as clickable link
                let keId = connectedNode.data('ke_identifier').split('/').pop();
                return `<a href="${connectedNode.data('ke_identifier')}" target="_blank">${keId}</a>`;
            }
        }).filter(ke => ke !== undefined).join(', '); // Filter out undefined and join
        // Correctly format the table rows and cells for each piece of data
        let contentHtml = `<strong>Node Data: (<span style="color: ${keTypeColor};">${node.data().ke_type}</span>)</strong><br><div><table>`;
        const geneName = node.data('name');
        const geneNameHtml = geneName && geneName !== 'N/A' ? `<a href="${geneHGNCurl}${geneName}" target="_blank">${geneName}</a>` : 'N/A';

        contentHtml += `<tr><td>Name:</td><td> ${geneNameHtml}</td></tr>`;
        contentHtml += `<tr><td><strong>Alias and previous Symbols:</strong></td><td>${aliasSymbols.join(', ') || 'N/A'}</td></tr>`;
        contentHtml += `<tr><td><strong>Connected KE:</strong></td><td>${connectedKEs || 'N/A'}</td></tr>`;
        //we only show info about one of the assays even if there are multiple
        if (assayInfo && assayInfo.length > 0) {
            const assayComponentName = assayInfo[0].assayComponentName || 'N/A';
            const assayLink = assayComponentName !== 'N/A' ? `<a href="https://comptox.epa.gov/dashboard/assay-endpoints/${assayComponentName}" target="_blank">${assayComponentName}</a>` : 'N/A';
            contentHtml += `<tr><td><strong>Assay Name: </strong></td><td>${assayLink}</td></tr>`;

            if (assayInfo.length > 1) {
                contentHtml += `<tr><td colspan="2">See other Assays for this gene: <a href="https://comptox.epa.gov/dashboard/assay-endpoints?search=${geneSymbol}" target="_blank">Link</a></td></tr>`;
            }
        }
        contentHtml += `</table></div>`;

        // Set the HTML content for the node information display
        document.getElementById('nodeInfo').innerHTML = contentHtml;
    } catch (error) {
        console.error('Error fetching alias symbols:', error);
    }
}

//render AOP/AOP-network given user_input
function render_graph(url_string, formData) {
    fetch(url_string, {
        method: 'POST',
        body: formData,
        credentials: 'same-origin'
    })
        .then(response => response.json())
        .then(cyData => {
                globalGraphJson = cyData.elements;
                globalMergeJson = cyData['merge_options:'];
                console.log(globalMergeJson);

                const destinationDropdown = document.getElementById('keepNodeDropDown');
                const sourceDropdown = document.getElementById('loseNodeDropDown');
                const aopDropDown = document.getElementById('aopDropDown')

                loggingAopVisualized(cyData['aop_before_filter'], cyData['aop_after_filter']);
                populateMergeOptionsDropDown(destinationDropdown, sourceDropdown, globalGraphJson);
                populateHighlightAopDropDown(aopDropDown, cyData['aop_after_filter']);

                cy = cytoscape({
                    container: document.getElementById('cy'),
                    elements: {
                        nodes: globalGraphJson.nodes,
                        edges: globalGraphJson.edges
                    },
                    style: [
                        // Conditional styling based on 'ke_type' - node color
                        {
                            selector: 'node[ke_type="Molecular Initiating Event"]',
                            style: {
                                'label': 'data(id)',
                                'background-color': '#00A79D'  // Green for 'Key Event'
                            }
                        },
                        {
                            selector: 'node[ke_type="Adverse Outcome"]',
                            style: {
                                'label': 'data(id)',
                                'background-color': '#ED1C24'  // Red for 'Adverse Outcome'
                            }
                        },
                        {
                            selector: 'node[ke_type="Key Event"]',
                            style: {
                                'label': 'data(id)',
                                'background-color': '#F7941D'  // Orange for 'Key Event'
                            }
                        },
                        {
                            selector: 'node[ke_type="genes"]',
                            style: {
                                'label': 'data(id)',
                                'background-color': function (ele) {
                                    const geneSymbol = ele.data('name');
                                    // Check if the gene is in the assayGenesDict
                                    return assayGenesDict && assayGenesDict[geneSymbol] ? '#35d135' : '#27AAE1'; // Green if in assayGenesDict, otherwise blue
                                },
                                'width': 10,
                                'height': 10
                            }
                        },
                        {
                            selector: 'edge',
                            style: {
                                'width': 3,
                                'line-color': '#7A7A7A',
                                'target-arrow-color': '#7A7A7A',
                                'target-arrow-shape': 'triangle',
                                'curve-style': 'bezier',
                                'target-arrow-scale': 1.5,
                                'opacity': 1
                            }
                        },
                        {
                            selector: 'node.highlighted',
                            style: {
                                'background-opacity': 1,
                                'border-color': 'black',
                                'border-width': 2,
                                'border-opacity': 1,
                                'text-opacity': 1 // labels are visible for highlighted nodes
                            }
                        },
                        {
                            selector: 'node.non-highlighted',
                            style: {
                                'background-opacity': 0.3,
                                'text-opacity': 0, // Hide label text
                                'border-opacity': 0
                            }
                        }
                    ],
                    layout: {
                        name: 'cose',
                        idealEdgeLength: 100,
                        nodeRepulsion: function (node) {
                            return 400000;
                        },
                        animate: true,
                        animationDuration: 1000,
                        animationEasing: undefined,
                        fit: true,
                        padding: 30,
                        randomize: false,
                        componentSpacing: 100,
                        nodeOverlap: 50,
                        nestingFactor: 5,
                        gravity: 80,
                        numIter: 1000,
                        initialTemp: 200,
                        coolingFactor: 0.95,
                        minTemp: 1.0
                    }
                });
                cy.ready(function () {
                    cy.edges().forEach(function (edge) {
                        var sourceNode = edge.source();
                        var targetNode = edge.target();

                        if (sourceNode.data('ke_type') === 'genes' || targetNode.data('ke_type') === 'genes') {
                            edge.style('opacity', 0.5);
                        }
                    });
                });
                // Inside render_graph, after cy initialization
                setupEdgeAddition(cy);
                toggleGeneLabels(document.getElementById('toggleLabels').checked);
                toggleGenesNode(document.getElementById('checkedBoxGene').checked);
                updateGeneVisibility();
                if (isColorBlindMode) {
                    applyColorScheme(colorBlindColors);
                }
                createMergeButtons(globalMergeJson);

                cy.on('click', 'node', function (evt) {
                    console.log("Node clicked: ", evt.target);
                    const currentTime = new Date().getTime();
                    if (currentTime - lastClickTime <= doubleClickThreshold) {
                        const node = evt.target;
                        let keTypeColor = getColorByType(node.data().ke_type);
                        let contentHtml = `<strong>Node Data: (<span style="color: ${keTypeColor};">${node.data().ke_type}</span>)</strong><br><div><table>`;

                        if (node.data().ke_type === 'genes') {
                            // For Gene nodes
                            let geneSymbol = node.data('name');

                            // Fetch alias and prev symbols for the clicked gene
                            displayNodeInfo(geneSymbol, node, keTypeColor);

                        } else {

                            let upstreamKEs = [];
                            let downstreamKEs = [];
                            let connectedGenes = [];
                            let ke_aop_urls = node.data('ke_aop_urls') || [];

                            // Determine upstream, downstream KEs, and connected genes
                            node.connectedEdges().forEach(edge => {
                                const targetNode = edge.target();
                                const sourceNode = edge.source();

                                if (sourceNode.id() === node.id()) { // downstream
                                    downstreamKEs.push(targetNode.data('ke_identifier'));
                                } else { //upstream
                                    if (sourceNode.data().ke_type === 'genes') {
                                        connectedGenes.push(sourceNode.data('name'));
                                    } else {
                                        upstreamKEs.push(sourceNode.data('ke_identifier'));
                                    }
                                }
                            });

                            // no upstream/downstream or connected genes
                            if (upstreamKEs.length === 0) upstreamKEs.push('N/A');
                            if (downstreamKEs.length === 0) downstreamKEs.push('N/A');
                            if (connectedGenes.length === 0) connectedGenes.push('N/A');

                            // Generating the clickable KE in AOPs links
                            let keAopLinksHtml = ke_aop_urls.map(url => {
                                const match = url.match(/\/(\d+)$/);
                                if (match) {
                                    const aopId = match[1];
                                    return `<a href="${url}" target="_blank">${aopId}</a>`; // Create clickable link
                                }
                                return ''; // URL does not match the expected format
                            }).join(', '); // Join all urls

                            const processKEs = (keArray) => {
                                if (!keArray || !Array.isArray(keArray)) {
                                    return 'N/A';
                                }

                                return keArray
                                    .filter(ke => typeof ke === 'string' && ke.includes('/'))
                                    .map(ke => {
                                        let keId = ke.split('/').pop();
                                        return `<a href="${ke}" target="_blank">${keId}</a>`;
                                    })
                                    .join(', ') || 'N/A';
                            };


                            contentHtml += `<tr><td>ID: </td><td> ${node.data('label') || 'N/A'}</td></tr>`;
                            contentHtml += `<tr><td>Name: </td><td> ${node.data('name') || 'N/A'}</td></tr>`;
                            const url = node.data('ke_url') ? `<a href="${node.data('ke_url')}" target="_blank">${node.data('ke_url')}</a>` : 'N/A';
                            contentHtml += `<tr><td>KE Url: </td><td> ${url}</td></tr>`;
                            contentHtml += `<tr><td>Downstream KE:</td><td>${processKEs(downstreamKEs) || 'N/A'}</td></tr>`;
                            contentHtml += `<tr><td>Upstream KE:</td><td>${processKEs(upstreamKEs) || 'N/A'}</td></tr>`;
                            contentHtml += `<tr><td>Connected Genes: </td><td> ${connectedGenes.join(', ') || 'N/A'}</td></tr>`;
                            if (keAopLinksHtml) {
                                contentHtml += `<tr><td>KE in AOPs:</td><td>${keAopLinksHtml}</td></tr>`;
                            }
                            let keyEvent = node.data('label').replace("KE", "").trim();
                            const doseKeyEvent = doseKeyeventsWithInfo.find(event => event.ke === keyEvent);
                            if (doseKeyEvent) {
                                const doseKeyEventsToDisplay = (doseKeyEvent.cumulativeProbability * 100).toFixed(0);
                                const imputatedText = doseKeyEvent.isImputated ? " (Imputated Data)" : "";
                                contentHtml += `<tr><td>Key Event Likelihood:</td><td>${doseKeyEventsToDisplay}%${imputatedText}</td></tr>`;
                            } else {
                                contentHtml += `<tr><td>Key Event Likelihood:</td><td>N/A</td></tr>`;
                            }

                        }
                        contentHtml += `</table></div>`;
                        document.getElementById('nodeInfo').innerHTML = contentHtml;
                        document.getElementById('nodePopup').style.display = 'block';

                        allowHidePopup = false;
                        setTimeout(() => {
                            allowHidePopup = true;
                        }, 50);
                    }
                    lastClickTime = currentTime;
                });
                cy.ready(function () {
                    document.getElementById("loader").style.display = "none";
                });
            }
        )
        .catch(
            function (error) {
                console.log('Error:', error);
                document.getElementById("loader").style.display = "none";
                ShowToaster("Error: Unable to fetch this AOP, please check the AOP ID and try again.", "error")

            }
        );
    chemicalSuggestions = [];
}

function addDataToGraph(data) {
    if (!data || data.length === 0) {
        console.error("No data to add to the graph.");
        return;
    }

    data.forEach((entry, index) => {
        const keid = getInsensitiveKeyValue(entry, ['KEID', 'keid']);
        const chemName = getInsensitiveKeyValue(entry, ['chemical', 'chem']);
        const ac50 = getInsensitiveKeyValue(entry, ['AC50', 'ac50']) || 'N/A';
        const gene = getInsensitiveKeyValue(entry, ['GENE', 'gene']);
        console.log("gen", gene);

        console.log(`Row ${index + 1}: KE ID: ${keid}, Assay: ${chemName}, AC50: ${ac50}`);

        if (!keid) {
            console.warn(`Row ${index + 1}: Missing KE ID. Skipping entry:`, entry);
            return;
        }

        const keNode = cy.nodes().filter(node => node.data('label') === keid);

        if (keNode.length === 0) {
            console.error(`Row ${index + 1}: KE Node with label "${keid}" does not exist. Skipping.`);
            return;
        }

        const keNodePosition = keNode.position();
        const angle = Math.random() * 2 * Math.PI;
        const offsetX = 200 * Math.cos(angle);
        const offsetY = 200 * Math.sin(angle);
        const genePosition = {
            x: keNodePosition.x + offsetX,
            y: keNodePosition.y + offsetY
        };

        let assayNode = cy.nodes(`[id = "assay-${gene}"]`);
        if (assayNode.length === 0) {
            try {
                assayNode = cy.add({
                    group: 'nodes',
                    data: {
                        id: `assay-${gene}`,
                        label: `${gene}`,
                        ke_type: 'assay',
                        name: `${gene}`,
                    },
                    position: genePosition,
                    style: {
                        'background-color': '#35d135',
                        'width': 10,
                        'height': 10
                    }
                });
                console.log(`Added Assay Node: assay-${gene}`);
            } catch (error) {
                console.error(`Error adding assay node "assay-${gene}":`, error);
                return;
            }
        }

        // Add an edge from the assay node to the KE node
        const existingEdge = cy.edges(`[source = "assay-${gene}"][target = "${keNode.id()}"]`);
        try {
            if (existingEdge.length === 0) {
                cy.add({
                    group: 'edges',
                    data: {
                        id: `edge-${gene}-${keid}`,
                        source: `assay-${gene}`,
                        target: keNode.id(),
                        label: `AC50: ${ac50}`
                    },
                    style: {
                        'line-color': '#7A7A7A',
                        'width': 2
                    }
                });
                console.log(`Edge added: assay-${gene} -> ${keNode.id()}`);
            } else {
                console.log(`Edge already exists: assay-${gene} -> ${keNode.id()}`);
            }
        } catch (error) {
            console.error(`Error adding edge between assay-${gene} and ${keNode.id()}:`, error);
        }
    });

    ShowToaster("File with Assays uploaded successfully!", "green");
    console.log("All Nodes in Graph:", cy.nodes().map(node => node.data('id')));
}


// Helper function to handle case-insensitive key matching
function getInsensitiveKeyValue(object, keys) {
    const key = keys.find(k => Object.keys(object).some(ok => ok.toLowerCase() === k.toLowerCase()));
    return key ? object[key] : undefined;
}


function getInsensitiveKeyValue(obj, keys) {
    for (const key of keys) {
        const matchedKey = Object.keys(obj).find(k => k.toLowerCase() === key.toLowerCase());
        if (matchedKey) {
            return obj[matchedKey];
        }
    }
    return undefined;
}

function uploadFile() {
    const searchValueAop = document.getElementById("searchFieldAOP").value.trim();
    if (!searchValueAop) {
        ShowToaster("Please search for an AOP before uploading a file", "error");
        return;
    }

    const fileInput = document.getElementById('fileUpload');

    fileInput.value = "";

    fileInput.removeEventListener('change', handleFileUpload);

    fileInput.addEventListener('change', handleFileUpload);

    fileInput.click();
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const fileName = file.name;
        console.log(`Selected file: ${fileName}`);

        if (!fileName.endsWith('.csv')) {
            ShowToaster("Invalid file format. Please upload a CSV file", "error");
            return;
        }

        const maxFileSize = 1048576; // 1MB in bytes
        if (file.size > maxFileSize) {
            ShowToaster("File is too large. Please upload a file smaller than 1MB.", "error");
            return;
        }

        const reader = new FileReader();

        reader.onload = function (event) {
            const fileContent = event.target.result;

            try {
                if (!isUtf8(fileContent)) {
                    throw new Error('Invalid file encoding. Please upload a UTF-8 encoded CSV file.');
                }
            } catch (error) {
                console.error(error.message);
                alert(error.message);
                return;
            }

            const rows = fileContent.split('\n').map(row => row.trim()).filter(row => row);
            const headers = rows.shift().split(',').map(header => header.trim().toLowerCase());
            console.log('Headers in uploaded file:', headers);

            const requiredHeaders = ['keid', 'chemical', 'ac50', 'gene'];
            const missingHeaders = requiredHeaders.filter(header => !headers.includes(header));
            if (missingHeaders.length > 0) {
                ShowToaster(`Invalid file format. Missing headers: ${missingHeaders.join(', ')}`, "error");
                return;
            }

            // Convert rows into JSON objects
            const json = rows.map(row => {
                const values = row.split(',').map(value => value.trim());
                return headers.reduce((obj, header, index) => {
                    obj[header] = values[index] || '';
                    return obj;
                }, {});
            });

            // Sanitize the data
            const sanitizedData = json.map(row => {
                for (const key in row) {
                    if (row[key].startsWith('=') || row[key].startsWith('+') || row[key].startsWith('-') || row[key].startsWith('@')) {
                        row[key] = `'${row[key]}`;
                    }
                }
                return row;
            });

            console.log('Sanitized Data:', sanitizedData);

            const requiredKeys = {
                keid: ['keid'],
                chemical: ['chemical', 'chem'],
                ac50: ['ac50'],
                gene: ['gene'],
            };

            const missingRows = [];
            sanitizedData.forEach((row, index) => {
                const normalizedRowKeys = Object.keys(row).map(key => key.toLowerCase());
                const missingKeys = Object.keys(requiredKeys).filter(
                    key => !requiredKeys[key].some(alias => normalizedRowKeys.includes(alias))
                );

                if (missingKeys.length > 0) {
                    console.warn(`Row ${index + 1} is missing keys: ${missingKeys.join(', ')}`);
                    missingRows.push({row: index + 1, missingKeys});
                }
            });

            if (missingRows.length > 0) {
                console.error("Validation failed for the following rows:", missingRows);
                ShowToaster("Validation failed. Missing keys in rows:\n" + missingRows.map(r => `Row ${r.row}: ${r.missingKeys.join(', ')}`).join('\n'), "red", false);
                return;
            }

            console.log('Validation passed. All required keys are present.');

            userUploadedData = sanitizedData;
            console.log("userUploadedData", userUploadedData);

            const formData = new FormData();
            formData.append('file_name', file.name);
            formData.append('file_size', file.size);
            formData.append('sanitized_data', JSON.stringify(sanitizedData));

            logUserInput(formData);

            addDataToGraph(userUploadedData);

            document.getElementById('fileUpload').value = "";
        };

        reader.readAsText(file); // Read the file as text
    }
}


// Utility function to check UTF-8 encoding
function isUtf8(fileContent) {
    const decoder = new TextDecoder('utf-8', {fatal: true});
    try {
        decoder.decode(new Uint8Array(fileContent.split('').map(c => c.charCodeAt(0))));
        return true;
    } catch (error) {
        return false;
    }
}


document.getElementById('triggerUpload').addEventListener('click', uploadFile);
document.getElementById('infoButton').addEventListener('click', function () {
    const modal = document.getElementById("mergePopupInfo");
    modal.style.display = 'block'

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});

document.getElementById('openDoseResponseDialog').addEventListener('click', async function () {
    const modal = document.getElementById("doseResponseDialog");
    modal.style.display = 'block'

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
    const aop_id = document.getElementById('searchFieldAOP').value;
    const nodes = cy?.nodes();
    if (aop_id && aop_id !== "" && chemicalSuggestions.length === 0 && nodes?.length > 0) {
        chemicalSuggestions = await getChemicalSuggestions(`AOP ${aop_id}`);
    }
    updateChemicalSuggestions();
});

function updateChemicalSuggestions() {
    if (typeof chemicalSuggestions !== 'undefined' && chemicalSuggestions.length > 0) {
        const chemicalHelpElement = document.getElementById('chemicalHelp');
        const suggestionsToShow = chemicalSuggestions.slice(0, 3).join(', ');
        chemicalHelpElement.innerHTML = `<strong>Suggested chemicals:</strong> ${suggestionsToShow}`;
        chemicalHelpElement.title = 'These are the chemicals that we have the most data on for this AOP.';

        console.log('Chemical Suggestions:', chemicalSuggestions);
    }
}

function getColorByType(ke_type) {
    if (!isColorBlindMode) {
        switch (ke_type) {
            case 'Adverse Outcome':
                return '#ED1C24'; // Example: Red color for type1
            case 'Molecular Initiating Event':
                return '#00A79D'; // Example: Blue color for type2
            case 'Key Event':
                return '#F7941D'; // Example: Green color for type3
            case 'genes':
                return '#27AAE1';
            // Add more cases as needed with their corresponding hexadecimal colors
            default:
                return '#000000'; // Default color (black) if type is not matched
        }
    } else {
        switch (ke_type) {
            case 'Adverse Outcome':
                return '#FF00FF';
            case 'Molecular Initiating Event':
                return '#40E0D0';
            case 'Key Event':
                return '#007FFF';
            case 'genes':
                return '#708090';
            default:
                return '#000000';
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // Get the modal
    var modal = document.getElementById("mergePopup");

    // Get the button that opens the modal
    var btn = document.getElementById("mergeButtonKeyEvent");

    //var span = document.getElementsByClassName("close")[0];

    btn.onclick = function () {
        modal.style.display = "block";
        createMergeButtons(globalMergeJson);
    }


    /*span.onclick = function() {
        modal.style.display = "none";
    }*/

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});

function highlightNodesById(idToHighlight) {
    // Mark all nodes as non-highlighted initially
    cy.nodes().forEach(node => {
        node.removeClass('highlighted').addClass('non-highlighted');
    });

    // Then, find and highlight the matching nodes
    cy.nodes().filter(node => {
        return node.data('relatedIds') && node.data('relatedIds').includes(idToHighlight);
    }).forEach(node => {
        node.removeClass('non-highlighted').addClass('highlighted');
    });
}


//Logic for merging nodes
function mergeNodes(keepNodeId, loseNodeId) {
    let keepNode = cy.getElementById(keepNodeId);
    let loseNode = cy.getElementById(loseNodeId);

    // Transfer edges from loseNode to keepNode
    loseNode.connectedEdges().forEach(edge => {
        let sourceId = edge.source().id();
        let targetId = edge.target().id();

        // Determine the new source and target for the edge
        let newSourceId = sourceId === loseNodeId ? keepNodeId : sourceId;
        let newTargetId = targetId === loseNodeId ? keepNodeId : targetId;

        // Check if an equivalent edge already exists
        let existingEdge = cy.edges().some(e => {
            return (e.source().id() === newSourceId && e.target().id() === newTargetId) ||
                (e.source().id() === newTargetId && e.target().id() === newSourceId);
        });

        // Add a new edge if no equivalent edge exists
        if (!existingEdge) {
            cy.add({
                group: 'edges',
                data: {
                    source: newSourceId,
                    target: newTargetId
                }
            });
        }
    });

    // Remove the loseNode and update dropdown
    loseNode.remove();
    removeButtonPairs(keepNodeId, loseNodeId);
    //update globaljsonmerge
    globalMergeJson = globalMergeJson.filter(([source, target]) => source !== loseNodeId && target !== loseNodeId);

    globalGraphJson.nodes = globalGraphJson.nodes.filter(node => node.data.name !== loseNodeId);

    const destinationDropdown = document.getElementById('keepNodeDropDown');
    const sourceDropdown = document.getElementById('loseNodeDropDown');
    populateMergeOptionsDropDown(destinationDropdown, sourceDropdown, globalGraphJson);
    //regenerate the updated buttons
    createMergeButtons(globalMergeJson);
}

function createMergeButtons(mergeOptions) {
    const container = document.getElementById('dynamicButtons');
    container.innerHTML = ''; // Clear existing content if any

    mergeOptions.forEach((pair, index) => {
        // Create a div to group buttons for each option pair
        const pairDiv = document.createElement('div');
        pairDiv.className = 'merge-option-group';
        pairDiv.id = `merge-pair-${index}`;

        // Iterate over each option in the pair to create buttons
        pair.forEach((option, optionIndex) => {
            const button = document.createElement('button');
            button.textContent = option; // Set the button text
            button.className = 'merge-option-button';
            button.id = `merge-option-${index}-${optionIndex}`;

            button.setAttribute('data-node-id', option);

            // Attach the event listener to each button
            button.addEventListener('click', function () {
                // Remove 'active' class from sibling button in the same pair
                const siblingButton = pairDiv.querySelector('.merge-option-button.active');
                if (siblingButton) {
                    siblingButton.classList.remove('active');
                }
                // Toggle 'active' class on clicked button
                this.classList.toggle('active');
                console.log(`Merge option selected: ${option}`);
            });

            pairDiv.appendChild(button); // Add the button to the pair's div
        });

        container.appendChild(pairDiv); // Add the pair's div to the dynamicButtons container
    });
    updateMergeButtonLabel(mergeOptions.length);
}

function populateMergeOptionsDropDown(dropDownKeep, dropDownLose, graphJson) {

    dropDownKeep.innerHTML = '';
    dropDownLose.innerHTML = '';

    const nodes = graphJson.nodes;

    nodes.forEach(nodeItem => {
        const nodeName = nodeItem.data.name;
        const option = document.createElement('option');
        option.value = nodeName;
        option.textContent = nodeName;

        const nodeNameTwo = nodeItem.data.name;
        const optionTwo = document.createElement('option');
        optionTwo.value = nodeNameTwo;
        optionTwo.textContent = nodeNameTwo;

        dropDownKeep.appendChild(option); // Appending the new option to the dropdown
        dropDownLose.appendChild(optionTwo);
    });

    $(dropDownKeep).select2({placeholder: "Select a node to keep"});
    $(dropDownLose).select2({placeholder: "Select a node to merge"});

    $(dropDownKeep).val(null).trigger('change');
    $(dropDownLose).val(null).trigger('change');
}

function populateHighlightAopDropDown(dropDownAop, graphJson) {

    const aopAfterFilter = graphJson;
    console.log(aopAfterFilter);
    dropDownAop.innerHTML = '';

    aopAfterFilter.forEach(aopItem => {
        const option = document.createElement('option');
        option.value = aopItem;
        option.textContent = `AOP ${aopItem}`;

        dropDownAop.appendChild(option);
    });

    $(dropDownAop).select2({placeholder: "Select an AOP to highlight"});

    $(dropDownAop).val(null).trigger('change');
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('processButton').addEventListener('click', function () {
        //Manuel merge process
        var keepNodeDropDown = document.getElementById("keepNodeDropDown").value;
        var loseNodeDropDown = document.getElementById("loseNodeDropDown").value;

        //if they are equal or if one of the options are empty, skip manuel merge
        if (keepNodeDropDown === '' || loseNodeDropDown === '' || keepNodeDropDown === loseNodeDropDown) {
            console.log('Either one of the options is empty or both options are equal. Skipping manual merge.');
        } else {
            // manuel merge
            mergeNodes(keepNodeDropDown, loseNodeDropDown)
            loggingMergeActions(keepNodeDropDown, loseNodeDropDown)
        }

        //Button merge process
        const mergePairs = document.querySelectorAll('.merge-option-group');

        mergePairs.forEach(pair => {
            const buttons = pair.querySelectorAll('.merge-option-button');
            let keepNodeId, loseNodeId;

            buttons.forEach(button => {
                if (button.classList.contains('active')) {
                    // This button is the keepNode
                    keepNodeId = button.getAttribute('data-node-id');
                    console.log('keepNode: ', keepNodeId);
                } else {
                    // The other button is the loseNode
                    loseNodeId = button.getAttribute('data-node-id');
                    console.log('loseNode: ', loseNodeId);
                }
            });

            //button merge
            if (keepNodeId && loseNodeId) {
                console.log(`Merging: Keep ${keepNodeId}, Lose ${loseNodeId}`);
                mergeNodes(keepNodeId, loseNodeId); // Perform the merge logic
                updateMergeButtonLabel(mergePairs.length)
                //log merging
                loggingMergeActions(keepNodeId, loseNodeId);
            }
        });
        const mergePairsCount = document.querySelectorAll('.merge-option-group').length;
        updateMergeButtonLabel(mergePairsCount);
    });
});

function removeButtonPairs(keepNodeId, loseNodeId) {
    // Remove the pair directly involved in the merge
    document.querySelectorAll(`button[data-node-id="${keepNodeId}"], button[data-node-id="${loseNodeId}"]`)
        .forEach(button => button.parentNode.remove());

    document.querySelectorAll(`button[data-node-id="${keepNodeId}"], button[data-node-id="${loseNodeId}"]`)
        .forEach(button => {
            if (button.parentNode && button.parentNode.classList.contains('merge-option-group')) {
                button.parentNode.remove();
            }
        });
}

function removeButtonPairsManuelMerge(loseNodeId) {
    document.querySelectorAll(`button[data-node-id="${loseNodeId}"]`).forEach(button => {
        if (button.parentNode && button.parentNode.classList.contains('merge-option-group')) {
            button.parentNode.remove();
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('exportToCytoscape').addEventListener('click', function () {
        const now = new Date();
        const formattedDate = `${String(now.getDate()).padStart(2, '0')}${String(now.getMonth() + 1).padStart(2, '0')}${now.getFullYear()}`;

        const graphmlContent = generateGraphML(cy);
        const blob = new Blob([graphmlContent], {type: 'application/graphml+xml'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const filename = 'AOP_' + formattedDate + '.graphml';
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        logCytoscape();
    });
});

function generateGraphML(cy) {
    let graphml = '<?xml version="1.0" encoding="UTF-8"?>\n<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n';
    graphml += '<key id="keType" for="node" attr.name="ke_type" attr.type="string"/>\n';
    graphml += '<key id="label" for="node" attr.name="label" attr.type="string"/>\n';
    graphml += '<key id="value" for="node" attr.name="value" attr.type="string"/>\n';
    graphml += '<key id="name" for="node" attr.name="name" attr.type="string"/>\n';
    graphml += '<key id="keInAop" for="node" attr.name="ke_in_aop" attr.type="string"/>\n';
    graphml += '<graph id="G" edgedefault="undirected">\n';

    // Filter and add nodes with attributes, exclude hidden genes if checkbox is unchecked
    cy.nodes().forEach((node) => {
        if (node.hasClass('hidden') && !document.getElementById('checkedBoxGene').checked) {
            // If node is hidden and checkbox for showing genes is not checked, skip this node
            return;
        }

        const data = node.data();
        graphml += `<node id="${data.id}">\n`;
        graphml += `<data key="keType">${data.ke_type}</data>\n`;
        graphml += `<data key="label">${data.label}</data>\n`;
        graphml += `<data key="value">${data.value}</data>\n`;
        graphml += `<data key="name">${data.name}</data>\n`;

        const keInAopString = JSON.stringify(data.ke_in_aop || []);
        graphml += `<data key="keInAop">${keInAopString}</data>\n`;
        graphml += '</node>\n';
    });

    // Filter and add edges, exclude those connected to hidden genes if checkbox is unchecked
    cy.edges().forEach((edge) => {
        if (edge.source().hasClass('hidden') || edge.target().hasClass('hidden')) {
            if (!document.getElementById('checkedBoxGene').checked) {
                // If either source or target node is hidden and checkbox for showing genes is not checked, skip this edge
                return;
            }
        }

        const data = edge.data();
        graphml += `<edge source="${data.source}" target="${data.target}"></edge>\n`;
    });
    graphml += '</graph>\n</graphml>';
    return graphml;
}

$(document).ready(function () {
    fetch('/get_stressors')
        .then(response => response.json())
        .then(data => {
            const formattedData = data.map(stressor => ({
                id: stressor,
                text: stressor
            }));

            $('#stressorDropdown').select2({
                placeholder: "Search for a stressor",
                allowClear: true,
                data: formattedData
            });
        })
        .catch(error => console.error('Fetch error:', error));

    $('#stressorDropdown').val(null).trigger('change');
});

$(document).ready(function () {
    fetch('/get_cells')
        .then(response => response.json())
        .then(data => {
            const formattedCellData = Object.keys(data).map(cell => ({
                id: cell,
                text: cell,
                synonyms: data[cell]
            }));

            $('#cellsDropdown').select2({
                placeholder: "Search for a Cell",
                allowClear: true,
                data: formattedCellData,
                multiple: true,
                templateResult: function (item) {
                    if (!item.id) {
                        return item.text;
                    }
                    const filteredSynonyms = item.synonyms
                        ? Array.from(new Set(item.synonyms)).filter(syn => syn !== item.text)
                        : [];
                    const synonymsText = filteredSynonyms.length > 0
                        ? ` (${filteredSynonyms.join(', ')})`
                        : '';
                    const displayText = $('<span>').text(item.text + synonymsText);
                    return displayText;
                }
            });

            $('#cellsDropdown').on('select2:select', function (e) {
                const selectedData = e.params.data;
            });
        })
        .catch(error => {
            console.error('Fetch error:', error)

        });

    $('#cellsDropdown').val(null).trigger('change');
});


$(document).ready(function () {
    fetch('/get_organs')
        .then(response => response.json())
        .then(data => {
            const formattedOrgsData = Object.keys(data).map(organ => ({
                id: organ,
                text: organ,
                synonyms: data[organ]
            }));

            $('#organsDropdown').select2({
                placeholder: "Search for an Organ",
                allowClear: true,
                data: formattedOrgsData,
                multiple: true,
                templateResult: function (item) {
                    if (!item.id) {
                        return item.text;
                    }
                    const synonyms = item.synonyms && item.synonyms.length > 0
                        ? ` (${item.synonyms.join(', ')})`
                        : '';
                    const displayText = $('<span>').text(item.text + synonyms);
                    return displayText;
                }
            });

            $('#organsDropdown').on('select2:select', function (e) {
                const selectedData = e.params.data;
            });
        })
        .catch(error => console.error('Fetch error:', error));

    $('#organsDropdown').val(null).trigger('change');
});


$(document).ready(function () {
    fetch('/get_taxonomies')
        .then(response => response.json())
        .then(data => {
            const formattedTaxData = Object.keys(data).map(tax => ({
                id: tax,
                text: tax,
                synonyms: data[tax]
            }));

            $('#taxonomiDropdown').select2({
                placeholder: "Search for a Taxonomy",
                allowClear: true,
                data: formattedTaxData,
                multiple: true,
                templateResult: function (item) {
                    if (!item.id) {
                        return item.text;
                    }
                    const filteredSynonyms = item.synonyms
                        ? Array.from(new Set(item.synonyms)).filter(syn => syn !== item.text)
                        : [];
                    const synonymsText = filteredSynonyms.length > 0
                        ? ` (${filteredSynonyms.join(', ')})`
                        : '';
                    const displayText = $('<span>').text(item.text + synonymsText);
                    return displayText;
                }
            });
        })
        .catch(error => console.error('Fetch error:', error));

    $('#taxonomiDropdown').val(null).trigger('change');
});


$(document).ready(function () {
    fetch('/get_sexes')
        .then(response => response.json())
        .then(data => {
            const formattedSexData = data.map(sex => ({
                id: sex,
                text: sex
            }));
            $('#sexDropdown').select2({
                placeholder: "Search for a Sex",
                allowClear: true,
                data: formattedSexData,
                multiple: true
            });
        })
        .catch(error => console.error('Fetch error:', error));
    $('#sexDropdown').val(null).trigger('change');
});


$(document).ready(function () {
    fetch('/get_life_stages')
        .then(response => response.json())
        .then(data => {
            const formattedLifeData = Object.keys(data).map(lifeStage => ({
                id: lifeStage,
                text: lifeStage,
                synonyms: data[lifeStage]
            }));

            $('#lifeStageDropdown').select2({
                placeholder: "Search for a Life Stage",
                allowClear: true,
                data: formattedLifeData,
                multiple: true,
                templateResult: function (item) {
                    if (!item.id) {
                        return item.text;
                    }
                    const filteredSynonyms = item.synonyms
                        ? Array.from(new Set(item.synonyms)).filter(syn => syn !== item.text)
                        : [];
                    const synonymsText = filteredSynonyms.length > 0
                        ? ` (${filteredSynonyms.join(', ')})`
                        : '';
                    const displayText = $('<span>').text(item.text + synonymsText);
                    return displayText;
                }
            });
        })
        .catch(error => console.error('Fetch error:', error));

    $('#lifeStageDropdown').val(null).trigger('change');
});


document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('saveButtonLog').addEventListener('click', function () {
        if (globalUserActionsLog.length === 0) {
            console.log("Log file is empty")
        } else {
            saveLogToFile();
        }
    });
});

function logUserAction(actionDescription) {
    const timestamp = new Date().toISOString();
    globalUserActionsLog.push(`${timestamp}: ${actionDescription}`);
}

function logHeaderName(logDescriptions) {
    globalUserActionsLog.push(`${logDescriptions}`)
}

function logCytoscape() {
    logHeaderName("Export to Cytoscape");
    logUserAction("Graph has been saved in the '.graphml' format.");
}

function logUserInput(formData) {
    logHeaderName("USER INPUTS\n")

    if (formData.get("searchFieldAOP")) {
        logHeaderName("USER INPUT AOP IDS:\n")
        logUserAction(formData.get("searchFieldAOP"));
    }

    if (formData.get("searchFieldKE")) {
        logHeaderName("USER INPUT KE IDS:\n")
        logUserAction(formData.get("searchFieldKE"));
    }

    if (formData.get("stressorDropdown")) {
        logHeaderName("USER INPUT STRESSOR NAME:\n")
        logUserAction(formData.get("stressorDropdown"));
    }

    /*logHeaderName("\n")

    if (formData.get("checkedBoxGene") === '1'){
        logUserAction("Genes enabled");
    }else{
        logUserAction("Genes disabled");
    }*/

    if (formData.get("checkboxDevelopment") === '1') {
        logUserAction("Filtering: OECD Under Development");
    }

    if (formData.get("checkboxEndorsed") === '1') {
        logUserAction("Filtering: OECD WPHA Endorsed");
    }

    if (formData.get("checkboxReview") === '1') {
        logUserAction("Filtering: OECD Under Review");
    }

    if (formData.get("checkboxApproved") === '1') {
        logUserAction("Filtering: OECD EAGMST Approved");
    }
    if (formData.get('file_name')) {
        logHeaderName("USER UPLOADED FILE:\n");
        logUserAction(`Uploaded file: ${formData.get('file_name')}`);
        logUserAction(`File size: ${formData.get('file_size')} bytes`);
    }
    if (formData.get('sanitized_data')) {
        logHeaderName("SANITIZED DATA:\n");
        logUserAction(`Sanitized data: ${formData.get('sanitized_data')}`);
    }
    if (formData.get('dose')) {
        logHeaderName("USER RUN DOSE RESPONSE DATA:\n");
        logUserAction(`Dose: ${formData.get('dose')}`);
    }
    if (formData.get('chemical')) {
        logUserAction(`Chemical: ${formData.get('chemical')}`);
    }
    if (formData.get('KePath')) {
        logUserAction(`KePath: ${formData.get('KePath')}`);
    }
    if (formData.get('result')) {
        logUserAction(`RESULTS: ${formData.get('result')}`);
    }

}

function loggingMergeActions(keepNode, removeNode) {
    logHeaderName("\n")
    logUserAction(`Merging the KE node: ${removeNode} into the KE: ${keepNode}`)
}

function loggingAopVisualized(aop_before_filter, aop_after_filter) {
    logHeaderName("\nAOPs before filtering\n")
    logUserAction(aop_before_filter)
    logHeaderName("\nAOPs after filtering (AOP VISUALIZED)\n")
    logUserAction(aop_after_filter)
}

function saveLogToFile() {
    globalUserActionsLog.push('\nThank you for using the AOP-networkFinder tool. Please remember to cite this article:\n(link to article)')
    const logContent = globalUserActionsLog.join('\n');
    const blob = new Blob([logContent], {type: "text/plain;charset=utf-8"});
    const url = URL.createObjectURL(blob);

    const downloadLink = document.createElement("a");
    downloadLink.href = url;
    downloadLink.download = "UserActionsLog.txt";
    document.body.appendChild(downloadLink);
    downloadLink.click();
    document.body.removeChild(downloadLink);

    //Clear the log array after downloading the file.
    globalUserActionsLog = [];
}

// Function to toggle labels
function toggleGeneLabels(showLabels) {
    if (showLabels) {
        // Show labels for genes
        cy.style().selector('node[ke_type="genes"]').style('label', 'data(id)').update();
    } else {
        // Hide labels for genes
        cy.style().selector('node[ke_type="genes"]').style('label', '').update();
    }
}

// Handle checkbox change event
document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('toggleLabels').addEventListener('change', function (e) {
        toggleGeneLabels(this.checked);
    });
});

function highlightGraphForAop(aopId) {
    // Initially classify all nodes and edges as non-highlighted
    cy.elements().addClass('non-highlighted').removeClass('highlighted');

    if (aopId && aopId !== "none") {
        const highlightedNodes = cy.nodes().filter(node => node.data('ke_in_aop') && node.data('ke_in_aop').includes(aopId));
        highlightedNodes.removeClass('non-highlighted').addClass('highlighted');

        cy.edges().forEach(edge => {
            const sourceHighlighted = edge.source().hasClass('highlighted');
            const targetHighlighted = edge.target().hasClass('highlighted');

            if (sourceHighlighted && targetHighlighted) {
                edge.style('opacity', '1');
            } else {
                edge.style('opacity', '0.1');
            }
        });
    } else {
        // If no aopId is provided or "none" is selected, remove all highlighting
        cy.elements().removeClass('highlighted non-highlighted');
        cy.elements().style('opacity', '1');
    }
}

$(document).ready(function () {
    $('#aopDropDown').select2({
        placeholder: "Select an AOP to highlight",
        allowClear: true
    });

    $('#aopDropDown').on('select2:select', function (e) {
        var selectedAop = $(this).val();
        highlightGraphForAop(selectedAop);
    });
    // Custom clear button functionality
    $('#clearSelection').on('click', function () {
        $('#aopDropDown').val(null).trigger('change');
        highlightGraphForAop(null);
    });
});

function setupEdgeAddition(cy) {
    let firstNodeId = null; // to keep track of the first node clicked
    let shiftKeyDown = false; // to track whether the Shift key is held down

    document.addEventListener('keydown', function (event) {
        if (event.key === 'Shift') {
            shiftKeyDown = true;
        }
    });

    document.addEventListener('keyup', function (event) {
        if (event.key === 'Shift') {
            shiftKeyDown = false;
        }
    });

    cy.on('tap', 'node', function (evt) {
        if (shiftKeyDown) {
            let nodeId = evt.target.id();
            if (firstNodeId === null) {
                firstNodeId = nodeId;
            } else {
                cy.add([
                    {group: "edges", data: {source: firstNodeId, target: nodeId}}
                ]);
                firstNodeId = null; // Reset for next edge addition
            }
        }
    });
}

document.addEventListener('click', function (e) {
    var popup = document.getElementById('nodePopup');
    if (popup && popup.style.display === 'block' && !popup.contains(e.target) && allowHidePopup) {
        popup.style.display = 'none';
    }
});

document.getElementById('nodePopup').addEventListener('click', function (e) {
    e.stopPropagation(); // Prevent click inside popup from propagating
});

function applyColorScheme(colors) {
    cy.nodes().forEach(node => {
        const keType = node.data('ke_type');
        const newColor = colors[keType] || node.style('background-color'); // Use current color as fallback
        node.style('background-color', newColor);
    });
}

function colorBlindModeToggle() {
    if (cy) {
        //graph initialized, call applyColorchema method
        isColorBlindMode = !isColorBlindMode; // Toggle the state

        if (isColorBlindMode) {
            applyColorScheme(colorBlindColors); // color blind mode
            this.style.backgroundColor = "#AADDAA";
            this.style.color = "#000000";
        } else {
            applyColorScheme(defaultColors); // Revert to default colors
            this.style.backgroundColor = "";
            this.style.color = "";
        }
    } else {
        //graph not initialized, change only state and button color.
        isColorBlindMode = !isColorBlindMode //toggle the state
        if (isColorBlindMode) {
            this.style.backgroundColor = "#AADDAA";
            this.style.color = "#000000";
        } else {
            this.style.backgroundColor = "";
            this.style.color = "";
        }
    }
}

document.getElementById('saveIcon').addEventListener('click', function () {

    const fileName = prompt("Enter the filename with extension (.png or .jpg):", "aop.png");
    var scale = 2;

    if (fileName) {
        let dataUrl;

        if (fileName.endsWith('.png')) {
            dataUrl = cy.png({
                bg: "white",
                full: true,
                scale: scale
            });
        } else if (fileName.endsWith('.jpg')) {
            dataUrl = cy.jpg({
                bg: "white",
                quality: 1
            });
        } else {
            ShowToaster("Invalid file extension. Please use .png or .jpg only.", "error");
            return;
        }

        const link = document.createElement('a');
        link.href = dataUrl;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        console.log("Save operation cancelled or invalid filename.");
    }
});

document.getElementById('colorBlindNotActive').addEventListener('click', function () {
    this.style.display = 'none';
    document.getElementById('colorBlindActive').style.display = 'block';
    // Enable color blind mode
    colorBlindModeToggle()
});

document.getElementById('colorBlindActive').addEventListener('click', function () {
    this.style.display = 'none';
    document.getElementById('colorBlindNotActive').style.display = 'block';
    // Disable color blind mode
    colorBlindModeToggle()
});

document.getElementById('saveStyleIcon').addEventListener('click', function () {
    const choice = prompt("Type '1' to download the Cytoscape Desktop Standard Style Template or '2' to download the Cytoscape Desktop Color-Blind Style Template:");

    if (choice === null) {
        return;
    }

    let fileName;
    switch (choice) {
        case '1':
            fileName = 'Cytoscape_AOPnetworkFinder_Style.xml';
            break;
        case '2':
            fileName = 'Cytoscape_AOPnetworkFinder_Style_Color_Blind.xml';
            break;
        default:
            ShowToaster("Invalid choice. Please enter '1' or '2'.", "error");
            return;
    }

    window.location.href = `/download/${fileName}`;
});

document.getElementById('emailIcon').addEventListener('click', function () {
    var searchValueAop = document.getElementById("searchFieldAOP").value;
    let aopArray = searchValueAop.split(',').map(id => id.trim());

    let validAopArray = aopArray.filter(aopId => !isNaN(aopId) && aopId !== '');

    if (validAopArray.length > 0) {
        let urls = validAopArray.map(aopId => `https://aopwiki.org/contact_form?aop=${aopId}`);

        urls.forEach(url => {
            window.open(url, '_blank');
        });
    } else {
        ShowToaster("Please enter valid AOP IDs", "error");

    }

});

function updateMergeButtonLabel(mergeCount) {
    const mergeButton = document.getElementById('mergeButtonKeyEvent');
    mergeButton.textContent = `Merge KE: (${mergeCount})`;
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById('mergeButtonKeyEvent').textContent = 'Merge KE: (0)';
});

document.getElementById('checkedBoxGene').addEventListener('change', function () {
    toggleGenesNode(this.checked)
});

function toggleGenesNode(checked) {
    if (checked) {
        cy.elements().removeClass('hidden');
    } else {

        cy.edges().filter(function (edge) {
            return edge.source().data('ke_type') === 'genes' || edge.target().data('ke_type') === 'genes';
        }).addClass('hidden');

        cy.nodes().filter(function (node) {
            return node.data('ke_type') === 'genes';
        }).addClass('hidden');
    }

    cy.style()
        .selector('.hidden')
        .style({
            'display': 'none'
        })
        .update();
}

//checkUploadedFileForAssay
function checkUploadedFileForAssay(ke) {
    if (!userUploadedData) {
        return null;
    }

    const keData = userUploadedData.find(row => row.keid === ke);
    console.log("KE Data from uploaded file:", keData);
    if (!keData) {
        return null;
    }

    return {
        gene: keData.gene,
        ke: keData.keid,
        ac50: keData.ac50,
        chemical: keData.chemical,
    }
}


function getGradientColor(likelihood) {
    if (likelihood == null) {
        return 'grey';
    }

    // Clamp likelihood between 0 and 1
    likelihood = Math.max(0, Math.min(1, likelihood));

    // Define the 10-color palette from worst (1) to best (0)
    const colorScale = [
        '#9e0142', // 1. Worst
        '#d53e4f',
        '#f46d43',
        '#fdae61',
        '#fee08b',
        '#e6f598',
        '#abdda4',
        '#66c2a5',
        '#3288bd',
        '#5e4fa2'  // 10. Best
    ];

    // Calculate the index for the color scale
    // Since likelihood=1 should map to index 0 (worst) and likelihood=0 to index 9 (best),
    // we invert the mapping by subtracting the scaled index from (colorScale.length - 1)
    const scaledLikelihood = likelihood * colorScale.length;
    let index = Math.floor(scaledLikelihood);

    // Handle edge case where likelihood=1 maps exactly to the last color
    if (index >= colorScale.length) {
        index = colorScale.length - 1;
    }

    // Since the colorScale is ordered from worst to best,
    // we map likelihood=1 to index=0 and likelihood=0 to index=9
    const reversedIndex = colorScale.length - 1 - index;

    return colorScale[reversedIndex];
}

document.addEventListener('DOMContentLoaded', function () {
    const checkboxDose = document.getElementById("checkbox-dose");
    const checkboxes = checkboxDose.querySelectorAll("input[type='checkbox']");

    checkboxes.forEach((checkbox) => {
        checkbox.addEventListener('change', function () {
            if (this.checked) {
                checkboxes.forEach((otherCheckbox) => {
                    if (otherCheckbox !== this) {
                        otherCheckbox.checked = false;
                    }
                });
            } else {
                const isAnyChecked = Array.from(checkboxes).some(cb => cb.checked);
                if (!isAnyChecked) {
                    this.checked = true;
                }
            }
        });
    });
});

// Reusable function that processes an array of Key Event labels
async function gatherAndProcessDoseResponse(kePaths) {
    removeGradientBarFromGraph()
    const dose = document.getElementById("dose").value;
    const chemical = document.getElementById("chemical").value;
    const aopId = document.getElementById("searchFieldAOP").value.toString();
    //const keyEvetnPath = document.getElementById("kePath").value.split(",").map(path => path.trim());
    const checkboxDose = document.getElementById("checkbox-dose");
    const checkboxes = checkboxDose.querySelectorAll("input[type='checkbox']");
    let handleNoneDataNodesModeCheckbox = null

    if (dose === "" || chemical === "") {
        ShowToaster("Please fill inn all fields before running the dose response", "error")
        return
    }

    checkboxes.forEach(checkbox => {
        if (checkbox.checked) {
            handleNoneDataNodesModeCheckbox = checkbox.id;
        }
    });


    const formData = new FormData();

    formData.append('dose', dose);
    formData.append('chemical', chemical);
    //formData.append('KePath', keyEvetnPath);


    const graph = cy.nodes();
    let keToAssaysMap = {};

    // Build up the KE->Assay map
    kePaths.forEach(path => {
        graph.forEach(node => {
            if (node.data('label') === path) {
                const connectedKEs = node.connectedEdges();
                let foundAssay = false;

                for (let edge of connectedKEs) {
                    const sourceIsAssayGene =
                        (edge.source().data('ke_type') === 'genes') &&
                        assayGenesDict &&
                        assayGenesDict[edge.source().data('name')];

                    if (sourceIsAssayGene) {
                        sourceIsAssayGene.forEach(assay => {
                            const keNumber = node.data('label').replace("KE ", "");
                            if (!keToAssaysMap[keNumber]) {
                                keToAssaysMap[keNumber] = [];
                            }
                            keToAssaysMap[keNumber].push(assay.assayComponentName);
                        });

                        foundAssay = true;
                    }
                }

                if (!foundAssay) {

                    const excelAssayData = checkUploadedFileForAssay(node.data('label'));

                    if (excelAssayData) {
                        const keNumber = node.data('label').replace("KE ", "");
                        if (!keToAssaysMap[keNumber]) {
                            keToAssaysMap[keNumber] = [];
                        }
                        keToAssaysMap[keNumber].push({
                            gene: excelAssayData.gene,
                            ac50: excelAssayData.ac50,
                            chemical: excelAssayData.chemical
                        });
                    } else {
                        keToAssaysMap[node.data('label').replace("KE ", "")] = null;
                    }
                }
            }
        });
    });
    addGradientBarToGraph()

    //get value of checkbox-enrichment
    const checkboxEnrichment = document.getElementById("checkbox-enrichment");
    const checkboxEnrichmentValue = checkboxEnrichment.querySelector("input[type='checkbox']").checked;

    if (checkboxEnrichmentValue) {
        let nullKeList = []
        for (const key in keToAssaysMap) {
            if (keToAssaysMap[key] === null) {
                nullKeList.push(key)
            }
        }

        const geneEnrichment = await fetchGeneEnrichment(nullKeList);

        for (const key in keToAssaysMap) {
            // If keToAssaysMap for the key is null and geneEnrichment has data,
            // update it with the array of assays from geneEnrichment.
            if (keToAssaysMap[key] === null && geneEnrichment[key]) {
                keToAssaysMap[key] = geneEnrichment[key].assays;
            }
        }
    }


    const jsonIfy = JSON.stringify(keToAssaysMap);

    // Make your API call with the compiled data
    const doseOfSubstance = parseFloat(dose);
    const csrfToken = document.getElementById('csrf_token').value;

    const payload = {
        doseOfSubstance: doseOfSubstance,
        chemical: chemical,
        ke_assay_list: jsonIfy,
        handleNoneDataNodesMode: handleNoneDataNodesModeCheckbox,
        aop_id: aopId
    };

    const response = await fetch('/api/dose_response', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken  // Include CSRF token header
        },
        body: JSON.stringify(payload),
        credentials: 'same-origin'
    });

    const bioactivityAssays = await response.json();


    // Reset all Key Event node styles
    cy.nodes('[ke_type = "Key Event"]').forEach(node => {
        node.style({
            'border-width': 0,
            'border-color': '#000'
        });
    });

    formData.append('result', JSON.stringify(bioactivityAssays.AOP));

    // Log user inputs
    logUserInput(formData);

    if (bioactivityAssays.AOP) {
        doseKeyeventsWithInfo = [];
        for (const [_, eventObj] of Object.entries(bioactivityAssays.AOP)) {
            let cumulativeProbability = eventObj["cumulative probability"];
            let keNumber = eventObj.KE_id
            doseKeyeventsWithInfo.push({
                ke: keNumber,
                cumulativeProbability: cumulativeProbability,
                isImputated: false
            });
        }
    }
    if (bioactivityAssays.ke_with_no_ac50Data) {
        for (const [keNumber, desc] of Object.entries(bioactivityAssays.ke_with_no_ac50Data)) {
            const keIndex = doseKeyeventsWithInfo.findIndex(ke => ke.ke === keNumber);
            if (keIndex !== -1) {
                doseKeyeventsWithInfo[keIndex].isImputated = true;
            }
        }
    }

    let aoIsActivated = bioactivityAssays.AOP.AO0;
    let cumulativeProbability = aoIsActivated["cumulative probability"];

    // Update node border colors based on ke_likelihoods
    if (bioactivityAssays.AOP) {
        for (const eventObj of Object.values(bioactivityAssays.AOP)) {
            // Retrieve the KE_id from the event object
            const keId = eventObj.KE_id;
            if (!keId) continue; // Skip if no KE_id is provided

            // Find the corresponding node by matching the node's data 'KE_id'
            const node = cy.nodes().filter(ele => ele.data('label') === `KE ${keId}`);
            if (node && node.length > 0) {
                // Get the individual event probability
                const probability = eventObj["cumulative probability"];

                // Calculate the color using your gradient function
                const borderColor = getGradientColor(probability);

                // Set the node's style with the determined border color and other styling properties
                node.style({
                    'border-width': 6,
                    'border-color': borderColor,
                    'border-opacity': 1,
                    'border-padding': 20,
                    'border-margin': 20
                });
            }
        }

        if (cumulativeProbability > 0.8) {
            const adverseNodes = cy.nodes('[ke_type = "Adverse Outcome"]');

            adverseNodes.style({'background-color': 'magenta'});

            const createBigCrazyExplosion = (node) => {
                const centerPos = node.position();

                const shakes = 3;
                let shakeSequence = [];
                for (let i = 0; i < shakes; i++) {
                    const offsetX = (Math.random() - 0.5) * 10;
                    const offsetY = (Math.random() - 0.5) * 10;
                    shakeSequence.push({
                        position: {
                            x: centerPos.x + offsetX,
                            y: centerPos.y + offsetY
                        },
                        duration: 100,
                        easing: 'ease-in-out'
                    });
                }
                shakeSequence.push({
                    position: {x: centerPos.x, y: centerPos.y},
                    duration: 100,
                    easing: 'ease-in-out'
                });

                node.animate(
                    {
                        queue: true,
                        complete: () => {
                            const shockwave = cy.add({
                                group: 'nodes',
                                data: {id: 'shockwave-' + node.id() + '-' + Math.random()},
                                style: {
                                    'background-color': 'rgba(255, 165, 0, 0.2)',
                                    'border-color': 'red',
                                    'border-width': 2,
                                    'border-opacity': 0.8,
                                    width: 1,
                                    height: 1
                                },
                                position: centerPos
                            });

                            shockwave.animate(
                                {
                                    style: {
                                        width: 200,
                                        height: 200,
                                        'border-opacity': 0,
                                        'background-opacity': 0
                                    }
                                },
                                {
                                    duration: 1000,
                                    easing: 'ease-out',
                                    complete: () => shockwave.remove()
                                }
                            );

                            node.animate(
                                {style: {'background-color': 'yellow'}},
                                {
                                    duration: 300,
                                    easing: 'ease-in-out',
                                    complete: () => {
                                        node.animate(
                                            {style: {'background-color': 'red'}},
                                            {
                                                duration: 300,
                                                easing: 'ease-in-out',
                                                complete: () => {
                                                    node.animate(
                                                        {style: {'background-color': 'orange'}},
                                                        {
                                                            duration: 300,
                                                            easing: 'ease-in-out',
                                                            complete: () => {
                                                                node.style('background-color', 'magenta');
                                                                triggerElectricWave(node);
                                                            }
                                                        }
                                                    );
                                                }
                                            }
                                        );
                                    }
                                }
                            );

                            const shrapnelCount = 16;
                            for (let i = 0; i < shrapnelCount; i++) {
                                const shrapnelNode = cy.add({
                                    group: 'nodes',
                                    data: {
                                        id: 'boom-' + node.id() + '-' + i + '-' + Math.random()
                                    },
                                    style: {
                                        'background-color': 'orange',
                                        width: 10,
                                        height: 10,
                                        label: '💥'
                                    },
                                    position: {
                                        x: centerPos.x,
                                        y: centerPos.y
                                    }
                                });

                                // Random direction & distance
                                const angle = Math.random() * 2 * Math.PI;
                                const distance = 80 + Math.random() * 80; // fling them further

                                const targetX = centerPos.x + distance * Math.cos(angle);
                                const targetY = centerPos.y + distance * Math.sin(angle);

                                shrapnelNode.animate(
                                    {position: {x: targetX, y: targetY}},
                                    {
                                        duration: 800, // slower fling for drama
                                        easing: 'ease-out',
                                        complete: () => {
                                            // Fade out & shrink them
                                            shrapnelNode.animate(
                                                {
                                                    style: {
                                                        opacity: 0,
                                                        width: 1,
                                                        height: 1
                                                    }
                                                },
                                                {
                                                    duration: 800,
                                                    complete: () => shrapnelNode.remove()
                                                }
                                            );
                                        }
                                    }
                                );
                            }
                        }
                    },
                    shakeSequence
                );
            };

            const triggerElectricWave = (startNode) => {
                const electricColor = '#00ffc3';
                const defaultEdgeColor = '#999';
                const defaultEdgeWidth = 2;

                cy.elements().bfs({
                    roots: startNode,
                    directed: false,
                    visit: (v, e, u, i, depth) => {
                        if (e) {
                            setTimeout(() => {
                                // "Light up" the edge
                                e.animate(
                                    {
                                        style: {'line-color': electricColor, width: 4}
                                    },
                                    {
                                        duration: 300,
                                        complete: () => {
                                            // Then revert it
                                            e.animate(
                                                {
                                                    style: {'line-color': defaultEdgeColor, width: defaultEdgeWidth}
                                                },
                                                {
                                                    duration: 300
                                                }
                                            );
                                        }
                                    }
                                );
                            }, depth * 400);
                        }
                    }
                });
            };

            adverseNodes.forEach((node) => createBigCrazyExplosion(node));
        }

    }

    const allImputatedFalse = doseKeyeventsWithInfo.every(ke => !ke.isImputated);

    if (allImputatedFalse) {
        ShowToaster("Dose response has been successfully processed.", "green");
    } else {
        const imputatedKEs = doseKeyeventsWithInfo.filter(ke => ke.isImputated).map(ke => ke.ke).join(", ");
        ShowToaster(`The dose response has successfully been processed, But the following Key Events have no AC50 data and have been imputated: ${imputatedKEs}. This means that the result will be less accurate.`, "red", false);
    }
}

function removeGradientBarFromGraph() {
    cy.remove('node[id = "gradient-bar"]');
}

function addGradientBarToGraph() {
    cy.add({
        group: 'nodes',
        data: {
            id: 'gradient-bar',
            label: '',
            isLegend: true
        },
        position: {x: 0, y: 0},
        selectable: false,
        grabbable: true,
        classes: 'gradient-bar-node'
    });

    cy.style()
        .selector('.gradient-bar-node')
        .style({
            'background-image': "/static/images/bar-gradient.png",
            'background-fit': 'contain',
            'background-opacity': 1,
            'shape': 'rectangle',
            'width': 470,
            'height': 50,
            'border-width': 0,
            'border-opacity': 0
        })
        .update();
}

document.getElementById('runAllKeyEvents').addEventListener('click', async function () {
    const kePaths = cy?.nodes('[ke_type = "Key Event"], [ke_type = "Molecular Initiating Event"]').map(node => node.data('label'));
    if (!kePaths) {
        ShowToaster("You have to search for an AOP before you can run the dose response", "error")
        return;
    }
    document.getElementById('doseResponseDialog').style.display = "none";
    await gatherAndProcessDoseResponse(kePaths);
});

/*document.getElementById('triggerDoseResponse').addEventListener('click', async function () {
    const kePaths = document.getElementById("kePath").value
        .split(",")
        .map(path => path.trim());
    document.getElementById('doseResponseDialog').style.display = "none";
    await gatherAndProcessDoseResponse(kePaths);

});*/

//document.addEventListener('click', function(event) {
//    console.log(event.target); // See which element was clicked
//});