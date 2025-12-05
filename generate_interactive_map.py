import csv
import json
import math
import os

# TRADES_FILE = 'data/trade_routes.csv' # Removed dependency

def generate_map(burgs, output_file, trades_data=None, map_name="Interactive Map", states=None, cultures=None, map_data=None):
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
    
    # Identify receivers
    food_receivers = set()
    gold_receivers = set()
    if trades_data:
        for t in trades_data:
            to_id = str(t['To_ID'])
            if t['Commodity'] == 'Net_Food':
                food_receivers.add(to_id)
            elif t['Commodity'] == 'Net_Gold':
                gold_receivers.add(to_id)
    
    # Generate SVG Elements
    svg_elements = []
    
    # 0. Background Map (Polygons)
    background_group = ""
    diplomacy_matrix = []
    
    if map_data:
        print("Generating background map polygons...")
        cells = map_data.get('pack', {}).get('cells', [])
        vertices = map_data.get('pack', {}).get('vertices', [])
        biomes_data = map_data.get('biomesData', {})
        biome_colors_list = biomes_data.get('color', [])
        
        # Extract Diplomacy Matrix
        # states is a list of dicts. states[i] corresponds to state ID i.
        # We want a list of lists where matrix[i] is the diplomacy array for state i.
        if states:
            for s in states:
                diplomacy_matrix.append(s.get('diplomacy', []))
        
        # Create state color lookup
        state_colors = {}
        state_names = {}
        if states:
            for s in states:
                state_colors[s.get('i')] = s.get('color', '#cccccc')
                state_names[s.get('i')] = s.get('name', 'Neutral')
        
        paths = []
        
        # We need to reconstruct polygons from cell vertices
        # Azgaar's format: cells[i].v is list of vertex indices
        # vertices[j] is [x, y]
        
        # Check if cells is a list of objects or the packed array format
        # Based on the JSON viewed earlier, it's a list of objects with 'v' property
        
        for cell in cells:
            state_id = cell.get('state', 0)
            biome_id = cell.get('biome', 0)
            
            # Determine colors
            state_fill = state_colors.get(state_id, '#e0e0e0') # Default grey for neutral
            
            # Handle water for state view
            h = cell.get('h', 0)
            t = cell.get('t', 0)
            is_water = False
            if state_id == 0:
                if h < 20:
                    state_fill = "#a0c8f0" # Light blue for water
                    is_water = True
                else:
                    state_fill = "#e0e0e0" # Neutral land
            
            # Biome color
            if 0 <= biome_id < len(biome_colors_list):
                biome_fill = biome_colors_list[biome_id]
            else:
                biome_fill = "#cccccc" # Fallback
            
            vertex_indices = cell.get('v', [])
            if not vertex_indices: continue
            
            # Build path data
            points = []
            for v_idx in vertex_indices:
                if v_idx < len(vertices):
                    vertex = vertices[v_idx]
                    if isinstance(vertex, dict) and 'p' in vertex:
                        vx, vy = vertex['p']
                    elif isinstance(vertex, (list, tuple)) and len(vertex) >= 2:
                        vx, vy = vertex[0], vertex[1]
                    else:
                        continue
                        
                    points.append(f"{vx},{vy}")
            
            if points:
                d = "M" + " L".join(points) + " Z"
                # Default to biome fill
                # Add data-state-id and onclick handler
                water_attr = 'data-is-water="true"' if is_water else ''
                
                # Get names
                biome_name = "Unknown"
                if biomes_data and 'name' in biomes_data and 0 <= biome_id < len(biomes_data['name']):
                    biome_name = biomes_data['name'][biome_id]
                
                state_name = state_names.get(state_id, 'Neutral')
                if state_id == 0: state_name = "Neutral"
                
                paths.append(f'<path d="{d}" fill="{biome_fill}" stroke="none" data-state-color="{state_fill}" data-biome-color="{biome_fill}" data-state-id="{state_id}" data-height="{h}" data-temp="{t}" data-biome="{biome_name}" data-state="{state_name}" {water_attr} onclick="selectState({state_id})" />')
        
        background_group = f'<g id="mapBackground" class="map-background">{"".join(paths)}</g>'
        svg_elements.append(background_group)

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
                stroke_color = '#e74c3c' if commodity == 'Net_Gold' else '#27ae60' # Gold (Red/Orange) vs Food (Green)
                
                # Add specific class for commodity
                route_class = "trade-route-gold" if commodity == 'Net_Gold' else "trade-route-food"
                
                svg_elements.append(f"""
                    <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" 
                          stroke="{stroke_color}" stroke-width="1" stroke-opacity="0.6"
                          class="trade-route {route_class}" />
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
    
    # Create lookups for names
    burg_name_lookup = {b['id']: b['name'] for b in burgs}
    culture_name_lookup = {}
    if cultures:
        for c in cultures:
            culture_name_lookup[c['i']] = c['name']

    for s in sorted_states:
        s_name = s.get('name', 'Unknown')
        
        # Prepare Tooltip Info
        capital_id = s.get('capital', 0)
        capital_name = burg_name_lookup.get(capital_id, 'Unknown') if capital_id else 'None'
        type_ = s.get('type', 'Unknown')
        culture_id = s.get('culture', 0)
        culture_name = culture_name_lookup.get(culture_id, 'Unknown')
        burgs_count = s.get('burgs', 0)
        area = s.get('area', 0)
        pop = s.get('urban', 0) # Using urban population as proxy if total not available, or just omit
        
        # Format tooltip content (using single quotes for JS string, so escape them if needed)
        # We'll use a data attribute to store the HTML content
        tooltip_info = f"<strong>{s.get('fullName', s_name)}</strong><br>"
        tooltip_info += f"Capital: {capital_name}<br>"
        tooltip_info += f"Type: {type_}<br>"
        tooltip_info += f"Culture: {culture_name}<br>"
        tooltip_info += f"Burgs: {burgs_count}<br>"
        tooltip_info += f"Area: {area:,}"
        
        state_checkboxes += f'<label onmouseover="showStateTooltip(event, \'{tooltip_info}\')" onmouseout="hideTooltip()"><input type="checkbox" value="{s_name}" checked onchange="filterTable()"> {s_name}</label>'
    state_checkboxes += '</div>'

    for b in burgs:
        # Map Logic
        cx = b['x']
        cy = b['y']
        
        # Radius based on population (sqrt scale)
        r = math.sqrt(b['population']) / 15
        if r < 3: r = 3
        if r > 12: r = 12
        
        color = type_colors.get(b.get('type'), '#95a5a6')
        
        net_gold = b.get('net_production_burg', {}).get('Net_Gold', 0)
        
        # Trade Receiver Logic for Classes and Extra Rings
        is_food_receiver = str(b['id']) in food_receivers
        is_gold_receiver = str(b['id']) in gold_receivers
        
        # We will control stroke color via CSS classes on the burg-dot
        # Default stroke is white (via CSS or attribute if not overridden)
        stroke = '#ffffff' 
        dot_classes = []
        extra_ring = ""
        
        if is_food_receiver and is_gold_receiver:
            # Both: Main dot is Green (Food), Extra ring is Orange (Gold)
            dot_classes.append("food-receiver")
            extra_ring = f'<circle cx="{cx}" cy="{cy}" r="{r + 3}" fill="none" stroke="#e74c3c" stroke-width="2" class="burg-ring-gold" pointer-events="none" />'
        elif is_food_receiver:
            # Food Only: Main dot is Green
            dot_classes.append("food-receiver")
        elif is_gold_receiver:
            # Gold Only: Main dot is Orange
            dot_classes.append("gold-receiver")
            
        dot_class_str = " " + " ".join(dot_classes) if dot_classes else ""
            
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
        # Append extra ring if it exists
        if extra_ring:
            svg_elements.append(extra_ring)
            
        svg_elements.append(f"""
            <circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" stroke="{stroke}" stroke-width="{stroke_width}"
                    class="burg-dot{capital_class}{dot_class_str}" data-id="{b['id']}" data-name="{b['name']}" 
                    data-pop="{b['population']}" data-type="{b.get('type', 'Unknown')}" 
                    data-state="{b.get('state_name', 'Unknown')}"
                    data-gold="{net_gold:.2f}" data-food="{net_food:.2f}"
                    data-quartiers="{quartier_details}">
            </circle>
        """)
        
        name_display = f"★ {b['name']}" if is_capital else b['name']
        row_class = "capital-row" if is_capital else ""
        
        table_rows.append(f"""
            <tr data-id="{b['id']}" data-original-index="{len(table_rows)}" class="{row_class}" onclick="highlightBurg({b['id']})">
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
                <tr data-original-index="{len(state_rows)}" onclick="highlightState('{name}', '{color}')">
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

    # 4. Trade Route Rows
    food_rows = []
    gold_rows = []
    if trades_data:
        for i, t in enumerate(trades_data):
            from_id = str(t['From_ID'])
            to_id = str(t['To_ID'])
            amount = t['Amount']
            commodity = t['Commodity']
            
            from_name = burg_name_lookup.get(int(from_id), 'Unknown')
            to_name = burg_name_lookup.get(int(to_id), 'Unknown')
            
            row_html = f"""
                <tr onclick="highlightTradeRoute({from_id}, {to_id})">
                    <td>{from_name}</td>
                    <td>{to_name}</td>
                    <td>{amount:.2f}</td>
                </tr>
            """
            
            if commodity == 'Net_Food':
                food_rows.append(row_html)
            elif commodity == 'Net_Gold':
                gold_rows.append(row_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interactive Map: {map_name}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }}
        header {{ background: #2c3e50; color: white; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 30; position: relative; }}
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
        .burg-dot.highlighted {{ stroke: #000; stroke-width: 4px; r: 15px; animation: pulse 1s infinite; }}
        .burg-dot.hidden {{ display: none; }}
        
        /* Only show capital glow when body has show-capitals class */
        body.show-capitals .burg-dot.capital {{ filter: drop-shadow(0 0 6px gold); }}
        
        .trade-route {{ pointer-events: none; transition: opacity 0.3s; opacity: 0; }}
        
        /* Visibility Toggles */
        body.show-food-trades .trade-route-food {{ opacity: 1; }}
        body.show-gold-trades .trade-route-gold {{ opacity: 1; }}
        
        /* Burg Rings Toggles */
        /* Default stroke is white (defined inline or default), overrides below */
        
        body.show-food-trades .burg-dot.food-receiver {{ stroke: #27ae60 !important; }}
        body.show-gold-trades .burg-dot.gold-receiver {{ stroke: #e74c3c !important; }}
        
        .burg-ring-gold {{ display: none; }}
        body.show-gold-trades .burg-ring-gold {{ display: block; }}
        
        @keyframes pulse {{
            0% {{ stroke-opacity: 1; }}
            50% {{ stroke-opacity: 0.5; }}
            100% {{ stroke-opacity: 1; }}
        }}

        /* Table Section */
        .tables-wrapper {{ position: absolute; right: 0; top: 0; bottom: 0; display: flex; z-index: 20; pointer-events: none; flex-direction: row-reverse; }}
        .table-container, .state-table-container, .trade-table-container {{ 
            width: 800px; 
            overflow-y: auto; 
            background: rgba(255, 255, 255, 0.95); 
            padding: 0; 
            box-shadow: -2px 0 5px rgba(0,0,0,0.1); 
            border-left: 1px solid #ddd; 
            pointer-events: auto; 
            transition: transform 0.3s ease-in-out;
        }}

        .trade-table-container {{ 
            width: 400px;
        }}
        
        /* Stacking Order: States > Burgs > Food > Gold (Left to Right) */
        /* Since we use flex-direction: row-reverse, the first element in DOM is rightmost. */
        /* We want Gold (Rightmost) -> Food -> Burgs -> States (Leftmost) */
        /* So DOM order should be: Gold, Food, Burgs, States */
        
        .hidden {{ display: none !important; }}
        
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; position: sticky; top: 0; z-index: 1; cursor: pointer; }}
        th:hover {{ background: #e9ecef; }}
        tr:hover {{ background-color: #f1f1f1; cursor: pointer; }}
        tr.selected {{ background-color: #fff3cd; border-left: 5px solid #f1c40f; }}
        tr.capital-row {{ font-weight: bold; background-color: #fffbf0; }}
        
        /* Sort Icons */
        th.sort-asc::after {{ content: ' ▲'; }}
        th.sort-desc::after {{ content: ' ▼'; }}
        
        caption {{ font-weight: bold; padding: 10px; font-size: 1.1rem; background: #f8f9fa; border-bottom: 1px solid #ddd; }}
        
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
        
        /* Toggle Buttons */
        .toggle-btn {{
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
            font-size: 0.9rem;
        }}
        .toggle-btn:hover {{
            background-color: #e0e0e0;
        }}
        .toggle-btn.active {{
            background-color: #3498db;
            color: white;
            border-color: #2980b9;
        }}
    </style>
</head>
<body class="show-capitals show-food-trades show-gold-trades">
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
            
            <button class="toggle-btn active" id="toggleFoodTrades" onclick="toggleFoodTrades()">Food Trade</button>
            <button class="toggle-btn active" id="toggleGoldTrades" onclick="toggleGoldTrades()">Gold Trade</button>
            <button class="toggle-btn active" id="toggleCapitals" onclick="toggleCapitals()">Highlight Capitals</button>
            <button class="toggle-btn" id="toggleStateTable" onclick="toggleStateTable()">States Table</button>
            <button class="toggle-btn" id="toggleTable" onclick="toggleTable()">Burgs Table</button>
            <button class="toggle-btn" id="toggleFoodTradeTable" onclick="toggleFoodTradeTable()">Food Trade Table</button>
            <button class="toggle-btn" id="toggleGoldTradeTable" onclick="toggleGoldTradeTable()">Gold Trade Table</button>
            <button class="toggle-btn active" id="toggleMap" onclick="toggleMap()">Show Map</button>
            <button class="toggle-btn" id="toggleMapMode" onclick="toggleMapMode()">Mode: Biome</button>
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
            <!-- Order in DOM: Gold, Food, Burgs, States (because of row-reverse) -->
            
            <div class="trade-table-container hidden" id="goldTradeTableContainer">
                <table id="goldTradeTable">
                    <caption>Gold Trade Routes</caption>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, this, 'goldTradeTable')">From</th>
                            <th onclick="sortTable(1, this, 'goldTradeTable')">To</th>
                            <th onclick="sortTable(2, this, 'goldTradeTable')">Gold</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(gold_rows)}
                    </tbody>
                </table>
            </div>

            <div class="trade-table-container hidden" id="foodTradeTableContainer">
                <table id="foodTradeTable">
                    <caption>Food Trade Routes</caption>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, this, 'foodTradeTable')">From</th>
                            <th onclick="sortTable(1, this, 'foodTradeTable')">To</th>
                            <th onclick="sortTable(2, this, 'foodTradeTable')">Food</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(food_rows)}
                    </tbody>
                </table>
            </div>

            <div class="table-container hidden" id="burgTableContainer">
                <table id="burgTable">
                    <caption>Burgs</caption>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, this, 'burgTable')">Name</th>
                            <th onclick="sortTable(1, this, 'burgTable')">Type</th>
                            <th onclick="sortTable(2, this, 'burgTable')">State</th>
                            <th onclick="sortTable(3, this, 'burgTable')">Quartiers</th>
                            <th onclick="sortTable({idx_pop}, this, 'burgTable')">Pop</th>
                            <th onclick="sortTable({idx_food}, this, 'burgTable')">Food</th>
                            <th onclick="sortTable({idx_gold}, this, 'burgTable')">Gold</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>

            <div class="state-table-container hidden" id="stateTableContainer">
                <table id="stateTable">
                    <caption>States</caption>
                    <thead>
                        <tr>
                            <th onclick="sortTable(0, this, 'stateTable')">Color</th>
                            <th onclick="sortTable(1, this, 'stateTable')">Name</th>
                            <th onclick="sortTable(2, this, 'stateTable')">Capital</th>
                            <th onclick="sortTable(3, this, 'stateTable')">Type</th>
                            <th onclick="sortTable(4, this, 'stateTable')">Culture</th>
                            <th onclick="sortTable(5, this, 'stateTable')">Burgs</th>
                            <th onclick="sortTable(6, this, 'stateTable')">Area</th>
                            <th onclick="sortTable(7, this, 'stateTable')">Cells</th>
                            <th onclick="sortTable(8, this, 'stateTable')">Form</th>
                            <th onclick="sortTable(9, this, 'stateTable')">Fullname</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(state_rows)}
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
        let highlightedIds = [];

        /* Dropdown Logic */
        function toggleDropdown(id) {{
            document.getElementById(id).classList.toggle("show");
        }}

        function showStateTooltip(e, content) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.innerHTML = content;
            tooltip.style.display = 'block';
            
            // Position near the cursor
            let left = e.clientX + 15;
            let top = e.clientY + 15;
            
            // Adjust if going off screen
            if (left + 220 > window.innerWidth) {{
                left = e.clientX - 230;
            }}
            
            if (top + 150 > window.innerHeight) {{
                top = e.clientY - 160;
            }}
            
            tooltip.style.left = left + 'px';
            tooltip.style.top = top + 'px';
        }}

        function hideTooltip() {{
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'none';
        }}

        function toggleFoodTrades() {{
            const btn = document.getElementById('toggleFoodTrades');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                document.body.classList.add('show-food-trades');
            }} else {{
                document.body.classList.remove('show-food-trades');
            }}
        }}

        function toggleGoldTrades() {{
            const btn = document.getElementById('toggleGoldTrades');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                document.body.classList.add('show-gold-trades');
            }} else {{
                document.body.classList.remove('show-gold-trades');
            }}
        }}
        
        function toggleCapitals() {{
            const btn = document.getElementById('toggleCapitals');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                document.body.classList.add('show-capitals');
            }} else {{
                document.body.classList.remove('show-capitals');
            }}
        }}

        function toggleTable() {{
            const btn = document.getElementById('toggleTable');
            const container = document.getElementById('burgTableContainer');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function toggleStateTable() {{
            const btn = document.getElementById('toggleStateTable');
            const container = document.getElementById('stateTableContainer');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function toggleFoodTradeTable() {{
            const btn = document.getElementById('toggleFoodTradeTable');
            const container = document.getElementById('foodTradeTableContainer');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        const diplomacyMatrix = {json.dumps(diplomacy_matrix)};
        const stateNameIdMap = {json.dumps({s.get('name', 'Unknown'): s.get('i', 0) for s in states} if states else {})};
        const relationColors = {{
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
        }};

        function toggleGoldTradeTable() {{
            const btn = document.getElementById('toggleGoldTradeTable');
            const container = document.getElementById('goldTradeTableContainer');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                container.classList.remove('hidden');
            }} else {{
                container.classList.add('hidden');
            }}
            window.dispatchEvent(new Event('resize'));
        }}

        function toggleMap() {{
            const btn = document.getElementById('toggleMap');
            const mapGroup = document.getElementById('mapBackground');
            btn.classList.toggle('active');
            if (btn.classList.contains('active')) {{
                mapGroup.style.display = 'block';
            }} else {{
                mapGroup.style.display = 'none';
            }}
        }}

        function toggleMapMode() {{
            const btn = document.getElementById('toggleMapMode');
            const paths = document.querySelectorAll('#mapBackground path');
            
            // Use data attribute for state tracking
            const currentMode = btn.getAttribute('data-mode') || 'biome';
            
            if (currentMode === 'biome') {{
                // Switch to State
                btn.innerText = 'Mode: State';
                btn.setAttribute('data-mode', 'state');
                paths.forEach(p => {{
                    p.setAttribute('fill', p.getAttribute('data-state-color'));
                }});
            }} else if (currentMode === 'state') {{
                // Switch to Heightmap
                btn.innerText = 'Mode: Heightmap';
                btn.setAttribute('data-mode', 'heightmap');
                paths.forEach(p => {{
                    const h = parseInt(p.getAttribute('data-height'));
                    p.setAttribute('fill', getColorForHeight(h));
                }});
            }} else if (currentMode === 'heightmap') {{
                // Switch to Temperature
                btn.innerText = 'Mode: Temperature';
                btn.setAttribute('data-mode', 'temperature');
                paths.forEach(p => {{
                    const t = parseInt(p.getAttribute('data-temp'));
                    p.setAttribute('fill', getColorForTemp(t));
                }});
            }} else {{
                // Switch to Biome
                btn.innerText = 'Mode: Biome';
                btn.setAttribute('data-mode', 'biome');
                paths.forEach(p => {{
                    p.setAttribute('fill', p.getAttribute('data-biome-color'));
                }});
            }}
        }}

        function getColorForHeight(h) {{
            // Azgaar height range: 0-100 (usually)
            // Water: < 20
            // Land: >= 20
            
            if (h < 20) {{
                // Water: Uniform Deep Blue
                return "#000080";
            }} else {{
                // Land gradient: Green -> Yellow -> Brown -> White
                if (h < 40) return "#228B22"; // Forest Green (Lowlands)
                if (h < 60) return "#9ACD32"; // Yellow Green (Hills)
                if (h < 80) return "#CD853F"; // Peru (Mountains)
                return "#FFFFFF"; // White (Peaks)
            }}
        }}

        function getColorForTemp(t) {{
            // Range: approx -30 to 50 (Celsius)
            // Hot (> 30): Red
            // Warm (20-30): Orange
            // Temperate (10-20): Yellow/Green
            // Cool (0-10): Cyan
            // Cold (-10 to 0): Blue
            // Freezing (< -10): Purple
            
            if (t < -20) return "#4B0082"; // Indigo (Deep Freeze)
            if (t < -10) return "#800080"; // Purple (Freezing)
            if (t < 0) return "#0000FF"; // Blue (Cold)
            if (t < 10) return "#00BFFF"; // Deep Sky Blue (Cool)
            if (t < 20) return "#ADFF2F"; // Green Yellow (Temperate)
            if (t < 30) return "#FFD700"; // Gold (Warm)
            if (t < 40) return "#FF8C00"; // Dark Orange (Hot)
            return "#FF0000"; // Red (Scorching)
        }}

        function selectState(stateId) {{
            const btn = document.getElementById('toggleMapMode');
            const currentMode = btn.getAttribute('data-mode');
            
            if (currentMode === 'state') {{
                updateDiplomacyColors(stateId);
            }}
        }}

        function updateDiplomacyColors(stateIdentifier) {{
            let stateId = null;
            
            // Try to find state ID
            if (typeof stateIdentifier === 'number') {{
                stateId = stateIdentifier;
            }} else if (typeof stateIdentifier === 'string') {{
                if (stateNameIdMap.hasOwnProperty(stateIdentifier)) {{
                    stateId = stateNameIdMap[stateIdentifier];
                }}
            }}
            
            // FIX: Treat selecting "Neutral" (0) as deselecting
            if (stateId === 0) stateId = null;
            
            const paths = document.querySelectorAll('#mapBackground path');
            
            if (stateId !== null && diplomacyMatrix[stateId]) {{
                const relations = diplomacyMatrix[stateId];
                
                paths.forEach(p => {{
                    const isWater = p.hasAttribute('data-is-water');
                    if (isWater) {{
                        p.setAttribute('fill', '#333333'); // Dark Gray for water
                    }} else {{
                        const pStateId = parseInt(p.getAttribute('data-state-id'));
                        
                        // FIX: Explicitly handle Neutrals (ID 0)
                        if (pStateId === 0 && stateId !== 0) {{
                             p.setAttribute('fill', '#ffffff'); // White for Neutrals
                        }} else if (!isNaN(pStateId) && pStateId < relations.length) {{
                            const relation = relations[pStateId];
                            // Highlight self differently?
                            let color = relationColors[relation] || relationColors['Unknown'];
                            if (pStateId === stateId) color = relationColors['x'];
                            
                            p.setAttribute('fill', color);
                        }}
                    }}
                }});
            }} else {{
                // Reset to State Colors if no state selected
                paths.forEach(p => {{
                    const isWater = p.hasAttribute('data-is-water');
                    if (isWater) {{
                        p.setAttribute('fill', '#333333'); // Dark Gray
                    }} else {{
                        // Revert to state color
                        p.setAttribute('fill', p.getAttribute('data-state-color'));
                    }}
                }});
            }}
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

            // Filter State Table
            const stateTable = document.getElementById('stateTable');
            if (stateTable) {{
                const stateRows = stateTable.getElementsByTagName('tr');
                // Start from 1 to skip header
                for (let i = 1; i < stateRows.length; i++) {{
                    const row = stateRows[i];
                    const nameCell = row.getElementsByTagName('td')[1]; // Name is 2nd column
                    
                    if (nameCell) {{
                        const stateName = nameCell.textContent || nameCell.innerText;
                        
                        // Check if state matches ANY of the selected states
                        let matchesState = false;
                        if (selectedStates.includes(stateName)) {{
                            matchesState = true;
                        }}
                        
                        // Check search text against state name
                        const matchesSearch = stateName.toLowerCase().indexOf(filterText) > -1;
                        
                        if (matchesState && matchesSearch) {{
                            row.style.display = "";
                        }} else {{
                            row.style.display = "none";
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
            }} else if (e.target.tagName === 'path') {{
                const btn = document.getElementById('toggleMapMode');
                const mode = btn.getAttribute('data-mode') || 'biome';
                
                let content = '';
                if (mode === 'biome') {{
                    const biome = e.target.getAttribute('data-biome');
                    if (biome) content = `<strong>Biome:</strong> ${{biome}}`;
                }} else if (mode === 'state') {{
                    const state = e.target.getAttribute('data-state');
                    if (state) content = `<strong>State:</strong> ${{state}}`;
                }} else if (mode === 'heightmap') {{
                    const h = e.target.getAttribute('data-height');
                    if (h) content = `<strong>Height:</strong> ${{h}}`;
                }} else if (mode === 'temperature') {{
                    const t = e.target.getAttribute('data-temp');
                    if (t) content = `<strong>Temp:</strong> ${{t}}°C`;
                }}
                
                if (content) {{
                    tooltip.innerHTML = content;
                    tooltip.style.display = 'block';
                    tooltip.style.left = (e.clientX + 15) + 'px';
                    tooltip.style.top = (e.clientY + 15) + 'px';
                }} else {{
                    tooltip.style.display = 'none';
                }}
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
            if (e.target === svg || e.target.tagName === 'circle' || e.target.tagName === 'line' || e.target.tagName === 'path') {{
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
            
            // Clear any trade route highlights
            clearHighlights();
            
            // Clear previous table highlights (State and Trade)
            document.querySelectorAll('.related-highlight').forEach(el => el.classList.remove('selected'));

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
                    
                    // Highlight Related State
                    const stateName = dot.getAttribute('data-state');
                    if (stateName) {{
                        // Update Diplomacy Map if active
                        const btn = document.getElementById('toggleMapMode');
                        if (btn && btn.getAttribute('data-mode') === 'state') {{
                            updateDiplomacyColors(stateName);
                        }}

                        const stateTable = document.getElementById('stateTable');
                        const stateRows = stateTable.getElementsByTagName('tr');
                        for (let i = 1; i < stateRows.length; i++) {{
                            const sRow = stateRows[i];
                            const nameCell = sRow.getElementsByTagName('td')[1]; // Name is 2nd column
                            if (nameCell && (nameCell.textContent || nameCell.innerText) === stateName) {{
                                sRow.classList.add('selected');
                                sRow.classList.add('related-highlight'); // Marker class to clear later
                                sRow.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
                                break; 
                            }}
                        }}
                    }}

                    // Highlight Related Trade Routes
                    const burgName = dot.getAttribute('data-name');
                    if (burgName) {{
                        ['foodTradeTable', 'goldTradeTable'].forEach(tableId => {{
                            const tTable = document.getElementById(tableId);
                            if (tTable) {{
                                const tRows = tTable.getElementsByTagName('tr');
                                for (let i = 1; i < tRows.length; i++) {{
                                    const tRow = tRows[i];
                                    const fromCell = tRow.getElementsByTagName('td')[0];
                                    const toCell = tRow.getElementsByTagName('td')[1];
                                    
                                    const fromName = fromCell.textContent || fromCell.innerText;
                                    const toName = toCell.textContent || toCell.innerText;
                                    
                                    if (fromName === burgName || toName === burgName) {{
                                        tRow.classList.add('selected');
                                        tRow.classList.add('related-highlight');
                                    }}
                                }}
                            }}
                        }});
                    }}
                }}
            }}
        }}
        
        function highlightBurg(id) {{
            selectBurg(id);
        }}

        function clearHighlights() {{
            highlightedIds.forEach(id => {{
                const dot = document.querySelector(`.burg-dot[data-id="${{id}}"]`);
                if (dot) {{
                    dot.classList.remove('highlighted');
                    dot.style.fill = ''; // Reset color
                    dot.style.stroke = ''; // Reset stroke
                }}
            }});
            highlightedIds = [];
        }}

        function highlightState(stateName, color) {{
            clearHighlights();
            if (selectedId) selectBurg(null);

            const dots = document.querySelectorAll(`.burg-dot[data-state="${{stateName}}"]`);
            dots.forEach(dot => {{
                dot.classList.add('highlighted');
                dot.style.fill = color;
                dot.style.stroke = '#000'; // Make it pop
                highlightedIds.push(dot.getAttribute('data-id'));
            }});
        }}

        function highlightTradeRoute(fromId, toId) {{
            clearHighlights();
            if (selectedId) selectBurg(null); // Clear single selection

            [fromId, toId].forEach(id => {{
                const dot = document.querySelector(`.burg-dot[data-id="${{id}}"]`);
                if (dot) {{
                    dot.classList.add('highlighted');
                    highlightedIds.push(id);
                }}
            }});
        }}

        function sortTable(n, header, tableId) {{
            const table = document.getElementById(tableId);
            let dir = "asc"; 
            
            // Reset other headers
            const headers = table.querySelectorAll('th');
            headers.forEach(h => {{
                if (h !== header) {{
                    h.classList.remove('sort-asc', 'sort-desc');
                }}
            }});
            
            // Determine sort direction (Tri-state: Asc -> Desc -> Original)
            if (header.classList.contains('sort-asc')) {{
                dir = "desc";
                header.classList.remove('sort-asc');
                header.classList.add('sort-desc');
            }} else if (header.classList.contains('sort-desc')) {{
                dir = "original";
                header.classList.remove('sort-desc');
            }} else {{
                dir = "asc";
                header.classList.add('sort-asc');
            }}

            // Optimization: Sort an array of rows instead of DOM manipulation
            const tbody = table.querySelector('tbody');
            const rowsArray = Array.from(tbody.rows);
            
            rowsArray.sort((a, b) => {{
                // If reverting to original order
                if (dir === "original") {{
                    let xIndex = parseInt(a.getAttribute('data-original-index'));
                    let yIndex = parseInt(b.getAttribute('data-original-index'));
                    return xIndex - yIndex;
                }}
                
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
