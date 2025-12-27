import csv
import json
import math
import os
from jinja2 import Environment, FileSystemLoader

def generate_map(burgs, output_file, trades_data=None, map_name="Interactive Map", states=None, cultures=None, map_data=None):
    print(f"Generating interactive map for {map_name} with {len(burgs)} burgs...")
    
    # helper for formatting numbers
    def fmt_num(n):
        return f"{n:,.0f}" # 1,000

    # Determine map bounds
    xs = [b['x'] for b in burgs]
    ys = [b['y'] for b in burgs]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    
    width = max_x - min_x + 100
    height = max_y - min_y + 100
    
    # Create a lookup for burg coordinates
    burg_coords = {str(b['id']): (b['x'], b['y']) for b in burgs}
    burg_name_lookup = {b['id']: b['name'] for b in burgs}

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
    
    # --- PREPARE DATA FOR TEMPLATE ---
    background_paths = []
    diplomacy_matrix = []
    state_name_id_map = {}
    
    # 1. Background Map (Polygons)
    if map_data:
        print("Generating background map polygons...")
        cells = map_data.get('pack', {}).get('cells', [])
        vertices = map_data.get('pack', {}).get('vertices', [])
        biomes_data = map_data.get('biomesData', {})
        biome_colors_list = biomes_data.get('color', [])
        
        # Extract Diplomacy Matrix
        if states:
            for s in states:
                diplomacy_matrix.append(s.get('diplomacy', []))
                state_name_id_map[s.get('name', 'Unknown')] = s.get('i', 0)
        
        # Create state color lookup
        state_colors = {}
        state_names = {}
        if states:
            for s in states:
                state_colors[s.get('i')] = s.get('color', '#cccccc')
                state_names[s.get('i')] = s.get('name', 'Neutral')
        
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
                
                # Get names
                biome_name = "Unknown"
                if biomes_data and 'name' in biomes_data and 0 <= biome_id < len(biomes_data['name']):
                    biome_name = biomes_data['name'][biome_id]
                
                state_name = state_names.get(state_id, 'Neutral')
                if state_id == 0: state_name = "Neutral"
                
                background_paths.append({
                    'cell_id': cell.get('i'),
                    'd': d,
                    'fill': biome_fill,
                    'state_fill': state_fill,
                    'biome_fill': biome_fill,
                    'state_id': state_id,
                    'h': h,
                    't': t,
                    'biome_name': biome_name,
                    'state_name': state_name,
                    'is_water': is_water
                })

    # 2. Trade Routes
    trade_routes = []
    food_rows = []
    gold_rows = []
    
    if trades_data:
        for t in trades_data:
            from_id = str(t['From_ID'])
            to_id = str(t['To_ID'])
            
            if from_id in burg_coords and to_id in burg_coords:
                x1, y1 = burg_coords[from_id]
                x2, y2 = burg_coords[to_id]
                
                commodity = t['Commodity']
                stroke_color = '#e74c3c' if commodity == 'Net_Gold' else '#27ae60'
                route_class = "trade-route-gold" if commodity == 'Net_Gold' else "trade-route-food"
                
                trade_routes.append({
                    'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                    'stroke_color': stroke_color,
                    'route_class': route_class
                })
                
                # Table Rows
                from_name = burg_name_lookup.get(int(from_id), 'Unknown')
                to_name = burg_name_lookup.get(int(to_id), 'Unknown')
                
                row_data = {
                    'from_id': from_id,
                    'to_id': to_id,
                    'from_name': from_name,
                    'to_name': to_name,
                    'amount': f"{t['Amount']:.2f}"
                }
                
                if commodity == 'Net_Food':
                    food_rows.append(row_data)
                elif commodity == 'Net_Gold':
                    gold_rows.append(row_data)

    # 3. Burgs
    burgs_data = []
    type_colors = {
        'Naval': '#3498db',    # Blue
        'Generic': '#95a5a6',  # Gray
        'Hunting': '#2ecc71',  # Green
        'Capital': '#e74c3c',  # Red
        'Mining': '#f1c40f'    # Yellow
    }
    
    citizen_types = set()
    burg_types_set = set()
    
    for b in burgs:
        citizen_types.update(b.get('quartiers', {}).keys())
        burg_types_set.add(b.get('type', 'Unknown'))
        
    sorted_citizen_types = sorted(list(citizen_types))
    sorted_burg_types = sorted(list(burg_types_set))
    
    for b in burgs:
        cx = b['x']
        cy = b['y']
        
        # Radius
        r = math.sqrt(b['population']) / 15
        if r < 3: r = 3
        if r > 12: r = 12
        
        color = type_colors.get(b.get('type'), '#95a5a6')
        net_gold = b.get('net_production_burg', {}).get('Net_Gold', 0)
        net_food = b.get('net_production_burg', {}).get('Net_Food', 0)
        
        # Receiver logic
        is_food_receiver = str(b['id']) in food_receivers
        is_gold_receiver = str(b['id']) in gold_receivers
        
        stroke = '#ffffff'
        dot_classes = []
        extra_ring = False
        
        if is_food_receiver and is_gold_receiver:
            dot_classes.append("food-receiver")
            extra_ring = True
        elif is_food_receiver:
            dot_classes.append("food-receiver")
        elif is_gold_receiver:
            dot_classes.append("gold-receiver")
            
        dot_class_str = " " + " ".join(dot_classes) if dot_classes else ""
        
        is_capital = b.get('capital') == 1
        capital_class = " capital" if is_capital else ""
        stroke_width = 3 if is_capital else 2
        
        # Tooltip details
        quartiers = b.get('nr_quartiers', 0)
        quartier_details = ""
        type_counts = []
        for ct in sorted_citizen_types:
            count = b.get('quartiers', {}).get(ct, 0)
            type_counts.append((ct, count))
        type_counts.sort(key=lambda x: x[1], reverse=True)
        
        for ct, count in type_counts:
            if count > 0:
                quartier_details += f"{ct}: {count}<br>"
                
        name_display = f"★ {b['name']}" if is_capital else b['name']
        row_class = "capital-row" if is_capital else ""
        
        burgs_data.append({
            'id': b['id'],
            'cell_id': b.get('cell'),
            'x': cx, 'y': cy, 'r': r,
            'color': color, 'stroke': stroke, 'stroke_width': stroke_width,
            'capital_class': capital_class,
            'dot_class_str': dot_class_str,
            'extra_ring': extra_ring,
            'name': b['name'],
            'population': b['population'],
            'population_fmt': fmt_num(b['population']),
            'type': b.get('type', 'Unknown'),
            'state_name': b.get('state_name', 'Unknown'),
            'net_gold': f"{net_gold:.2f}",
            'net_food': f"{net_food:.2f}",
            'net_gold_val': net_gold,
            'net_food_val': net_food,
            'quartier_details': quartier_details,
            'nr_quartiers': quartiers,
            'name_display': name_display,
            'row_class': row_class
        })

    # 4. States Data for Table
    states_data = []
    culture_name_lookup = {}
    if cultures:
        for c in cultures:
            culture_name_lookup[c['i']] = c['name']
            
    sorted_states = sorted(states, key=lambda x: x.get('name', '')) if states else []
    
    for s in sorted_states:
        s_name = s.get('name', 'Unknown')
        capital_id = s.get('capital', 0)
        capital_name = burg_name_lookup.get(capital_id, 'Unknown') if capital_id else 'None'
        culture_id = s.get('culture', 0)
        culture_name = culture_name_lookup.get(culture_id, 'Unknown')
        
        # Tooltip info
        tooltip_info = f"<strong>{s.get('fullName', s_name)}</strong><br>"
        tooltip_info += f"Capital: {capital_name}<br>"
        tooltip_info += f"Type: {s.get('type', 'Unknown')}<br>"
        tooltip_info += f"Culture: {culture_name}<br>"
        tooltip_info += f"Burgs: {s.get('burgs', 0)}<br>"
        tooltip_info += f"Area: {s.get('area', 0):,}"
        
        states_data.append({
            'color': s.get('color', '#cccccc'),
            'name': s_name,
            'safe_name': s_name.replace("'", "\\'"),
            'capital_name': capital_name,
            'type': s.get('type', 'Unknown'),
            'culture_name': culture_name,
            'burgs_count': s.get('burgs', 0),
            'area': f"{s.get('area', 0):,}",
            'cells': f"{s.get('cells', 0):,}",
            'form': s.get('form', 'Unknown'),
            'fullname': s.get('fullName', s_name),
            'tooltip_info': tooltip_info
        })

    # --- RENDER TEMPLATE ---
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template('templates/map_template.html')
    
    context = {
        'map_name': map_name,
        'min_x': min_x, 'min_y': min_y,
        'width': width, 'height': height,
        'total_burgs': len(burgs),
        'background_paths': background_paths,
        'trade_routes': trade_routes,
        'burgs_data': burgs_data,
        'states_data': states_data,
        'burg_types': sorted_burg_types,
        'food_rows': food_rows,
        'gold_rows': gold_rows,
        'gold_rows': gold_rows,
        'diplomacy_matrix': json.dumps(diplomacy_matrix),
        'state_name_id_map': json.dumps(state_name_id_map),
        'graph_data': json.dumps([{
            'i': c.get('i'),
            'c': c.get('c', []),
            'h': c.get('h', 0),
            'b': c.get('biome', 0),
            'p': c.get('p', [0, 0])
        } for c in (map_data.get('pack', {}).get('cells', []) if map_data else [])])
    }
    
    html_output = template.render(context)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
        
    print(f"Map generated at {output_file}")
