function selectBurg(id) {
    // Remove previous selection
    if (selectedId) {
        const prevRow = document.querySelector(`tr[data-id="${selectedId}"]`);
        const prevDot = document.querySelector(`.burg-dot[data-id="${selectedId}"]`);
        if (prevRow) prevRow.classList.remove('selected');
        if (prevDot) prevDot.classList.remove('selected');
    }

    // Clear any trade route highlights
    clearHighlights();

    // Clear previous table highlights (State and Trade)
    document.querySelectorAll('.related-highlight').forEach(el => el.classList.remove('selected'));

    selectedId = id;

    if (id) {
        const row = document.querySelector(`tr[data-id="${id}"]`);
        const dot = document.querySelector(`.burg-dot[data-id="${id}"]`);

        if (row) {
            row.classList.add('selected');
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        if (dot) {
            dot.classList.add('selected');

            // Highlight Related State
            const stateName = dot.getAttribute('data-state');
            if (stateName) {
                // Update Diplomacy Map if active
                const btn = document.getElementById('toggleMapMode');
                if (btn && btn.getAttribute('data-mode') === 'state') {
                    updateDiplomacyColors(stateName);
                }

                const stateTable = document.getElementById('stateTable');
                const stateRows = stateTable.getElementsByTagName('tr');
                for (let i = 1; i < stateRows.length; i++) {
                    const sRow = stateRows[i];
                    const nameCell = sRow.getElementsByTagName('td')[1]; // Name is 2nd column
                    if (nameCell && (nameCell.textContent || nameCell.innerText).trim() === stateName) {
                        sRow.classList.add('related-highlight');
                        sRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        break;
                    }
                }
            }

            // Highlight Related Trade Routes
            const burgName = dot.getAttribute('data-name');
            if (burgName) {
                ['foodTradeTable', 'goldTradeTable'].forEach(tableId => {
                    let scrolled = false;
                    const tTable = document.getElementById(tableId);
                    if (tTable) {
                        const tRows = tTable.getElementsByTagName('tr');
                        for (let i = 1; i < tRows.length; i++) {
                            const tRow = tRows[i];
                            const fromCell = tRow.getElementsByTagName('td')[0];
                            const toCell = tRow.getElementsByTagName('td')[1];

                            const fromName = (fromCell.textContent || fromCell.innerText).trim();
                            const toName = (toCell.textContent || toCell.innerText).trim();

                            if (fromName === burgName || toName === burgName) {
                                tRow.classList.add('related-highlight');
                                if (!scrolled) {
                                    tRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                    scrolled = true;
                                }
                            }
                        }
                    }
                });
            }
        }
    }
}

function highlightBurg(id) {
    selectBurg(id);
}

function clearHighlights() {
    // Clear Burg Dots
    document.querySelectorAll('.burg-dot').forEach(el => {
        el.classList.remove('selected', 'highlighted');
        el.style.fill = '';
        el.style.stroke = '';
    });

    // Clear Table Rows (Burgs, States, Trades)
    document.querySelectorAll('tr').forEach(el => {
        el.classList.remove('selected', 'related-highlight');
    });

    highlightedIds = [];
    selectedId = null;
}

function highlightState(stateName, color) {
    clearHighlights();

    // Find and highlight state row
    const stateTable = document.getElementById('stateTable');
    if (stateTable) {
        const stateRows = stateTable.getElementsByTagName('tr');
        for (let i = 1; i < stateRows.length; i++) {
            const sRow = stateRows[i];
            const nameCell = sRow.getElementsByTagName('td')[1];
            if (nameCell && (nameCell.textContent || nameCell.innerText).trim() === stateName) {
                sRow.classList.add('selected');
                break;
            }
        }
    }

    const burgsInState = [];
    let firstBurgScrolled = false;

    // Highlight Burg Dots and accumulate names
    const dots = document.querySelectorAll(`.burg-dot[data-state="${stateName}"]`);
    dots.forEach(dot => {
        dot.classList.add('highlighted');
        dot.style.fill = color;
        dot.style.stroke = '#000';

        const id = dot.getAttribute('data-id');
        const name = dot.getAttribute('data-name');
        if (id) {
            highlightedIds.push(id);
            // Highlight Burg Row
            const row = document.querySelector(`tr[data-id="${id}"]`);
            if (row) {
                row.classList.add('related-highlight');
                if (!firstBurgScrolled) {
                    row.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstBurgScrolled = true;
                }
            }
        }
        if (name) burgsInState.push(name);
    });

    // Highlight Trade Routes
    if (burgsInState.length > 0) {
        ['foodTradeTable', 'goldTradeTable'].forEach(tableId => {
            let firstTradeScrolled = false;
            const tTable = document.getElementById(tableId);
            if (tTable) {
                const tRows = tTable.getElementsByTagName('tr');
                for (let i = 1; i < tRows.length; i++) {
                    const tRow = tRows[i];
                    const fromCell = tRow.getElementsByTagName('td')[0];
                    const toCell = tRow.getElementsByTagName('td')[1];

                    const fromName = (fromCell.textContent || fromCell.innerText).trim();
                    const toName = (toCell.textContent || toCell.innerText).trim();

                    if (burgsInState.includes(fromName) || burgsInState.includes(toName)) {
                        tRow.classList.add('related-highlight');
                        if (!firstTradeScrolled) {
                            tRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            firstTradeScrolled = true;
                        }
                    }
                }
            }
        });
    }
}

function highlightTradeRoute(el, fromId, toId) {
    clearHighlights();
    if (selectedId) selectBurg(null); // Reset single burg selection mode

    // 1. Highlight the Trade Route Row(s)
    if (el) el.classList.add('selected');

    // 2. Identify and Highlight Burgs (Dots and Rows)
    const burgIds = [fromId, toId];
    const stateNames = new Set();

    burgIds.forEach(id => {
        // Highlight Dot
        const dot = document.querySelector(`.burg-dot[data-id="${id}"]`);
        if (dot) {
            dot.classList.add('selected');
            highlightedIds.push(id);

            const sName = dot.getAttribute('data-state');
            if (sName) stateNames.add(sName);
        }

        // Highlight Row
        const row = document.querySelector(`tr[data-id="${id}"]`);
        if (row) {
            row.classList.add('selected');
            row.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });

    // 3. Highlight States
    const stateTable = document.getElementById('stateTable');
    if (stateTable && stateNames.size > 0) {
        const stateRows = stateTable.getElementsByTagName('tr');
        let firstStateScrolled = false;
        for (let i = 1; i < stateRows.length; i++) {
            const sRow = stateRows[i];
            const nameCell = sRow.getElementsByTagName('td')[1];
            const rowStateName = (nameCell.textContent || nameCell.innerText).trim();

            if (nameCell && stateNames.has(rowStateName)) {
                sRow.classList.add('related-highlight');
                if (!firstStateScrolled) {
                    sRow.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstStateScrolled = true;
                }
            }
        }
    }
}

function selectState(stateId) {
    const btn = document.getElementById('toggleMapMode');
    const currentMode = btn.getAttribute('data-mode');

    if (currentMode === 'state') {
        updateDiplomacyColors(stateId);
    }
}
