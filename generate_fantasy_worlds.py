import json
import collections
import os
import re
import glob
import shutil

# Import modules
import simulate_economy
import generate_interactive_map
import simulate_trade

# Configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, 'fantasy_maps')
OUTPUT_DIR = os.path.join(BASE_DIR, 'fantasy_worlds')

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"Saved JSON to {filepath}")

def analyze_world_data(data):
    pack = data.get('pack', {})
    settings = data.get('settings', {})
    cells = pack.get('cells', [])
    burgs = pack.get('burgs', [])
    
    total_area = 0
    total_pop = 0
    
    biome_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0})
    state_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0})
    
    pop_rate = float(settings.get('populationRate', 1000))

    for cell in cells:
        if 'area' not in cell: continue
        area = cell.get('area', 0)
        pop = cell.get('pop', 0) * pop_rate
        
        biome_stats[cell.get('biome', 0)]['area'] += area
        biome_stats[cell.get('biome', 0)]['cells'] += 1
        biome_stats[cell.get('biome', 0)]['pop'] += pop
        
        state_id = cell.get('state', 0)
        if state_id > 0:
            state_stats[state_id]['area'] += area
            state_stats[state_id]['cells'] += 1
            state_stats[state_id]['pop'] += pop

        total_area += area
        total_pop += pop

    # Create a lookup for cells by index 'i'
    # The cells list in pack['cells'] might not be sorted or might skip indices, 
    # but usually it's a list where index matches 'i' if it's dense. 
    # However, Azgaar's cells are often a list of objects with 'i'.
    # Let's create a dict for safety.
    cell_lookup = {c.get('i'): c for c in cells if 'i' in c}

    valid_burgs = []
    for b in burgs:
        if isinstance(b, dict) and 'name' in b:
            # Enrich with cell data
            cell_id = b.get('cell')
            if cell_id is not None and cell_id in cell_lookup:
                cell = cell_lookup[cell_id]
                b['h'] = cell.get('h', 0)
                b['road'] = cell.get('road', 0)
                b['haven'] = cell.get('haven', 0)
                b['biome'] = cell.get('biome', 0)
                # Ensure state is consistent (burg state should match cell state usually, but burg state takes precedence)
                if 'state' not in b:
                    b['state'] = cell.get('state', 0)
            
            valid_burgs.append(b)
    
    return {
        'total_area': total_area, 'total_pop': total_pop,
        'biome_stats': biome_stats, 'state_stats': state_stats,
        'valid_burgs': valid_burgs
    }

def generate_section_html(section_id, title, table_headers, rows_html, chart_id):
    return f"""
        <div class="card" id="{section_id}">
            <div class="header-row">
                <h2>{title}</h2>
                <div class="toggle-container">
                    <span>Table</span>
                    <label class="switch">
                        <input type="checkbox" checked onchange="toggleView('{section_id}')">
                        <span class="slider"></span>
                    </label>
                    <span>Chart</span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead><tr>{''.join(f'<th>{h}</th>' for h in table_headers)}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            <div class="chart-container"><canvas id="{chart_id}"></canvas></div>
        </div>"""

def generate_world_report(data, analysis, output_file):
    info = data.get('info', {})
    settings = data.get('settings', {})
    pack = data.get('pack', {})
    
    biomes_data = data.get('biomesData', {})
    states = pack.get('states', [])
    
    # Helper to get name/color safely
    def get_meta(source, idx, key, default):
        if idx < len(source):
            val = source[idx].get(key)
            return val if val is not None else default
        return default

    # Prepare Sections
    sections = []
    charts_config = []
    
    # 1. Biomes
    # Table sorted by Area
    sorted_biomes_area = sorted(analysis['biome_stats'].items(), key=lambda x: x[1]['area'], reverse=True)
    b_rows = ""
    
    for bid, stats in sorted_biomes_area:
        name = biomes_data.get('name', [])[bid] if bid < len(biomes_data.get('name', [])) else "Unknown"
        color = biomes_data.get('color', [])[bid] if bid < len(biomes_data.get('color', [])) else "#ccc"
        pct = (stats['area'] / analysis['total_area'] * 100) if analysis['total_area'] else 0
        
        b_rows += f"""<tr><td><span class="color-box" style="background-color: {color}"></span>{name}</td>
                      <td>{stats['area']:,.0f}</td><td>{pct:.1f}%</td><td>{stats['cells']}</td></tr>"""

    # Chart sorted by Temperature (Cold -> Warm)
    BIOME_RANK = {
        'Glacier': 1, 'Tundra': 2, 'Taiga': 3, 'Cold desert': 4,
        'Temperate rainforest': 5, 'Temperate deciduous forest': 6,
        'Grassland': 7, 'Wetland': 8,
        'Tropical seasonal forest': 9, 'Tropical rainforest': 10,
        'Savanna': 11, 'Hot desert': 12
    }
    
    # Filter and sort for chart
    chart_biomes = []
    for bid, stats in analysis['biome_stats'].items():
        name = biomes_data.get('name', [])[bid] if bid < len(biomes_data.get('name', [])) else "Unknown"
        if name.lower() == "marine": continue
        
        color = biomes_data.get('color', [])[bid] if bid < len(biomes_data.get('color', [])) else "#ccc"
        rank = BIOME_RANK.get(name, 99)
        chart_biomes.append({'name': name, 'area': stats['area'], 'color': color, 'rank': rank})
        
    chart_biomes.sort(key=lambda x: x['rank'])
    
    # Prepare Stacked Bar Data (One bar, multiple datasets)
    b_chart = {'labels': ['Global Biome Distribution'], 'datasets': []}
    total_chart_area = 0
    
    for b in chart_biomes:
        total_chart_area += b['area']
        b_chart['datasets'].append({
            'label': b['name'],
            'data': [b['area']],
            'backgroundColor': b['color'],
            'barPercentage': 0.9, # Make bar thick
            'categoryPercentage': 1.0
        })
            
    sections.append(generate_section_html('biomes-section', 'Biomes', ['Biome', 'Area', '% Area', 'Cells'], b_rows, 'biomesChart'))
    charts_config.append({
        'id': 'biomesChart', 'type': 'bar', 'data': b_chart, 
        'title': 'Biome Distribution (Cold to Warm)',
        'dataset_label': 'Area', 'legend_pos': 'bottom',
        'indexAxis': 'y', 'stacked': True,
        'x_max': total_chart_area
    })

    # 2. States
    sorted_states = sorted(analysis['state_stats'].items(), key=lambda x: x[1]['pop'], reverse=True)
    s_rows = ""
    s_chart = {'labels': [], 'data': [], 'colors': []}
    
    for sid, stats in sorted_states:
        name = get_meta(states, sid, 'name', f'State {sid}')
        color = get_meta(states, sid, 'color', '#ccc')
        burg_count = sum(1 for b in analysis['valid_burgs'] if b.get('state_id') == sid)
        
        s_rows += f"""<tr><td><span class="color-box" style="background-color: {color}"></span>{name}</td>
                      <td>{stats['area']:,.0f}</td><td>{int(stats['pop']):,}</td><td>{burg_count}</td></tr>"""
        
        s_chart['labels'].append(name)
        s_chart['data'].append(stats['pop'])
        s_chart['colors'].append(color)

    sections.append(generate_section_html('states-section', 'States', ['State', 'Area', 'Population', 'Burgs'], s_rows, 'statesChart'))
    charts_config.append({
        'id': 'statesChart', 'type': 'bar', 'data': s_chart, 
        'title': 'State Populations', 'indexAxis': 'y',
        'dataset_label': 'Population', 'legend_pos': 'top'
    })

    # 3. Burgs (Largest & Smallest)
    pop_rate = float(settings.get('populationRate', 1000))
    
    def process_burgs(burg_list, chart_id, title, section_id):
        rows = ""
        chart = {'labels': [], 'data': [], 'colors': []}
        for b in burg_list:
            name = b.get('name', 'Unnamed')
            pop = b.get('population', 0) * pop_rate
            sid = int(b.get('state_id', 0))
            s_name = get_meta(states, sid, 'name', 'Neutral')
            s_color = get_meta(states, sid, 'color', '#ccc')
            
            # Debug print for first few
            if len(chart['labels']) < 3:
                print(f"DEBUG: Burg {name}, State ID {sid}, Color {s_color}")

            rows += f"<tr><td><span class=\"color-box\" style=\"background-color: {s_color}\"></span>{name}</td><td>{int(pop):,}</td><td>{s_name}</td><td>{b.get('type', 'Generic')}</td></tr>"
            chart['labels'].append(name)
            chart['data'].append(pop)
            chart['colors'].append(s_color)
            
        return generate_section_html(section_id, title, ['Name', 'Population', 'State', 'Type'], rows, chart_id), \
               {'id': chart_id, 'type': 'bar', 'data': chart, 'title': title, 'indexAxis': 'y', 'dataset_label': 'Population'}

    sorted_burgs = sorted(analysis['valid_burgs'], key=lambda x: x.get('population', 0), reverse=True)[:20]
    sec, cfg = process_burgs(sorted_burgs, 'burgsChart', 'Largest Burgs', 'burgs-section')
    sections.append(sec)
    charts_config.append(cfg)
    
    sorted_smallest = sorted(analysis['valid_burgs'], key=lambda x: x.get('population', 0))[:20]
    sec, cfg = process_burgs(sorted_smallest, 'smallestBurgsChart', 'Smallest Burgs', 'smallest-burgs-section')
    sections.append(sec)
    charts_config.append(cfg)

    # Generate JS for charts
    js_charts = ""
    for c in charts_config:
        legend_display = 'true' if c['type'] == 'pie' or c.get('stacked') else 'false'
        
        scales_config = ""
        if c.get('stacked'):
            x_max_str = f", max: {c['x_max']}" if 'x_max' in c else ""
            scales_config = f", scales: {{ x: {{ stacked: true, display: false{x_max_str} }}, y: {{ stacked: true, display: false }} }}"
        elif c['type'] == 'bar':
            # For bar charts, we want to ensure the index axis (where labels are) shows all ticks
            idx_axis = c.get('indexAxis', 'x')
            scales_config = f", scales: {{ {idx_axis}: {{ ticks: {{ autoSkip: false }} }} }}"

        if 'datasets' in c['data']:
            data_json = json.dumps(c['data'])
        else:
            data_json = f"""{{
                labels: {json.dumps(c['data']['labels'])},
                datasets: [{{
                    label: '{c.get('dataset_label', 'Value')}',
                    data: {json.dumps(c['data']['data'])},
                    backgroundColor: {json.dumps(c['data']['colors'])},
                    borderWidth: 1
                }}]
            }}"""

        js_charts += f"""
        new Chart(document.getElementById('{c['id']}').getContext('2d'), {{
            type: '{c['type']}',
            data: {data_json},
            options: {{
                responsive: true, maintainAspectRatio: false,
                indexAxis: '{c.get('indexAxis', 'x')}',
                plugins: {{ 
                    legend: {{ display: {legend_display}, position: '{c.get('legend_pos', 'top')}' }}, 
                    title: {{ display: true, text: '{c['title']}' }} 
                }}{scales_config}
            }}
        }});"""

    # Final HTML assembly
    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>World Analysis: {info.get('mapName', 'Montreia')}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="../styles.css">
    </head><body>
    <a href="../index.html" class="back-link">&larr; Back to Index</a>
    <h1>World Analysis: {info.get('mapName', 'Montreia')}</h1>
    <div class="card"><h2>General Statistics</h2><div class="stat-grid">
        <div class="stat-box"><div class="stat-value">{len(states)-1 if len(states)>1 else 0}</div><div>States</div></div>
        <div class="stat-box"><div class="stat-value">{len(analysis['valid_burgs']):,}</div><div>Burgs</div></div>
        <div class="stat-box"><div class="stat-value">{analysis['total_area']:,.0f}</div><div>Total Area</div></div>
        <div class="stat-box"><div class="stat-value">{int(analysis['total_pop']):,}</div><div>Total Pop</div></div>
    </div></div>
    {''.join(sections)}
    <script>
        function toggleView(id) {{ document.getElementById(id).classList.toggle('show-table'); }}
        {js_charts}
    </script></body></html>"""
    
    with open(output_file, 'w', encoding='utf-8') as f: f.write(html)
    print(f"Report generated at: {output_file}")

def generate_css(output_dir):
    css = """
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0 auto; padding: 20px; background: #f4f4f9; max-width: 1000px; }
        .card { background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; } th { background-color: #f8f9fa; }
        .stat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-box { background: #eef2f5; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-value { font-size: 1.5em; font-weight: bold; color: #2980b9; }
        .color-box { display: inline-block; width: 12px; height: 12px; margin-right: 5px; border: 1px solid #ccc; }
        .header-row { display: flex; justify-content: space-between; align-items: center; }
        .toggle-container { display: flex; align-items: center; gap: 10px; font-size: 0.9em; }
        .switch { position: relative; display: inline-block; width: 50px; height: 24px; }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .4s; border-radius: 24px; }
        .slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 4px; bottom: 4px; background-color: white; transition: .4s; border-radius: 50%; }
        input:checked + .slider { background-color: #2196F3; }
        input:checked + .slider:before { transform: translateX(26px); }
        .chart-container { position: relative; height: 400px; width: 100%; display: block; }
        .table-container { display: none; overflow-x: auto; }
        .show-table .chart-container { display: none; } .show-table .table-container { display: block; }
        .back-link { display: inline-block; margin-bottom: 20px; color: #2980b9; text-decoration: none; font-weight: bold; }
        .back-link:hover { text-decoration: underline; }
    """
    css_path = os.path.join(output_dir, 'styles.css')
    with open(css_path, 'w', encoding='utf-8') as f: f.write(css)
    print(f"CSS generated at: {css_path}")

def generate_worlds_index(reports, output_dir):
    links_html = ""
    for name, report_file, map_file in reports:
        # Filename is absolute path, need relative for link
        # Reports are now in subfolders, so we need to link into them
        # report_file: reports/MapName/MapName_report.html
        # map_file: reports/MapName/MapName_map.html
        
        report_rel = os.path.relpath(report_file, output_dir)
        map_rel = os.path.relpath(map_file, output_dir)
        
        links_html += f"""
        <div class="report-card">
            <div class="report-icon">🗺️</div>
            <div class="report-name">{name}</div>
            <div class="report-actions">
                <a href="{report_rel}" class="report-action">View Report &rarr;</a>
                <a href="{map_rel}" class="report-action">Interactive Map &rarr;</a>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy Worlds</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0 auto; padding: 40px; background: #f4f4f9; max-width: 800px; }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 40px; }}
        .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
        .report-card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; align-items: center; text-align: center; }}
        .report-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
        .report-icon {{ font-size: 3em; margin-bottom: 15px; }}
        .report-name {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
        .report-actions {{ display: flex; flex-direction: column; gap: 10px; width: 100%; }}
        .report-action {{ color: #3498db; font-weight: 500; text-decoration: none; border: 1px solid #3498db; padding: 8px; border-radius: 4px; transition: background 0.2s, color 0.2s; }}
        .report-action:hover {{ background: #3498db; color: white; }}
    </style></head><body>
    <h1>Fantasy Worlds</h1>
    <div class="reports-grid">
        {links_html}
    </div>
    </body></html>"""
    
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f: f.write(html)
    print(f"Index generated at: {index_path}")

if __name__ == "__main__":
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")
        
    generate_css(OUTPUT_DIR)

    # Copy interactive map CSS
    map_css_src = os.path.join(BASE_DIR, 'templates', 'map.css')
    map_css_dst = os.path.join(OUTPUT_DIR, 'map.css')
    if os.path.exists(map_css_src):
        shutil.copy(map_css_src, map_css_dst)
        print(f"Copied map.css to: {map_css_dst}")
    else:
        print(f"Warning: map.css not found at {map_css_src}")

    # Build map.js from modules
    js_modules_dir = os.path.join(BASE_DIR, 'templates', 'js_modules')
    # Config file moved to templates/ for visibility
    modules_config_path = os.path.join(BASE_DIR, 'templates', 'js_modules_to_load.json')
    map_js_dst = os.path.join(OUTPUT_DIR, 'map.js')
    
    map_js_content = ""
    
    if os.path.exists(modules_config_path):
        try:
            with open(modules_config_path, 'r', encoding='utf-8') as f:
                module_list = json.load(f)
            
            print(f"Bundling {len(module_list)} JS modules from config...")
            for mod_name in module_list:
                mod_path = os.path.join(js_modules_dir, mod_name)
                if os.path.exists(mod_path):
                    with open(mod_path, 'r', encoding='utf-8') as f:
                        map_js_content += f.read() + "\n\n"
                else:
                    print(f"Warning: Module {mod_name} listed in modules.json not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {modules_config_path}")
    elif os.path.exists(js_modules_dir):
         # Fallback to sorted glob if json missing (backup behavior)
         print(f"Warning: modules.json not found in {js_modules_dir}. Using alphabetical order.")
         module_files = sorted(glob.glob(os.path.join(js_modules_dir, '*.js')))
         for mod_file in module_files:
             with open(mod_file, 'r', encoding='utf-8') as f:
                 map_js_content += f.read() + "\n\n"
    else:
        print(f"Warning: JS Modules directory not found at {js_modules_dir}")

    if map_js_content:
        with open(map_js_dst, 'w', encoding='utf-8') as f:
            f.write(map_js_content)
        print(f"Generated map.js at {map_js_dst}")
    
    # Fallback to legacy map.js if no modules found
    if not map_js_content:
        map_js_src = os.path.join(BASE_DIR, 'templates', 'map.js')
        if os.path.exists(map_js_src):
            shutil.copy(map_js_src, map_js_dst)
            print(f"Copied legacy map.js to: {map_js_dst}")
        else:
            print(f"Warning: legacy map.js source not found")

    json_files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
    
    # Load simulation config once
    sim_config = simulate_economy.load_simulation_config()
    
    generated_reports = []

    if not json_files:
        print(f"No JSON files found in {INPUT_DIR}")
    else:
        print(f"Found {len(json_files)} map files.")
        for filepath in json_files:
            try:
                print(f"Processing {os.path.basename(filepath)}...")
                data = load_data(filepath)
                
                map_name = data.get('info', {}).get('mapName', 'Unknown_Map')
                safe_name = re.sub(r'[^\w\-_]', '_', map_name)
                
                # Create Map Folder
                map_dir = os.path.join(OUTPUT_DIR, safe_name)
                if not os.path.exists(map_dir):
                    os.makedirs(map_dir)
                
                # 1. Run Economy Simulation
                processed_burgs = simulate_economy.process_map_data(data, sim_config)

                # Add state_name and rename state to state_id
                states = data.get('pack', {}).get('states', [])
                for burg in processed_burgs:
                    state_id = burg.get('state')
                    if state_id is not None:
                        # Get state name, default to "Neutral" or "Unknown" if not found
                        # States list index matches state ID usually, but safe lookup is better if IDs are properties
                        # Based on typical Azgaar format, states is a list where index = state_id
                        state_name = "Neutral"
                        if isinstance(states, list) and 0 <= state_id < len(states):
                            state_name = states[state_id].get('name', 'Neutral')
                        
                        burg['state_name'] = state_name
                        burg['state_id'] = state_id
                        del burg['state']
                        
                        # Reorder keys for cleaner JSON (optional but nice)
                        # Create a new dict with desired order
                        new_order = {'id': burg['id'], 'name': burg['name'], 'x': burg['x'], 'y': burg['y'], 
                                     'type': burg['type'], 'state_id': state_id, 'state_name': state_name}
                        # Add remaining keys
                        for k, v in burg.items():
                            if k not in new_order:
                                new_order[k] = v
                        
                        # Update burg object in place (clear and update)
                        burg.clear()
                        burg.update(new_order)
                
                # Save Burgs JSON
                burgs_file = os.path.join(map_dir, f"{safe_name}_burgs.json")
                save_json(processed_burgs, burgs_file)
                
                # Update burgs in data object for analysis
                data['pack']['burgs'] = processed_burgs
                
                # 2. Run Trade Simulation
                states = data.get('pack', {}).get('states', [])
                states_file = os.path.join(map_dir, f"{safe_name}_states.json")
                save_json(states, states_file)

                cultures = data.get('pack', {}).get('cultures', [])
                cultures_file = os.path.join(map_dir, f"{safe_name}_cultures.json")
                save_json(cultures, cultures_file)

                trades = simulate_trade.simulate_trade(processed_burgs)
                
                # Save Trade Routes JSON
                trades_file = os.path.join(map_dir, f"{safe_name}_trade_routes.json")
                save_json(trades, trades_file)
                
                # 3. Generate Interactive Map
                map_file = os.path.join(map_dir, f"{safe_name}_map.html")
                generate_interactive_map.generate_map(processed_burgs, map_file, trades, safe_name, states=states, cultures=cultures, map_data=data)
                
                # 4. Generate Static Report
                report_filename = os.path.join(map_dir, f"{safe_name}_report.html")
                generate_world_report(data, analyze_world_data(data), report_filename)
                
                generated_reports.append((map_name, report_filename, map_file))
                
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                import traceback
                traceback.print_exc()
        
        if generated_reports:
            generate_worlds_index(generated_reports, OUTPUT_DIR)
