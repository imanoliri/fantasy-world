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
    const tbody = table.querySelector('tbody') || table;

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

    const rows = Array.from(table.rows).slice(1);

    rows.sort((rowA, rowB) => {
        const cellA = rowA.getElementsByTagName("TD")[n];
        const cellB = rowB.getElementsByTagName("TD")[n];

        let aVal = cellA ? (cellA.textContent || cellA.innerText).toLowerCase() : "";
        let bVal = cellB ? (cellB.textContent || cellB.innerText).toLowerCase() : "";

        // Remove commas for number parsing
        const aNum = parseFloat(aVal.replace(/,/g, ''));
        const bNum = parseFloat(bVal.replace(/,/g, ''));

        if (!isNaN(aNum) && !isNaN(bNum)) {
            return dir === "asc" ? aNum - bNum : bNum - aNum;
        } else {
            if (aVal < bVal) return dir === "asc" ? -1 : 1;
            if (aVal > bVal) return dir === "asc" ? 1 : -1;
            return 0;
        }
    });

    // Re-append rows in sorted order
    // Using DocumentFragment for better performance
    const fragment = document.createDocumentFragment();
    rows.forEach(row => fragment.appendChild(row));

    // Append fragment to cached tbody
    if (tbody) {
        tbody.appendChild(fragment);
    }

    if (dir === "asc") {
        header.innerHTML = header.innerHTML.replace(' ▼', '') + ' ▲';
    } else {
        header.innerHTML = header.innerHTML.replace(' ▲', '') + ' ▼';
    }
}
