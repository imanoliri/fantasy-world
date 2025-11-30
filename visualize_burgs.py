import json
import math

BURGS_FILE = 'data/burgs.json'
OUTPUT_FILE = 'interactive_map.html'

def load_burgs():
    with open(BURGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_html(burgs):
    # Determine map bounds
    xs = [b['x'] for b in burgs]
    ys = [b['y'] for b in burgs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x + 100
    height = max_y - min_y + 100
    
    # Generate SVG circles
    svg_elements = []
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
    for b in burgs:
        citizen_types.update(b.get('quartiers', {}).keys())
    sorted_citizen_types = sorted(list(citizen_types))

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
        
        # SVG Element (Removed <title> to avoid double tooltip)
        svg_elements.append(f"""
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"
                    class="burg-dot{capital_class}" data-id="{b['id']}" data-name="{b['name']}" 
                    data-pop="{b['population']}" data-type="{b.get('type', 'Unknown')}" 
                    data-gold="{net_gold:.2f}" data-food="{net_food:.2f}">
            </circle>
        """)
        
        name_display = f"★ {b['name']}" if is_capital else b['name']
        row_class = "capital-row" if is_capital else ""

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
        
        table_rows.append(f"""
            <tr data-id="{b['id']}" class="{row_class}" onclick="highlightBurg({b['id']})">
                <td>{name_display}</td>
                <td>{b.get('type', 'Unknown')}</td>
                <td class="quartier-cell" data-details="{quartier_details}">{quartiers}</td>
                <td>{b['population']:,}</td>
                <td class="{ 'pos' if net_food > 0 else 'neg' }">{net_food:.2f}</td>
                <td class="{ 'pos' if net_gold > 0 else 'neg' }">{net_gold:.2f}</td>
            </tr>
        """)

    # Update sort indices (fixed again)
    idx_pop = 3
    idx_food = 4
    idx_gold = 5

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Burg Map</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
        header {{ background: #2c3e50; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 10; }}
        h1 {{ margin: 0; font-size: 1.2rem; }}
        
        .container {{ display: flex; flex: 1; overflow: hidden; }}
        
        /* Map Section */
        .map-container {{ flex: 2; background: #ecf0f1; position: relative; overflow: hidden; border-right: 1px solid #bdc3c7; }}
        svg {{ width: 100%; height: 100%; cursor: grab; }}
        svg:active {{ cursor: grabbing; }}
        
        .burg-dot {{ transition: r 0.2s, stroke-width 0.2s; cursor: pointer; }}
        .burg-dot:hover {{ stroke: #333; stroke-width: 3px; }}
        .burg-dot.selected {{ stroke: #000; stroke-width: 4px; r: 15px; animation: pulse 1s infinite; }}
        .burg-dot.capital {{ filter: drop-shadow(0 0 6px gold); }}
        
        @keyframes pulse {{
            0% {{ stroke-opacity: 1; }}
            50% {{ stroke-opacity: 0.5; }}
            100% {{ stroke-opacity: 1; }}
        }}

        /* Table Section */
        .table-container {{ flex: 1; overflow-y: auto; background: white; padding: 0; min-width: 300px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; position: sticky; top: 0; z-index: 1; cursor: pointer; }}
        th:hover {{ background: #e9ecef; }}
        tr:hover {{ background-color: #f1f1f1; cursor: pointer; }}
        tr.selected {{ background-color: #fff3cd; border-left: 5px solid #f1c40f; }}
        tr.capital-row {{ font-weight: bold; background-color: #fffbf0; }}
        
        .quartier-cell {{ cursor: help; text-decoration: underline dotted #aaa; }}
        
        .pos {{ color: #27ae60; font-weight: bold; }}
        .neg {{ color: #c0392b; font-weight: bold; }}
        
        /* Tooltip */
        .tooltip {{ position: absolute; background: rgba(0,0,0,0.8); color: white; padding: 5px 10px; border-radius: 4px; pointer-events: none; font-size: 0.8rem; display: none; z-index: 1000; }}
    </style>
</head>
<body>
    <header>
        <h1>Interactive Burg Map</h1>
        <div style="font-size: 0.9rem;">Total Burgs: {len(burgs)}</div>
    </header>
    
    <div class="container">
        <div class="map-container" id="mapContainer">
            <svg id="mapSvg" viewBox="{min_x-50} {min_y-50} {width} {height}" preserveAspectRatio="xMidYMid meet">
                <!-- Grid/Background could go here -->
                {''.join(svg_elements)}
            </svg>
        </div>
        
        <div class="table-container">
            <table id="burgTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Name</th>
                        <th onclick="sortTable(1)">Type</th>
                        <th onclick="sortTable(2)">Quartiers</th>
                        <th onclick="sortTable({idx_pop})">Pop</th>
                        <th onclick="sortTable({idx_food})">Food</th>
                        <th onclick="sortTable({idx_gold})">Gold</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>
    </div>
    <div id="tooltip" class="tooltip"></div>


    <script>
        const svg = document.getElementById('mapSvg');
        const tooltip = document.getElementById('tooltip');
        const mapContainer = document.getElementById('mapContainer');
        const table = document.getElementById('burgTable');
        let selectedId = null;

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
                const gold = e.target.getAttribute('data-gold');
                const food = e.target.getAttribute('data-food');
                
                tooltip.innerHTML = `<strong>${{name}}</strong><br>Type: ${{type}}<br>Pop: ${{pop}}<br>Food: ${{food}}<br>Gold: ${{gold}}`;
                tooltip.style.display = 'block';
                tooltip.style.left = (e.pageX + 10) + 'px';
                tooltip.style.top = (e.pageY + 10) + 'px';
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
                    tooltip.style.left = (e.pageX + 10) + 'px';
                    tooltip.style.top = (e.pageY + 10) + 'px';
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
            if (e.target === svg || e.target.tagName === 'circle') {{
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
        
        mapContainer.addEventListener('mouseup', () => {{ isPanning = false; mapContainer.style.cursor = 'default'; }});
        mapContainer.addEventListener('mouseleave', () => {{ isPanning = false; mapContainer.style.cursor = 'default'; }});
        
        mapContainer.addEventListener('wheel', (e) => {{
            e.preventDefault();
            const scale = e.deltaY > 0 ? 1.1 : 0.9;
            viewBox[2] *= scale;
            viewBox[3] *= scale;
            svg.setAttribute('viewBox', viewBox.join(' '));
        }});

        // Selection Logic
        function selectBurg(id) {{
            // Clear previous
            document.querySelectorAll('.selected').forEach(el => el.classList.remove('selected'));
            
            if (!id) return;
            
            // Highlight Map
            const dot = document.querySelector(`.burg-dot[data-id="${{id}}"]`);
            if (dot) dot.classList.add('selected');
            
            // Highlight Table
            const row = document.querySelector(`tr[data-id="${{id}}"]`);
            if (row) {{
                row.classList.add('selected');
                row.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            }}
            
            selectedId = id;
        }}
        
        function highlightBurg(id) {{
            selectBurg(id);
        }}

        // Table Sorting
        function sortTable(n) {{
            var table, rows, switching, i, x, y, shouldSwitch, dir, switchcount = 0;
            table = document.getElementById("burgTable");
            switching = true;
            dir = "asc";
            while (switching) {{
                switching = false;
                rows = table.rows;
                for (i = 1; i < (rows.length - 1); i++) {{
                    shouldSwitch = false;
                    x = rows[i].getElementsByTagName("TD")[n];
                    y = rows[i + 1].getElementsByTagName("TD")[n];
                    let xVal = x.innerHTML.replace(/,/g, '');
                    let yVal = y.innerHTML.replace(/,/g, '');
                    
                    if (!isNaN(parseFloat(xVal))) {{ xVal = parseFloat(xVal); yVal = parseFloat(yVal); }}
                    else {{ xVal = xVal.toLowerCase(); yVal = yVal.toLowerCase(); }}
                    
                    if (dir == "asc") {{
                        if (xVal > yVal) {{ shouldSwitch = true; break; }}
                    }} else if (dir == "desc") {{
                        if (xVal < yVal) {{ shouldSwitch = true; break; }}
                    }}
                }}
                if (shouldSwitch) {{
                    rows[i].parentNode.insertBefore(rows[i + 1], rows[i]);
                    switching = true;
                    switchcount ++;
                }} else {{
                    if (switchcount == 0 && dir == "asc") {{
                        dir = "desc";
                        switching = true;
                    }}
                }}
            }}
        }}
    </script>
</body>
</html>"""
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"Map generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    burgs = load_burgs()
    generate_html(burgs)
