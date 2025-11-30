import json
import collections
import os
import re

import glob

# Configuration
INPUT_DIR = r'c:\Github_Projects\fantasy-world\fantasy_map'
OUTPUT_DIR = r'c:\Github_Projects\fantasy-world\reports'

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_data(data):
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

    valid_burgs = [b for b in burgs if isinstance(b, dict) and 'name' in b]
    
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

def generate_html(data, analysis, output_file):
    info = data.get('info', {})
    settings = data.get('settings', {})
    pack = data.get('pack', {})
    
    biomes_data = data.get('biomesData', {})
    states = pack.get('states', [])
    
    # Helper to get name/color safely
    def get_meta(source, idx, key, default):
        return source[idx].get(key, default) if idx < len(source) else default

    # Prepare Sections
    sections = []
    charts_config = []
    
    # 1. Biomes
    sorted_biomes = sorted(analysis['biome_stats'].items(), key=lambda x: x[1]['area'], reverse=True)
    b_rows = ""
    b_chart = {'labels': [], 'data': [], 'colors': []}
    
    for bid, stats in sorted_biomes:
        name = biomes_data.get('name', [])[bid] if bid < len(biomes_data.get('name', [])) else "Unknown"
        color = biomes_data.get('color', [])[bid] if bid < len(biomes_data.get('color', [])) else "#ccc"
        pct = (stats['area'] / analysis['total_area'] * 100) if analysis['total_area'] else 0
        
        b_rows += f"""<tr><td><span class="color-box" style="background-color: {color}"></span>{name}</td>
                      <td>{stats['area']:,.0f}</td><td>{pct:.1f}%</td><td>{stats['cells']}</td></tr>"""
        
        if name.lower() != "marine":
            b_chart['labels'].append(name)
            b_chart['data'].append(stats['area'])
            b_chart['colors'].append(color)
            
    sections.append(generate_section_html('biomes-section', 'Biomes', ['Biome', 'Area', '% Area', 'Cells'], b_rows, 'biomesChart'))
    charts_config.append({
        'id': 'biomesChart', 'type': 'pie', 'data': b_chart, 
        'title': 'Biome Distribution (Area) - Excluding Marine',
        'dataset_label': 'Area', 'legend_pos': 'right'
    })

    # 2. States
    sorted_states = sorted(analysis['state_stats'].items(), key=lambda x: x[1]['pop'], reverse=True)
    s_rows = ""
    s_chart = {'labels': [], 'data': [], 'colors': []}
    
    for sid, stats in sorted_states:
        name = get_meta(states, sid, 'name', f'State {sid}')
        color = get_meta(states, sid, 'color', '#ccc')
        burg_count = sum(1 for b in analysis['valid_burgs'] if b.get('state') == sid)
        
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
            sid = b.get('state', 0)
            s_name = get_meta(states, sid, 'name', 'Neutral')
            s_color = get_meta(states, sid, 'color', '#ccc')
            
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
        legend_display = 'true' if c['type'] == 'pie' else 'false'
        scales_config = ""
        if c['type'] == 'bar':
            # For bar charts, we want to ensure the index axis (where labels are) shows all ticks
            idx_axis = c.get('indexAxis', 'x')
            scales_config = f", scales: {{ {idx_axis}: {{ ticks: {{ autoSkip: false }} }} }}"

        js_charts += f"""
        new Chart(document.getElementById('{c['id']}').getContext('2d'), {{
            type: '{c['type']}',
            data: {{
                labels: {json.dumps(c['data']['labels'])},
                datasets: [{{
                    label: '{c.get('dataset_label', 'Value')}',
                    data: {json.dumps(c['data']['data'])},
                    backgroundColor: {json.dumps(c['data']['colors'])},
                    borderWidth: 1
                }}]
            }},
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
    <link rel="stylesheet" href="styles.css">
    </head><body>
    <a href="index.html" class="back-link">&larr; Back to Index</a>
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

def generate_index_html(reports, output_dir):
    links_html = ""
    for name, filename in reports:
        # Filename is absolute path, need relative for link
        rel_path = os.path.basename(filename)
        links_html += f"""
        <a href="{rel_path}" class="report-card">
            <div class="report-icon">🗺️</div>
            <div class="report-name">{name}</div>
            <div class="report-action">View Report &rarr;</div>
        </a>"""

    html = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Fantasy World Reports</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0 auto; padding: 40px; background: #f4f4f9; max-width: 800px; }}
        h1 {{ text-align: center; color: #2c3e50; margin-bottom: 40px; }}
        .reports-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }}
        .report-card {{ background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); text-decoration: none; color: inherit; transition: transform 0.2s, box-shadow 0.2s; display: flex; flex-direction: column; align-items: center; text-align: center; }}
        .report-card:hover {{ transform: translateY(-5px); box-shadow: 0 8px 15px rgba(0,0,0,0.1); }}
        .report-icon {{ font-size: 3em; margin-bottom: 15px; }}
        .report-name {{ font-size: 1.2em; font-weight: bold; margin-bottom: 10px; color: #2c3e50; }}
        .report-action {{ color: #3498db; font-weight: 500; }}
    </style></head><body>
    <h1>Fantasy World Reports</h1>
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

    json_files = glob.glob(os.path.join(INPUT_DIR, '*.json'))
    
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
                output_filename = os.path.join(OUTPUT_DIR, f"{safe_name}_report.html")
                
                generate_html(data, analyze_data(data), output_filename)
                generated_reports.append((map_name, output_filename))
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
        
        if generated_reports:
            generate_index_html(generated_reports, OUTPUT_DIR)
