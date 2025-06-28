//sending the user inputted values to the backend for processing
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('submitBtn').addEventListener('click', function(event) {
        event.preventDefault();

        var formData = new FormData();

        var searchValueAops = document.getElementById("searchFieldAOPs").value;
        var searchValueKes = document.getElementById("searchFieldKEs").value;

        formData.append("searchFieldAOPs", searchValueAops);
        formData.append("searchFieldKEs", searchValueKes);

        document.querySelectorAll('#aop_checkboxes input[type="checkbox"]').forEach(function(checkbox) {
            formData.append(checkbox.name, checkbox.checked ? "1" : "0");
        });

        document.querySelectorAll('#ke_checkboxes input[type="checkbox"]').forEach(function(checkbox) {
            formData.append(checkbox.name, checkbox.checked ? "1" : "0");
        });

        var csrfToken = document.querySelector('input[name="csrf_token"]').value;
        formData.append('csrf_token', csrfToken);

        render_table('/data-extraction-submit', formData)
    });
});

function render_table(url_string, formData) {
    fetch(url_string, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const table = document.getElementById('dynamicTable');
        table.innerHTML = ''; // Clear the table

        const columns = data.head.vars;
        let thead = table.createTHead();
        let headerRow = thead.insertRow();

        columns.forEach(header => {
            let th = document.createElement('th');
            th.innerText = header;

            // Create a span element to serve as a drag handle
            let span = document.createElement('span');
            span.classList.add('resize-handle');
            th.appendChild(span);

            headerRow.appendChild(th);
        });

        let tbody = document.createElement('tbody');
        table.appendChild(tbody);

        data.results.bindings.forEach(binding => {
            let row = tbody.insertRow();
            columns.forEach(column => {
                let cell = row.insertCell();
                let text = binding[column] && binding[column].value ? binding[column].value : "";

                // Create a span for the text
                let span = document.createElement('span');
                span.classList.add('cell-text');
                span.innerText = text;

                // Add a button or link to expand/collapse
                let toggleButton = document.createElement('a');
                toggleButton.href = '#';
                toggleButton.innerText = 'More';
                toggleButton.classList.add('toggle-text');
                toggleButton.onclick = function() {
                    span.classList.toggle('expanded');
                    toggleButton.innerText = span.classList.contains('expanded') ? 'Less' : 'More';
                    adjustCellContentVisibility(span.parentElement);
                    return false;
                };

                // Initially hide long text if necessary
                if (text.length > 100) {
                    span.classList.add('collapsed');
                    cell.appendChild(span);
                    cell.appendChild(toggleButton);
                } else {
                    cell.appendChild(span); // No need for toggle button if text is short
                }
            });
        });
        initializeColumnResizing();
    })
    .catch(error => console.error('Error:', error));
}

document.getElementById('saveCsvBtn').addEventListener('click', function() {

        const table = document.getElementById('dynamicTable');
        let csvContent = "data:text/csv;charset=utf-8,";

        // Iterate over each row in the table
        for (let i = 0; i < table.rows.length; i++) {
            let row = [], cols = table.rows[i].querySelectorAll("td, th");

            // Iterate over each column in the row
            cols.forEach(function(col) {
                let cellTextElement = col.querySelector('.cell-text');
                let cellValue = cellTextElement ? cellTextElement.innerText : col.innerText;

                // Escape double quotes in cell value
                cellValue = cellValue.replace(/"/g, '""');

                // Wrap cell value in double quotes
                row.push(`"${cellValue}"`);
            });

            csvContent += row.join(",") + "\r\n";
        }

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "table_data.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
});

document.getElementById('saveExcelBtn').addEventListener('click', function() {
    const table = document.getElementById('dynamicTable');
    let worksheet_data = [];

    // Iterate over each row in the table
    for (let i = 0; i < table.rows.length; i++) {
        let row_data = [], cols = table.rows[i].querySelectorAll("td, th");

        // Iterate over each column in the row
        cols.forEach(function(col) {

            let cellTextElement = col.querySelector('.cell-text');
            let cellValue = cellTextElement ? cellTextElement.innerText : col.innerText;

            row_data.push(cellValue);
        });

        worksheet_data.push(row_data);
    }

    // Create a new workbook and add the worksheet
    let wb = XLSX.utils.book_new();
    let ws = XLSX.utils.aoa_to_sheet(worksheet_data);
    XLSX.utils.book_append_sheet(wb, ws, "Sheet1");

    // Generate an Excel file
    XLSX.writeFile(wb, "table_data.xlsx");
});

document.addEventListener('DOMContentLoaded', function() {
    const inputAOPs = document.getElementById('searchFieldAOPs');
    const inputKEs = document.getElementById('searchFieldKEs');
    const aopCheckboxes = document.querySelectorAll('#aop_checkboxes input[type="checkbox"]');
    const keCheckboxes = document.querySelectorAll('#ke_checkboxes input[type="checkbox"]');

    function clearKE() {
        inputKEs.value = '';
        keCheckboxes.forEach(checkbox => checkbox.checked = false);
    }

    function clearAOP() {
        inputAOPs.value = '';
        aopCheckboxes.forEach(checkbox => checkbox.checked = false);
    }

    inputAOPs.addEventListener('input', clearKE);
    aopCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', clearKE);
    });

    inputKEs.addEventListener('input', clearAOP);
    keCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', clearAOP);
    });
});

function initializeColumnResizing() {
    document.querySelectorAll('th .resize-handle').forEach(handle => {
        handle.addEventListener('mousedown', function(e) {
            e.preventDefault(); // Avoid text selection

            let startX = e.pageX;
            let startWidth = handle.parentElement.offsetWidth;

            function mouseMoveHandler(e) {
                // Calculate the new width
                let newWidth = startWidth + (e.pageX - startX);
                console.log(`New Width: ${newWidth}, Current Width: ${handle.parentElement.style.width}`);
                handle.parentElement.style.width = `${newWidth}px`;
                adjustCellContentVisibility(handle.parentElement);
            }

            function mouseUpHandler() {
                document.removeEventListener('mousemove', mouseMoveHandler);
                document.removeEventListener('mouseup', mouseUpHandler);
            }

            document.addEventListener('mousemove', mouseMoveHandler);
            document.addEventListener('mouseup', mouseUpHandler);
        });
    });
}

function adjustCellContentVisibility(column) {
    let columnIndex = Array.from(column.parentNode.children).indexOf(column) + 1;
    document.querySelectorAll(`tbody tr td:nth-child(${columnIndex})`).forEach(td => {
        let cellContent = td.querySelector('.cell-text');
        if (!cellContent) return; // Skip if no .cell-text

        // Check if the cell content is expanded
        if (cellContent.classList.contains('expanded')) {
            cellContent.style.maxWidth = "none";
            cellContent.style.overflow = "visible";
            cellContent.style.textOverflow = "clip";
            cellContent.style.whiteSpace = "normal";
        } else {
            cellContent.style.maxWidth = `${td.clientWidth - 10}px`;
            cellContent.style.overflow = "hidden";
            cellContent.style.textOverflow = "ellipsis";
            cellContent.style.whiteSpace = "nowrap";
        }
    });
}

