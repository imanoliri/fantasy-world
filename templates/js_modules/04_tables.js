function toggleAllStates(source) {
    const checkboxes = document.querySelectorAll('#stateCheckboxes input[type="checkbox"]');
    for (var i = 0, n = checkboxes.length; i < n; i++) {
        checkboxes[i].checked = source.checked;
    }
    filterTable();
}


// COPY-PASTED HELPER FUNCTIONS TO ENSURE FUNCTIONALITY
function filterTable() {
    const searchInput = document.getElementById('searchInput');
    const filterText = searchInput.value.toLowerCase();

    // Get selected types
    const typeCheckboxes = document.querySelectorAll('#typeCheckboxes input[type="checkbox"]');
    const selectedTypes = [];

    typeCheckboxes.forEach(cb => {
        if (cb.value !== 'all' && cb.checked) {
            selectedTypes.push(cb.value);
        }
    });

    // Get selected states
    const stateCheckboxes = document.querySelectorAll('#stateCheckboxes input[type="checkbox"]');
    const selectedStates = [];

    stateCheckboxes.forEach(cb => {
        if (cb.value !== 'all' && cb.checked) {
            selectedStates.push(cb.value);
        }
    });

    const rows = table.getElementsByTagName('tr');

    // Filter Table
    // Start from 1 to skip header
    for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const nameCell = row.getElementsByTagName('td')[0];
        const typeCell = row.getElementsByTagName('td')[1];
        const stateCell = row.getElementsByTagName('td')[2];
        const burgId = row.getAttribute('data-id');

        if (nameCell && typeCell && stateCell) {
            const nameText = nameCell.textContent || nameCell.innerText;
            const typeText = typeCell.textContent || typeCell.innerText;
            const stateText = stateCell.textContent || stateCell.innerText;
            const isCapitalRow = row.classList.contains('capital-row');

            const matchesName = nameText.toLowerCase().indexOf(filterText) > -1;

            // Check if type matches ANY of the selected types
            let matchesType = false;
            if (selectedTypes.includes(typeText)) {
                matchesType = true;
            }
            if (selectedTypes.includes('Capital') && isCapitalRow) {
                matchesType = true;
            }

            // Check if state matches ANY of the selected states
            let matchesState = false;
            if (selectedStates.includes(stateText)) {
                matchesState = true;
            }

            const isVisible = matchesName && matchesType && matchesState;

            if (isVisible) {
                row.style.display = "";
            } else {
                row.style.display = "none";
            }

            // Filter Map Dot corresponding to this row
            const dot = document.querySelector(`.burg-dot[data-id="${burgId}"]`);
            if (dot) {
                if (isVisible) {
                    dot.classList.remove('hidden');
                } else {
                    dot.classList.add('hidden');
                }
            }
        }
    }

    // Filter State Table
    const stateTable = document.getElementById('stateTable');
    if (stateTable) {
        const stateRows = stateTable.getElementsByTagName('tr');
        // Start from 1 to skip header
        for (let i = 1; i < stateRows.length; i++) {
            const row = stateRows[i];
            const nameCell = row.getElementsByTagName('td')[1]; // Name is 2nd column

            if (nameCell) {
                const stateName = nameCell.textContent || nameCell.innerText;

                // Check if state matches ANY of the selected states
                let matchesState = false;
                if (selectedStates.includes(stateName)) {
                    matchesState = true;
                }

                // Check search text against state name
                const matchesSearch = stateName.toLowerCase().indexOf(filterText) > -1;

                if (matchesState && matchesSearch) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            }
        }
    }
}

function toggleAllTypes(source) {
    const checkboxes = document.querySelectorAll('#typeCheckboxes input');
    for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].checked = source.checked;
    }
    filterTable();
}

function sortTable(n, header, tableId) {
    const table = document.getElementById(tableId);
    let dir = "asc";

    // Reset other headers
    const headers = table.querySelectorAll('th');
    headers.forEach(h => {
        if (h !== header) {
            h.innerHTML = h.innerHTML.replace(' ▲', '').replace(' ▼', '');
        }
    });

    if (header.innerHTML.includes('▲')) {
        dir = "desc";
    }

    let switching = true;
    let shouldSwitch, i;

    while (switching) {
        switching = false;
        const rows = table.rows;

        for (i = 1; i < (rows.length - 1); i++) {
            shouldSwitch = false;
            const x = rows[i].getElementsByTagName("TD")[n];
            const y = rows[i + 1].getElementsByTagName("TD")[n];

            let xVal = x.innerHTML.toLowerCase();
            let yVal = y.innerHTML.toLowerCase();

            // Check if numeric (remove commons)
            const xNum = parseFloat(xVal.replace(/,/g, ''));
            const yNum = parseFloat(yVal.replace(/,/g, ''));

            if (!isNaN(xNum) && !isNaN(yNum)) {
                if (dir === "asc") {
                    if (xNum > yNum) { shouldSwitch = true; break; }
                } else {
                    if (xNum < yNum) { shouldSwitch = true; break; }
                }
            } else {
                if (dir === "asc") {
                    if (xVal > yVal) { shouldSwitch = true; break; }
                } else {
                    if (xVal < yVal) { shouldSwitch = true; break; }
                }
            }
        }
        if (shouldSwitch) {
            rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
            switching = true;
        }
    }

    if (dir === "asc") {
        header.innerHTML = header.innerHTML.replace(' ▼', '') + ' ▲';
    } else {
        header.innerHTML = header.innerHTML.replace(' ▲', '') + ' ▼';
    }
}
