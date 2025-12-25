const svg = document.getElementById('mapSvg');
const tooltip = document.getElementById('tooltip');
const mapContainer = document.getElementById('mapContainer');
const table = document.getElementById('burgTable');
let selectedId = null;
let highlightedIds = [];

// These variables will be defined by data injection in the HTML itself
// let diplomacyMatrix = [];
// let stateNameIdMap = [];


/* Dropdown Logic */
function toggleDropdown(id) {
    document.getElementById(id).classList.toggle("show");
}

function showStateTooltip(e, content) {
    const tooltip = document.getElementById('tooltip');
    tooltip.innerHTML = content;
    tooltip.style.display = 'block';

    // Position near the cursor
    let left = e.clientX + 15;
    let top = e.clientY + 15;

    // Adjust if going off screen
    if (left + 220 > window.innerWidth) {
        left = e.clientX - 230;
    }

    if (top + 150 > window.innerHeight) {
        top = e.clientY - 160;
    }

    tooltip.style.left = left + 'px';
    tooltip.style.top = top + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.display = 'none';
}

function toggleFoodTrades() {
    const btn = document.getElementById('toggleFoodTrades');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-food-trades');
    } else {
        document.body.classList.remove('show-food-trades');
    }
}

function toggleGoldTrades() {
    const btn = document.getElementById('toggleGoldTrades');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-gold-trades');
    } else {
        document.body.classList.remove('show-gold-trades');
    }
}

function toggleCapitals() {
    const btn = document.getElementById('toggleCapitals');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        document.body.classList.add('show-capitals');
    } else {
        document.body.classList.remove('show-capitals');
    }
}

function toggleTable() {
    const btn = document.getElementById('toggleTable');
    const container = document.getElementById('burgTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleStateTable() {
    const btn = document.getElementById('toggleStateTable');
    const container = document.getElementById('stateTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleFoodTradeTable() {
    const btn = document.getElementById('toggleFoodTradeTable');
    const container = document.getElementById('foodTradeTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleGoldTradeTable() {
    const btn = document.getElementById('toggleGoldTradeTable');
    const container = document.getElementById('goldTradeTableContainer');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        container.classList.remove('hidden');
    } else {
        container.classList.add('hidden');
    }
    window.dispatchEvent(new Event('resize'));
}

function toggleMap() {
    const btn = document.getElementById('toggleMap');
    const mapGroup = document.getElementById('mapBackground');
    btn.classList.toggle('active');
    if (btn.classList.contains('active')) {
        mapGroup.style.display = 'block';
    } else {
        mapGroup.style.display = 'none';
    }
}


const relationColors = {
    "Ally": "#32CD32",      // Lime Green
    "Friendly": "#90EE90",  // Light Green
    "Neutral": "#D3D3D3",   // Light Grey
    "Suspicion": "#FFA500", // Orange
    "Enemy": "#FF4500",     // Orange Red
    "War": "#FF0000",       // Red
    "Vassal": "#87CEEB",    // Sky Blue
    "Suzerain": "#C8A2C8",  // Lilac
    "Unknown": "#F5F5F5",   // White Smoke
    "x": "#800080"          // Selected State (Purple)
};

function toggleMapMode() {
    const btn = document.getElementById('toggleMapMode');
    const paths = document.querySelectorAll('#mapBackground path');

    // Use data attribute for state tracking
    const currentMode = btn.getAttribute('data-mode') || 'biome';

    if (currentMode === 'biome') {
        // Switch to State
        btn.innerText = 'Mode: State';
        btn.setAttribute('data-mode', 'state');
        paths.forEach(p => {
            p.setAttribute('fill', p.getAttribute('data-state-color'));
        });
    } else if (currentMode === 'state') {
        // Switch to Heightmap
        btn.innerText = 'Mode: Heightmap';
        btn.setAttribute('data-mode', 'heightmap');

        paths.forEach(p => {
            // Heightmap logic: darken color based on height
            let h = parseInt(p.getAttribute('data-height'));
            let c = 255 - h * 2;
            if (c < 0) c = 0;
            if (p.getAttribute('data-is-water') === 'true') {
                p.setAttribute('fill', `rgb(${c / 2}, ${c / 2}, ${200 + h / 2})`);
            } else {
                p.setAttribute('fill', `rgb(${c}, ${c}, ${c})`);
            }
        });
    } else if (currentMode === 'heightmap') {
        // Switch to Temperature
        btn.innerText = 'Mode: Temperature';
        btn.setAttribute('data-mode', 'temperature');
        paths.forEach(p => {
            const t = parseInt(p.getAttribute('data-temp'));
            p.setAttribute('fill', getColorForTemp(t));
        });
    } else {
        // Switch to Biome
        btn.innerText = 'Mode: Biome';
        btn.setAttribute('data-mode', 'biome');
        paths.forEach(p => {
            p.setAttribute('fill', p.getAttribute('data-biome-color'));
        });
    }
}

function getColorForHeight(h) {
    // Azgaar height range: 0-100 (usually)
    // Water: < 20
    // Land: >= 20

    if (h < 20) {
        // Water: Uniform Deep Blue
        return "#000080";
    } else {
        // Land gradient: Green -> Yellow -> Brown -> White
        if (h < 40) return "#228B22"; // Forest Green (Lowlands)
        if (h < 60) return "#9ACD32"; // Yellow Green (Hills)
        if (h < 80) return "#CD853F"; // Peru (Mountains)
        return "#FFFFFF"; // White (Peaks)
    }
}

function getColorForTemp(t) {
    // Range: approx -30 to 50 (Celsius)
    // Hot (> 30): Red
    // Warm (20-30): Orange
    // Temperate (10-20): Yellow/Green
    // Cool (0-10): Cyan
    // Cold (-10 to 0): Blue
    // Freezing (< -10): Purple

    if (t < -10) return "#4B0082"; // Indigo (Deep Freeze)
    if (t < -5) return "#800080"; // Purple (Freezing)
    if (t < 0) return "#0000FF"; // Blue (Cold)
    if (t < 5) return "#00BFFF"; // Deep Sky Blue (Cool)
    if (t < 10) return "#ADFF2F"; // Green Yellow (Temperate)
    if (t < 15) return "#FFD700"; // Gold (Warm)
    if (t < 20) return "#FF8C00"; // Dark Orange (Hot)
    return "#FF0000"; // Red (Scorching)
}

function updateDiplomacyColors(stateIdentifier) {
    let stateId = null;

    // Try to find state ID
    if (typeof stateIdentifier === 'number') {
        stateId = stateIdentifier;
    } else if (typeof stateIdentifier === 'string') {
        if (stateNameIdMap.hasOwnProperty(stateIdentifier)) {
            stateId = stateNameIdMap[stateIdentifier];
        }
    }

    // FIX: Treat selecting "Neutral" (0) as deselecting
    if (stateId === 0) stateId = null;

    const paths = document.querySelectorAll('#mapBackground path');

    if (stateId !== null && diplomacyMatrix[stateId]) {
        const relations = diplomacyMatrix[stateId];

        paths.forEach(p => {
            const isWater = p.hasAttribute('data-is-water');
            if (isWater) {
                p.setAttribute('fill', '#333333'); // Dark Gray for water
            } else {
                const pStateId = parseInt(p.getAttribute('data-state-id'));

                // FIX: Explicitly handle Neutrals (ID 0)
                if (pStateId === 0 && stateId !== 0) {
                    p.setAttribute('fill', '#ffffff'); // White for Neutrals
                } else if (!isNaN(pStateId) && pStateId < relations.length) {
                    const relation = relations[pStateId];
                    // Highlight self differently?
                    let color = relationColors[relation] || relationColors['Unknown'];
                    if (pStateId === stateId) color = relationColors['x'];

                    p.setAttribute('fill', color);
                }
            }
        });
    } else {
        // Reset to State Colors if no state selected
        paths.forEach(p => {
            const isWater = p.hasAttribute('data-is-water');
            if (isWater) {
                p.setAttribute('fill', '#333333'); // Dark Gray
            } else {
                // Revert to state color
                p.setAttribute('fill', p.getAttribute('data-state-color'));
            }
        });
    }
}


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


// Map Interactions
svg.addEventListener('click', (e) => {
    if (e.target.classList.contains('burg-dot')) {
        const id = e.target.getAttribute('data-id');
        selectBurg(id);
    } else {
        // Deselect if clicking empty space
        // selectBurg(null);
    }
});

svg.addEventListener('mousemove', (e) => {
    if (e.target.classList.contains('burg-dot')) {
        const name = e.target.getAttribute('data-name');
        const pop = parseInt(e.target.getAttribute('data-pop')).toLocaleString();
        const type = e.target.getAttribute('data-type');
        const state = e.target.getAttribute('data-state');
        const gold = e.target.getAttribute('data-gold');
        const food = e.target.getAttribute('data-food');
        const quartiers = e.target.getAttribute('data-quartiers');
        const isCapital = e.target.classList.contains('capital');

        let displayName = isCapital ? `★ ${name}` : name;

        let tooltipContent = `<strong>${displayName}</strong><br>State: ${state}<br>Type: ${type}<br>Pop: ${pop}<br>Food: ${food}<br>Gold: ${gold}`;
        if (quartiers) {
            tooltipContent += `<hr style="margin: 5px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">${quartiers}`;
        }

        tooltip.innerHTML = tooltipContent;
        tooltip.style.display = 'block';

        // Smart positioning to keep within viewport
        let top = e.clientY + 10;
        let left = e.clientX + 10;

        // Check if tooltip goes off bottom
        if (top + 100 > window.innerHeight) {
            top = e.clientY - 100; // Move above cursor
        }

        tooltip.style.left = left + 'px';
        tooltip.style.top = top + 'px';
    } else if (e.target.tagName === 'path') {
        const btn = document.getElementById('toggleMapMode');
        const mode = btn.getAttribute('data-mode') || 'biome';

        let content = '';
        if (mode === 'biome') {
            const biome = e.target.getAttribute('data-biome');
            if (biome) content = `<strong>Biome:</strong> ${biome}`;
        } else if (mode === 'state') {
            const state = e.target.getAttribute('data-state');
            if (state) content = `<strong>State:</strong> ${state}`;
        } else if (mode === 'heightmap') {
            const h = e.target.getAttribute('data-height');
            if (h) content = `<strong>Height:</strong> ${h}`;
        } else if (mode === 'temperature') {
            const t = e.target.getAttribute('data-temp');
            if (t) content = `<strong>Temp:</strong> ${t}°C`;
        }

        if (content) {
            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 15) + 'px';
            tooltip.style.top = (e.clientY + 15) + 'px';
        } else {
            tooltip.style.display = 'none';
        }
    } else {
        tooltip.style.display = 'none';
    }
});

// Table Tooltip Interactions
table.addEventListener('mousemove', (e) => {
    if (e.target.classList.contains('quartier-cell')) {
        const details = e.target.getAttribute('data-details');
        if (details) {
            tooltip.innerHTML = details;
            tooltip.style.display = 'block';
            tooltip.style.left = (e.clientX + 10) + 'px';
            tooltip.style.top = (e.clientY + 10) + 'px';
        }
    } else {
        // Only hide if not over map dot (which is separate)
        // But we are in table container, so map tooltip is not active
        tooltip.style.display = 'none';
    }
});

table.addEventListener('mouseleave', () => {
    tooltip.style.display = 'none';
});

// Pan and Zoom (Basic)
let isPanning = false;
let startX, startY;
let viewBox = svg.getAttribute('viewBox').split(' ').map(parseFloat);

mapContainer.addEventListener('mousedown', (e) => {
    if (e.target === svg || e.target.tagName === 'circle' || e.target.tagName === 'line' || e.target.tagName === 'path') {
        isPanning = true;
        startX = e.clientX;
        startY = e.clientY;
        mapContainer.style.cursor = 'grabbing';
    }
});

mapContainer.addEventListener('mousemove', (e) => {
    if (!isPanning) return;
    e.preventDefault();
    const dx = (e.clientX - startX) * (viewBox[2] / mapContainer.clientWidth);
    const dy = (e.clientY - startY) * (viewBox[3] / mapContainer.clientHeight);

    viewBox[0] -= dx;
    viewBox[1] -= dy;
    svg.setAttribute('viewBox', viewBox.join(' '));

    startX = e.clientX;
    startY = e.clientY;
});

mapContainer.addEventListener('mouseup', () => {
    isPanning = false;
    mapContainer.style.cursor = 'default';
});

mapContainer.addEventListener('mouseleave', () => {
    isPanning = false;
    mapContainer.style.cursor = 'default';
});

mapContainer.addEventListener('wheel', (e) => {
    e.preventDefault();
    const scale = e.deltaY > 0 ? 1.1 : 0.9;
    const w = viewBox[2];
    const h = viewBox[3];

    viewBox[2] *= scale;
    viewBox[3] *= scale;

    // Zoom towards center
    viewBox[0] -= (viewBox[2] - w) / 2;
    viewBox[1] -= (viewBox[3] - h) / 2;

    svg.setAttribute('viewBox', viewBox.join(' '));
});


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


