import csv
import json
import math

# TRADES_FILE = 'data/trade_routes.csv' # Removed dependency

def generate_map(burgs, output_file, trades_data=None, map_name="Interactive Map", states=None, cultures=None):
    print(f"Generating interactive map for {map_name} with {len(burgs)} burgs...")
    
    # Determine map bounds
    xs = [b['x'] for b in burgs]
    ys = [b['y'] for b in burgs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x + 100
    height = max_y - min_y + 100
    
    # Create a lookup for burg coordinates
    burg_coords = {str(b['id']): (b['x'], b['y']) for b in burgs}
    
    # Generate SVG Elements
    svg_elements = []
    
    # 1. Trade Routes (Lines) - Draw first so they are behind burgs
    if trades_data:
        for t in trades_data:
            from_id = str(t['From_ID'])
            to_id = str(t['To_ID'])
            
            if from_id in burg_coords and to_id in burg_coords:
                x1, y1 = burg_coords[from_id]
                x2, y2 = burg_coords[to_id]
                
                # Style based on commodity or amount? 
                # For now, simple styling.
                commodity = t['Commodity']
                stroke_color = '#f39c12' if commodity == 'Net_Gold' else '#27ae60' # Gold vs Food
                
                svg_elements.append(f"""
                    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                          stroke="{stroke_color}" stroke-width="1" stroke-opacity="0.6"
                          class="trade-route" />
                """)

    # 2. Burgs (Circles)
    table_rows = []
    
    # Color mapping
    type_colors = {
        'Naval': '#3498db',    # Blue
        'Generic': '#95a5a6',  # Gray
        'Hunting': '#2ecc71',  # Green
        'Capital': '#e74c3c',  # Red (if we use capital field)
        'Mining': '#f1c40f'    # Yellow
    }
    
    # Collect all citizen types for table headers
    citizen_types = set()
    burg_types = set()
    for b in burgs:
        citizen_types.update(b.get('quartiers', {}).keys())
        burg_types.add(b.get('type', 'Unknown'))
    
    sorted_citizen_types = sorted(list(citizen_types))
    sorted_burg_types = sorted(list(burg_types))
    
    # Generate Type Filter Options (Checkboxes)
    type_checkboxes = '<div class="checkbox-list" id="typeCheckboxes">'
    type_checkboxes += '<label><input type="checkbox" value="all" checked onchange="toggleAllTypes(this)"> All Types</label>'
    for t in sorted_burg_types:
        type_checkboxes += f'<label><input type="checkbox" value="{t}" checked onchange="filterTable()"> {t}</label>'
    type_checkboxes += '<label><input type="checkbox" value="Capital" checked onchange="filterTable()"> Capital</label>'
    type_checkboxes += '</div>'

    # Generate State Filter Options (Checkboxes)
    state_checkboxes = '<div class="checkbox-list" id="stateCheckboxes">'
    state_checkboxes += '<label><input type="checkbox" value="all" checked onchange="toggleAllStates(this)"> All States</label>'
    
    # Sort states by name
    sorted_states = sorted(states, key=lambda x: x.get('name', '')) if states else []
    
    for s in sorted_states:
        s_name = s.get('name', 'Unknown')
        state_checkboxes += f'<label><input type="checkbox" value="{s_name}" checked onchange="filterTable()"> {s_name}</label>'
    state_checkboxes += '</div>'

    for b in burgs:
        # Map Logic
        cx = b['x']
        cy = b['y']
        
        # Radius based on population (sqrt scale)
        r = math.sqrt(b['population']) / 10
        if r < 3: r = 3
        if r > 20: r = 20
        
        color = type_colors.get(b.get('type'), '#95a5a6')
        
        # Net Gold Logic for Stroke
        net_gold = b.get('net_production_burg', {}).get('Net_Gold', 0)
        if net_gold > 0.01:
            stroke = '#2ecc71' # Green
        elif net_gold < -0.01:
            stroke = '#e74c3c' # Red
        else:
            stroke = '#ffffff' # White
            
        # Capital Logic
        is_capital = b.get('capital') == 1
        capital_class = " capital" if is_capital else ""
        stroke_width = 3 if is_capital else 2
        
        # Table Logic
        net_food = b.get('net_production_burg', {}).get('Net_Food', 0)
        quartiers = b.get('nr_quartiers', 0)
        
        # Quartier Details for Tooltip
        quartier_details = ""
        # Get counts for all types (including 0s) and sort by count desc
        type_counts = []
        for ct in sorted_citizen_types:
            count = b.get('quartiers', {}).get(ct, 0)
            type_counts.append((ct, count))
        
        type_counts.sort(key=lambda x: x[1], reverse=True)
        
        for ct, count in type_counts:
            if count > 0:
                quartier_details += f"{ct}: {count}<br>"

        # SVG Element (Removed <title> to avoid double tooltip)
        svg_elements.append(f"""
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"
                    class="burg-dot{capital_class}" data-id="{b['id']}" data-name="{b['name']}" 
                    data-pop="{b['population']}" data-type="{b.get('type', 'Unknown')}" 
                    data-state="{b.get('state_name', 'Unknown')}"
                    data-gold="{net_gold:.2f}" data-food="{net_food:.2f}"
                    data-quartiers="{quartier_details}">
            </circle>
        """)
        
        name_display = f"★ {b['name']}" if is_capital else b['name']
        row_class = "capital-row" if is_capital else ""
        
        table_rows.append(f"""
            <tr data-id="{b['id']}" class="{row_class}" onclick="highlightBurg({b['id']})">
                <td>{name_display}</td>
                <td>{b.get('type', 'Unknown')}</td>
                <td>{b.get('state_name', 'Unknown')}</td>
                <td class="quartier-cell" data-details="{quartier_details}">{quartiers}</td>
                <td>{b['population']:,}</td>
                <td class="{ 'pos' if net_food > 0 else 'neg' }">{net_food:.2f}</td>
                <td class="{ 'pos' if net_gold > 0 else 'neg' }">{net_gold:.2f}</td>
            </tr>
        """)

    # Update sort indices
    idx_pop = 4
    idx_food = 5
    idx_gold = 6

    # 3. States Table Rows
    state_rows = []
    if states:
        # Create lookups
        burg_name_lookup = {b['id']: b['name'] for b in burgs}
        culture_name_lookup = {}
        if cultures:
            for c in cultures:
                culture_name_lookup[c['i']] = c['name']

        for s in states:
            # Columns: color, name, capital, type, culture, burgs, area, cells, form, fullname
            color = s.get('color', '#cccccc')
            name = s.get('name', 'Unknown')
            capital_id = s.get('capital', 0)
            capital_name = burg_name_lookup.get(capital_id, 'Unknown') if capital_id else 'None'
            type_ = s.get('type', 'Unknown')
            culture_id = s.get('culture', 0)
            culture_name = culture_name_lookup.get(culture_id, 'Unknown')
            burgs_count = s.get('burgs', 0)
            area = s.get('area', 0)
            cells = s.get('cells', 0)
            form = s.get('form', 'Unknown')
            fullname = s.get('fullName', name)
            
            state_rows.append(f"""
                <tr>
                    <td><span class="color-box" style="background-color: {color}; display: inline-block; width: 15px; height: 15px; border: 1px solid #333;"></span></td>
                    <td>{name}</td>
                    <td>{capital_name}</td>
                    <td>{type_}</td>
                    <td>{culture_name}</td>
                    <td>{burgs_count}</td>
                    <td>{area:,}</td>
                    <td>{cells:,}</td>
                    <td>{form}</td>
                    <td>{fullname}</td>
                </tr>
            """)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Map: {map_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
        header {{ background: #2c3e50; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 10; }}
        h1 {{ margin: 0; font-size: 1.2rem; }}
        
        .controls {{ display: flex; align-items: center; gap: 10px; font-size: 0.9rem; }}
        
        .container {{ display: flex; flex: 1; overflow: hidden; position: relative; }}
        
        /* Map Section */
        .map-container {{ width: 100%; height: 100%; background: #ecf0f1; position: relative; overflow: hidden; }}
        svg {{ width: 100%; height: 100%; cursor: grab; }}
        svg:active {{ cursor: grabbing; }}
        
        .burg-dot {{ transition: r 0.2s, stroke-width 0.2s, opacity 0.3s; cursor: pointer; }}
        .burg-dot:hover {{ stroke: #333; stroke-width: 3px; }}
        .burg-dot.selected {{ stroke: #000; stroke-width: 4px; r: 15px; animation: pulse 1s infinite; }}
        .burg-dot.hidden {{ display: none; }}
        
        /* Only show capital glow when body has show-capitals class */
        body.show-capitals .burg-dot.capital {{ filter: drop-shadow(0 0 6px gold); }}
        
        .trade-route {{ pointer-events: none; transition: opacity 0.3s; }}
        .trade-route.hidden {{ opacity: 0; }}
        
        @keyframes pulse {{
            0% {{ stroke-opacity: 1; }}
            50% {{ stroke-opacity: 0.5; }}
            100% {{ stroke-opacity: 1; }}
        }}

        /* Table Section */
        .tables-wrapper {{ position: absolute; right: 0; top: 0; bottom: 0; display: flex; z-index: 20; pointer-events: none; }}
        .table-container, .state-table-container {{ width: 800px; overflow-y: auto; background: rgba(255, 255, 255, 0.95); padding: 0; box-shadow: -2px 0 5px rgba(0,0,0,0.1); border-left: 1px solid #ddd; pointer-events: auto; }}
        .hidden {{ display: none !important; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; position: sticky; top: 0; z-index: 1; cursor: pointer; }}
        th:hover {{ background: #e9ecef; }}
        tr:hover {{ background-color: #f1f1f1; cursor: pointer; }}
        tr.selected {{ background-color: #fff3cd; border-left: 5px solid #f1c40f; }}
        tr.capital-row {{ font-weight: bold; background-color: #fffbf0; }}
        
        /* Tooltip */
        .tooltip {{ position: fixed; background: rgba(0,0,0,0.8); color: white; padding: 5px 10px; border-radius: 4px; pointer-events: none; font-size: 0.8rem; display: none; z-index: 1000; max-width: 200px; }}
        
        .controls input[type="text"] {{
            padding: 5px;
            border-radius: 4px;
            border: 1px solid #ccc;
            margin-right: 10px;
        }}
        
        /* Custom Dropdown */
        .dropdown {{ position: relative; display: inline-block; }}
        .dropbtn {{ background-color: #34495e; color: white; padding: 5px 10px; font-size: 0.9rem; border: none; cursor: pointer; border-radius: 4px; }}
        .dropdown-content {{ display: none; position: absolute; background-color: #f9f9f9; min-width: 160px; box-shadow: 0px 8px 16px 0px rgba(0,0,0,0.2); z-index: 100; max-height: 300px; overflow-y: auto; padding: 5px; border-radius: 4px; }}
        .dropdown-content label {{ color: black; padding: 5px; display: block; cursor: pointer; }}
        .dropdown-content label:hover {{ background-color: #f1f1f1; }}
        .dropdown-content.show {{ display: block; }}
        .dropdown:hover .dropbtn {{ background-color: #2c3e50; }}
    </style>
</head>
<body class="show-capitals">
    <header>
        <h1>Interactive Map: {map_name}</h1>
        <div class="controls">
            <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="Search names...">
            
            <div class="dropdown">
                <button class="dropbtn" onclick="toggleDropdown('typeDropdown')">Filter Types ▼</button>
                <div class="dropdown-content" id="typeDropdown">
                    {type_checkboxes}
                </div>
            </div>

            <div class="dropdown">
                <button class="dropbtn" onclick="toggleDropdown('stateDropdown')">Filter States ▼</button>
                <div class="dropdown-content" id="stateDropdown">
                    {state_checkboxes}
                </div>
            </div>
            
            <label><input type="checkbox" id="toggleTrades" checked onchange="toggleTrades()"> Show Trade Routes</label>
            <label><input type="checkbox" id="toggleCapitals" checked onchange="toggleCapitals()"> Highlight Capitals</label>
            <label><input type="checkbox" id="toggleStateTable" onchange="toggleStateTable()"> Show States Table</label>
            <label><input type="checkbox" id="toggleTable" onchange="toggleTable()"> Show Burgs Table</label>
            <span>| Total Burgs: {len(burgs)}</span>
        </div>
    </header>
    
    <div class="container">
        <div class="map-container" id="mapContainer">
            <svg id="mapSvg" viewBox="{min_x-50} {min_y-50} {width} {height}" preserveAspectRatio="xMidYMid meet">
                <!-- Grid/Background could go here -->
                {''.join(svg_elements)}
            </svg>
        </div>
        
        <div class="tables-wrapper">
            <div class="state-table-container hidden" id="stateTableContainer">
                <table id="stateTable">
                    <thead>
                        <tr>
                            <th>Color</th>
                            <th>Name</th>
                            <th>Capital</th>
                            <th>Type</th>
                            <th>Culture</th>
                            <th>Burgs</th>
                            <th>Area</th>
                            <th>Cells</th>
                            <th>Form</th>
                            <th>Fullname</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(state_rows)}
                    </tbody>
                </table>
            </div>

            <div class="table-container hidden" id="burgTableContainer">
                <table id="burgTable">
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, this)">Name</th>
                            <th onclick="sortTable(1, this)">Type</th>
                            <th onclick="sortTable(2, this)">State</th>
                            <th onclick="sortTable(3, this)">Quartiers</th>
                            <th onclick="sortTable({idx_pop}, this)">Pop</th>
                            <th onclick="sortTable({idx_food}, this)">Food</th>
                            <th onclick="sortTable({idx_gold}, this)">Gold</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <div id="tooltip" class="tooltip"></div>

    <script>
        const svg = document.getElementById('mapSvg');
        const tooltip = document.getElementById('tooltip');
        const mapContainer = document.getElementById('mapContainer');
        const table = document.getElementById('burgTable');
        let selectedId = null;

        /* Dropdown Logic */
        function toggleDropdown(id) {{
            document.getElementById(id).classList.toggle("show");
        }}

        // Close the dropdown if the user clicks outside of it
        window.onclick = function(event) {{
            if (!event.target.matches('.dropbtn')) {{
                var dropdowns = document.getElementsByClassName("dropdown-content");
                var i;
                for (i = 0; i < dropdowns.length; i++) {{
                    var openDropdown = dropdowns[i];
                    if (openDropdown.classList.contains('show')) {{
                        openDropdown.classList.remove('show');
                    }}
                }}
            }}
        }}

        function toggleTrades() {{
            const checkbox = document.getElementById('toggleTrades');
            const routes = document.querySelectorAll('.trade-route');
            routes.forEach(r => {{
                if (checkbox.checked) {{
                    r.classList.remove('hidden');
                }} else {{
                    r.classList.add('hidden');
                }}
            }});
        }}
        
        function toggleCapitals() {{
            const checkbox = document.getElementById('toggleCapitals');
            if (checkbox.checked) {{
                document.body.classList.add('show-capitals');
            }} else {{
                document.body.classList.remove('show-capitals');
            }}
        }}

        function toggleTable() {{
            const checkbox = document.getElementById('toggleTable');
            const container = document.getElementById('burgTableContainer');
            if (checkbox.checked) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function toggleStateTable() {{
            const checkbox = document.getElementById('toggleStateTable');
            const container = document.getElementById('stateTableContainer');
            if (checkbox.checked) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}
        
        function toggleAllTypes(source) {{
            const checkboxes = document.querySelectorAll('#typeCheckboxes input[type="checkbox"]');
            for(var i=0, n=checkboxes.length;i<n;i++) {{
                checkboxes[i].checked = source.checked;
            }}
            filterTable();
        }}

        function toggleAllStates(source) {{
            const checkboxes = document.querySelectorAll('#stateCheckboxes input[type="checkbox"]');
            for(var i=0, n=checkboxes.length;i<n;i++) {{
                checkboxes[i].checked = source.checked;
            }}
            filterTable();
        }}

        function filterTable() {{
            const searchInput = document.getElementById('searchInput');
            const filterText = searchInput.value.toLowerCase();
            
            // Get selected types
            const typeCheckboxes = document.querySelectorAll('#typeCheckboxes input[type="checkbox"]');
            const selectedTypes = [];
            
            typeCheckboxes.forEach(cb => {{
                if (cb.value !== 'all' && cb.checked) {{
                    selectedTypes.push(cb.value);
                }}
            }});

            // Get selected states
            const stateCheckboxes = document.querySelectorAll('#stateCheckboxes input[type="checkbox"]');
            const selectedStates = [];
            
            stateCheckboxes.forEach(cb => {{
                if (cb.value !== 'all' && cb.checked) {{
                    selectedStates.push(cb.value);
                }}
            }});
            
            const rows = table.getElementsByTagName('tr');
            
            // Filter Table
            // Start from 1 to skip header
            for (let i = 1; i < rows.length; i++) {{
                const row = rows[i];
                const nameCell = row.getElementsByTagName('td')[0];
                const typeCell = row.getElementsByTagName('td')[1];
                const stateCell = row.getElementsByTagName('td')[2];
                const burgId = row.getAttribute('data-id');
                
                if (nameCell && typeCell && stateCell) {{
                    const nameText = nameCell.textContent || nameCell.innerText;
                    const typeText = typeCell.textContent || typeCell.innerText;
                    const stateText = stateCell.textContent || stateCell.innerText;
                    const isCapitalRow = row.classList.contains('capital-row');
                    
                    const matchesName = nameText.toLowerCase().indexOf(filterText) > -1;
                    
                    // Check if type matches ANY of the selected types
                    let matchesType = false;
                    if (selectedTypes.includes(typeText)) {{
                        matchesType = true;
                    }}
                    if (selectedTypes.includes('Capital') && isCapitalRow) {{
                        matchesType = true;
                    }}

                    // Check if state matches ANY of the selected states
                    let matchesState = false;
                    if (selectedStates.includes(stateText)) {{
                        matchesState = true;
                    }}
                    
                    const isVisible = matchesName && matchesType && matchesState;
                    
                    if (isVisible) {{
                        row.style.display = "";
                    }} else {{
                        row.style.display = "none";
                    }}
                    
                    // Filter Map Dot corresponding to this row
                    const dot = document.querySelector(`.burg-dot[data-id="${{burgId}}"]`);
                    if (dot) {{
                        if (isVisible) {{
                            dot.classList.remove('hidden');
                        }} else {{
                            dot.classList.add('hidden');
                        }}
                    }}
                }}
            }}
        }}

        // Map Interactions
        svg.addEventListener('click', (e) => {{
            if (e.target.classList.contains('burg-dot')) {{
                const id = e.target.getAttribute('data-id');
                selectBurg(id);
            }} else {{
                // Deselect if clicking empty space
                // selectBurg(null);
            }}
        }});

        svg.addEventListener('mousemove', (e) => {{
            if (e.target.classList.contains('burg-dot')) {{
                const name = e.target.getAttribute('data-name');
                const pop = parseInt(e.target.getAttribute('data-pop')).toLocaleString();
                const type = e.target.getAttribute('data-type');
                const state = e.target.getAttribute('data-state');
                const gold = e.target.getAttribute('data-gold');
                const food = e.target.getAttribute('data-food');
                const quartiers = e.target.getAttribute('data-quartiers');
                const isCapital = e.target.classList.contains('capital');
                
                let displayName = isCapital ? `★ ${{name}}` : name;
                
                let tooltipContent = `<strong>${{displayName}}</strong><br>State: ${{state}}<br>Type: ${{type}}<br>Pop: ${{pop}}<br>Food: ${{food}}<br>Gold: ${{gold}}`;
                if (quartiers) {{
                    tooltipContent += `<hr style="margin: 5px 0; border: 0; border-top: 1px solid rgba(255,255,255,0.3);">${{quartiers}}`;
                }}
                
                tooltip.innerHTML = tooltipContent;
                tooltip.style.display = 'block';
                
                // Smart positioning to keep within viewport
                let top = e.clientY + 10;
                let left = e.clientX + 10;
                
                // Check if tooltip goes off bottom
                if (top + 100 > window.innerHeight) {{
                    top = e.clientY - 100; // Move above cursor
                }}
                
                tooltip.style.left = left + 'px';
                tooltip.style.top = top + 'px';
            }} else {{
                tooltip.style.display = 'none';
            }}
        }});
        
        // Table Tooltip Interactions
        table.addEventListener('mousemove', (e) => {{
            if (e.target.classList.contains('quartier-cell')) {{
                const details = e.target.getAttribute('data-details');
                if (details) {{
                    tooltip.innerHTML = details;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (e.clientX + 10) + 'px';
                    tooltip.style.top = (e.clientY + 10) + 'px';
                }}
            }} else {{
                // Only hide if not over map dot (which is separate)
                // But we are in table container, so map tooltip is not active
                tooltip.style.display = 'none';
            }}
        }});
        
        table.addEventListener('mouseleave', () => {{
            tooltip.style.display = 'none';
        }});

        // Pan and Zoom (Basic)
        let isPanning = false;
        let startX, startY;
        let viewBox = svg.getAttribute('viewBox').split(' ').map(parseFloat);
        
        mapContainer.addEventListener('mousedown', (e) => {{
            if (e.target === svg || e.target.tagName === 'circle' || e.target.tagName === 'line') {{
                isPanning = true;
                startX = e.clientX;
                startY = e.clientY;
                mapContainer.style.cursor = 'grabbing';
            }}
        }});
        
        mapContainer.addEventListener('mousemove', (e) => {{
            if (!isPanning) return;
            e.preventDefault();
            const dx = (e.clientX - startX) * (viewBox[2] / mapContainer.clientWidth);
            const dy = (e.clientY - startY) * (viewBox[3] / mapContainer.clientHeight);
            
            viewBox[0] -= dx;
            viewBox[1] -= dy;
            svg.setAttribute('viewBox', viewBox.join(' '));
            
            startX = e.clientX;
            startY = e.clientY;
        }});
        
        mapContainer.addEventListener('mouseup', () => {{
            isPanning = false;
            mapContainer.style.cursor = 'default';
        }});
        
        mapContainer.addEventListener('mouseleave', () => {{
            isPanning = false;
            mapContainer.style.cursor = 'default';
        }});
        
        mapContainer.addEventListener('wheel', (e) => {{
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
        }});

        function selectBurg(id) {{
            // Remove previous selection
            if (selectedId) {{
                const prevRow = document.querySelector(`tr[data-id="${{selectedId}}"]`);
                const prevDot = document.querySelector(`.burg-dot[data-id="${{selectedId}}"]`);
                if (prevRow) prevRow.classList.remove('selected');
                if (prevDot) prevDot.classList.remove('selected');
            }}
            
            selectedId = id;
            
            if (id) {{
                const row = document.querySelector(`tr[data-id="${{id}}"]`);
                const dot = document.querySelector(`.burg-dot[data-id="${{id}}"]`);
                
                if (row) {{
                    row.classList.add('selected');
                    row.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
                
                if (dot) {{
                    dot.classList.add('selected');
                    // Optional: Center map on dot?
                }}
            }}
        }}
        
        function highlightBurg(id) {{
            selectBurg(id);
        }}

        function sortTable(n, header) {{
            const table = document.getElementById("burgTable");
            let rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            switching = true;
            dir = "asc"; 
            
            // Reset other headers
            const headers = table.querySelectorAll('th');
            headers.forEach(h => {{
                if (h !== header) {{
                    h.classList.remove('sort-asc', 'sort-desc');
                }}
            }});
            
            // Toggle current header
            if (header.classList.contains('sort-asc')) {{
                dir = "desc";
                header.classList.remove('sort-asc');
                header.classList.add('sort-desc');
            }} else {{
                header.classList.remove('sort-desc');
                header.classList.add('sort-asc');
            }}

            // Optimization: Sort an array of rows instead of DOM manipulation
            const tbody = table.querySelector('tbody');
            const rowsArray = Array.from(tbody.rows);
            
            rowsArray.sort((a, b) => {{
                let x = a.getElementsByTagName("TD")[n];
                let y = b.getElementsByTagName("TD")[n];
                
                let xContent = x.textContent || x.innerText;
                let yContent = y.textContent || y.innerText;
                
                // Handle "★ " prefix
                xContent = xContent.replace("★ ", "");
                yContent = yContent.replace("★ ", "");
                
                // Check if numeric (remove commas)
                let xNum = parseFloat(xContent.replace(/,/g, ""));
                let yNum = parseFloat(yContent.replace(/,/g, ""));
                
                if (!isNaN(xNum) && !isNaN(yNum)) {{
                    return dir === "asc" ? xNum - yNum : yNum - xNum;
                }} else {{
                    return dir === "asc" ? xContent.localeCompare(yContent) : yContent.localeCompare(xContent);
                }}
            }});
            
            // Re-append sorted rows
            const fragment = document.createDocumentFragment();
            rowsArray.forEach(row => fragment.appendChild(row));
            tbody.appendChild(fragment);
        }}
    </script>
</body>
</html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Map generated at {output_file}")
