import json
import collections

# Configuration
INPUT_FILE = r'c:\Github_Projects\fantasy-world\fantasy_map\Montreia Full 2024-05-23-10-01.json'
OUTPUT_FILE = r'c:\Github_Projects\fantasy-world\montreia_report.html'

def load_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_html(data):
    pack = data.get('pack', {})
    info = data.get('info', {})
    settings = data.get('settings', {})
    
    # Extract Data
    biomes_data = data.get('biomesData', {}) # Usually a dict or list
    # If biomesData is a dict with ids as keys, or list. Azgaar usually has it as object with i, name, color
    # Let's handle both list and dict if possible, but usually it's a list in recent versions or dict in older.
    # Based on keys seen earlier, it's a top level key.
    
    cells = pack.get('cells', [])
    burgs = pack.get('burgs', [])
    states = pack.get('states', [])
    cultures = pack.get('cultures', [])
    religions = pack.get('religions', [])
    
    # Analysis Storage
    total_area = 0
    total_pop = 0
    
    biome_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0})
    state_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0, 'burgs': 0})
    culture_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0, 'burgs': 0})
    religion_stats = collections.defaultdict(lambda: {'area': 0, 'cells': 0, 'pop': 0, 'burgs': 0})
    
    # Process Cells
    # cells is often a columnar data structure in Azgaar (arrays of values), OR a list of objects.
    # The view_file output showed 'cells' as a LIST OF OBJECTS (e.g., {"i": 0, "v": [...], "biome": 0, ...})
    # So we can iterate directly.
    
    for cell in cells:
        # Skip if 'i' is missing or it's a placeholder (though list of objects usually implies valid cells)
        if 'area' not in cell: continue
        
        area = cell.get('area', 0)
        pop = cell.get('pop', 0) * float(settings.get('populationRate', 1000)) # pop is usually scaled
        # Actually pop in cells is usually raw population * populationRate? 
        # In Azgaar JSON, cell.pop is often just a number. The settings.populationRate is a multiplier usually applied in UI.
        # Let's assume cell.pop needs multiplication if it looks small, or check settings.
        # Wait, usually cell.pop is already the population number in some versions, or needs 'populationRate'.
        # Let's use the raw value * rate for now, or just raw if it looks big. 
        # In the file view: "pop": 0 for many cells. "populationRate": "1000".
        # Let's assume we multiply.
        
        real_pop = pop # We will format this later.
        
        # Biome
        biome_id = cell.get('biome', 0)
        biome_stats[biome_id]['area'] += area
        biome_stats[biome_id]['cells'] += 1
        biome_stats[biome_id]['pop'] += real_pop
        
        # State
        state_id = cell.get('state', 0)
        if state_id > 0: # 0 is usually neutrals/water
            state_stats[state_id]['area'] += area
            state_stats[state_id]['cells'] += 1
            state_stats[state_id]['pop'] += real_pop
            
        # Culture
        culture_id = cell.get('culture', 0)
        if culture_id > 0:
            culture_stats[culture_id]['area'] += area
            culture_stats[culture_id]['cells'] += 1
            culture_stats[culture_id]['pop'] += real_pop
            
        # Religion
        religion_id = cell.get('religion', 0)
        if religion_id > 0:
            religion_stats[religion_id]['area'] += area
            religion_stats[religion_id]['cells'] += 1
            religion_stats[religion_id]['pop'] += real_pop

        total_area += area
        total_pop += real_pop

    # Process Burgs
    # Burgs is usually a list of objects.
    valid_burgs = [b for b in burgs if isinstance(b, dict) and 'name' in b] # Filter out empty/placeholders
    
    # HTML Construction
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>World Analysis: {info.get('mapName', 'Montreia')}</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max_width: 1200px; margin: 0 auto; padding: 20px; background: #f4f4f9; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .card {{ background: white; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
            th {{ background-color: #f8f9fa; }}
            .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }}
            .stat-box {{ background: #eef2f5; padding: 15px; border-radius: 5px; text-align: center; }}
            .stat-value {{ font-size: 1.5em; font-weight: bold; color: #2980b9; }}
            .color-box {{ display: inline-block; width: 12px; height: 12px; margin-right: 5px; border: 1px solid #ccc; }}
            
            /* Toggle Switch */
            .header-row {{ display: flex; justify-content: space-between; align-items: center; }}
            .toggle-container {{ display: flex; align-items: center; gap: 10px; font-size: 0.9em; }}
            .switch {{ position: relative; display: inline-block; width: 50px; height: 24px; }}
            .switch input {{ opacity: 0; width: 0; height: 0; }}
            .slider {{ position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; -webkit-transition: .4s; transition: .4s; border-radius: 24px; }}
            .slider:before {{ position: absolute; content: ""; height: 16px; width: 16px; left: 4px; bottom: 4px; background-color: white; -webkit-transition: .4s; transition: .4s; border-radius: 50%; }}
            input:checked + .slider {{ background-color: #2196F3; }}
            input:focus + .slider {{ box-shadow: 0 0 1px #2196F3; }}
            input:checked + .slider:before {{ -webkit-transform: translateX(26px); -ms-transform: translateX(26px); transform: translateX(26px); }}
            
            /* View Containers */
            .chart-container {{ position: relative; height: 400px; width: 100%; display: block; }}
            .table-container {{ display: none; overflow-x: auto; }}
            .show-table .chart-container {{ display: none; }}
            .show-table .table-container {{ display: block; }}
        </style>
    </head>
    <body>
        <h1>World Analysis: {info.get('mapName', 'Montreia')}</h1>
        
        <div class="card">
            <h2>General Statistics</h2>
            <div class="stat-grid">
                <div class="stat-box">
                    <div class="stat-value">{len(states)-1 if len(states)>1 else 0}</div>
                    <div>States</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{len(valid_burgs):,}</div>
                    <div>Burgs (Cities/Towns)</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{total_area:,.0f} {settings.get('areaUnit', 'sq mi')}</div>
                    <div>Total Land Area</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{int(total_pop):,}</div>
                    <div>Total Population (Approx)</div>
                </div>
            </div>
        </div>

        <!-- Biomes Section -->
        <div class="card" id="biomes-section">
            <div class="header-row">
                <h2>Biomes</h2>
                <div class="toggle-container">
                    <span>Table</span>
                    <label class="switch">
                        <input type="checkbox" checked onchange="toggleView('biomes-section')">
                        <span class="slider"></span>
                    </label>
                    <span>Chart</span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Biome</th>
                            <th>Area</th>
                            <th>% Area</th>
                            <th>Cells</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Biomes Table
    # biomesData is a dict of lists (columnar)
    # keys: 'i', 'name', 'color', etc.
    biome_names = biomes_data.get('name', [])
    biome_colors = biomes_data.get('color', [])
    
    # Sort biomes by area
    sorted_biomes = sorted(biome_stats.items(), key=lambda x: x[1]['area'], reverse=True)
    
    # Prepare data for charts
    chart_biomes_labels = []
    chart_biomes_data = []
    chart_biomes_colors = []

    for bid, stats in sorted_biomes:
        b_name = "Unknown"
        b_color = "#ccc"
        
        if bid < len(biome_names):
            b_name = biome_names[bid]
        
        if bid < len(biome_colors):
            b_color = biome_colors[bid]

        pct = (stats['area'] / total_area * 100) if total_area > 0 else 0
        
        # Filter Marine from Chart only
        if b_name.lower() != "marine":
            chart_biomes_labels.append(b_name)
            chart_biomes_data.append(stats['area'])
            chart_biomes_colors.append(b_color)

        html += f"""
                        <tr>
                            <td><span class="color-box" style="background-color: {b_color}"></span>{b_name}</td>
                            <td>{stats['area']:,.0f}</td>
                            <td>{pct:.1f}%</td>
                            <td>{stats['cells']}</td>
                        </tr>
        """
        
    html += """
                    </tbody>
                </table>
            </div>
            <div class="chart-container">
                <canvas id="biomesChart"></canvas>
            </div>
        </div>
        
        <!-- States Section -->
        <div class="card" id="states-section">
            <div class="header-row">
                <h2>States</h2>
                <div class="toggle-container">
                    <span>Table</span>
                    <label class="switch">
                        <input type="checkbox" checked onchange="toggleView('states-section')">
                        <span class="slider"></span>
                    </label>
                    <span>Chart</span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>State</th>
                            <th>Area</th>
                            <th>Population</th>
                            <th>Burgs</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # States Table
    # states is a list, index = state_id. 0 is usually neutral.
    sorted_states = sorted(state_stats.items(), key=lambda x: x[1]['pop'], reverse=True)
    
    chart_states_labels = []
    chart_states_data = []
    chart_states_colors = []

    for sid, stats in sorted_states:
        s_name = "Neutral"
        s_color = "#ccc"
        if sid < len(states):
            s_name = states[sid].get('name', f'State {sid}')
            s_color = states[sid].get('color', '#ccc')
            
        # Count burgs for this state
        burg_count = sum(1 for b in valid_burgs if b.get('state') == sid)
        
        chart_states_labels.append(s_name)
        chart_states_data.append(stats['pop'])
        chart_states_colors.append(s_color)

        html += f"""
                        <tr>
                            <td><span class="color-box" style="background-color: {s_color}"></span>{s_name}</td>
                            <td>{stats['area']:,.0f}</td>
                            <td>{int(stats['pop']):,}</td>
                            <td>{burg_count}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
            <div class="chart-container">
                <canvas id="statesChart"></canvas>
            </div>
        </div>

        <!-- Burgs Section -->
        <div class="card" id="burgs-section">
            <div class="header-row">
                <h2>Largest Burgs</h2>
                <div class="toggle-container">
                    <span>Table</span>
                    <label class="switch">
                        <input type="checkbox" checked onchange="toggleView('burgs-section')">
                        <span class="slider"></span>
                    </label>
                    <span>Chart</span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Population</th>
                            <th>State</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Burgs Table (Top 20)
    # Sort by population
    sorted_burgs = sorted(valid_burgs, key=lambda x: x.get('population', 0), reverse=True)[:20]
    
    chart_burgs_labels = []
    chart_burgs_data = []
    chart_burgs_colors = []

    for b in sorted_burgs:
        name = b.get('name', 'Unnamed')
        pop = b.get('population', 0) * float(settings.get('populationRate', 1000))
        state_id = b.get('state', 0)
        state_name = states[state_id].get('name', 'Neutral') if state_id < len(states) else 'Unknown'
        state_color = states[state_id].get('color', '#ccc') if state_id < len(states) else '#ccc'
        b_type = b.get('type', 'Generic')
        
        chart_burgs_labels.append(name)
        chart_burgs_data.append(pop)
        chart_burgs_colors.append(state_color)

        html += f"""
                        <tr>
                            <td>{name}</td>
                            <td>{int(pop):,}</td>
                            <td>{state_name}</td>
                            <td>{b_type}</td>
                        </tr>
        """

    html += """
                    </tbody>
                </table>
            </div>
            <div class="chart-container">
                <canvas id="burgsChart"></canvas>
            </div>
        </div>

        <!-- Smallest Burgs Section -->
        <div class="card" id="smallest-burgs-section">
            <div class="header-row">
                <h2>Smallest Burgs</h2>
                <div class="toggle-container">
                    <span>Table</span>
                    <label class="switch">
                        <input type="checkbox" checked onchange="toggleView('smallest-burgs-section')">
                        <span class="slider"></span>
                    </label>
                    <span>Chart</span>
                </div>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th>Population</th>
                            <th>State</th>
                            <th>Type</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Smallest Burgs Table (Bottom 20)
    # Sort by population ascending to get the smallest
    sorted_smallest_burgs = sorted(valid_burgs, key=lambda x: x.get('population', 0))[:20]
    
    chart_smallest_burgs_labels = []
    chart_smallest_burgs_data = []
    chart_smallest_burgs_colors = []

    for b in sorted_smallest_burgs:
        name = b.get('name', 'Unnamed')
        pop = b.get('population', 0) * float(settings.get('populationRate', 1000))
        state_id = b.get('state', 0)
        state_name = states[state_id].get('name', 'Neutral') if state_id < len(states) else 'Unknown'
        state_color = states[state_id].get('color', '#ccc') if state_id < len(states) else '#ccc'
        b_type = b.get('type', 'Generic')
        
        chart_smallest_burgs_labels.append(name)
        chart_smallest_burgs_data.append(pop)
        chart_smallest_burgs_colors.append(state_color)

        html += f"""
                        <tr>
                            <td>{name}</td>
                            <td>{int(pop):,}</td>
                            <td>{state_name}</td>
                            <td>{b_type}</td>
                        </tr>
        """

    html += f"""
                    </tbody>
                </table>
            </div>
            <div class="chart-container">
                <canvas id="smallestBurgsChart"></canvas>
            </div>
        </div>

    <script>
        function toggleView(sectionId) {{
            const section = document.getElementById(sectionId);
            section.classList.toggle('show-table');
        }}

        // Biomes Chart (Pie)
        const ctxBiomes = document.getElementById('biomesChart').getContext('2d');
        new Chart(ctxBiomes, {{
            type: 'pie',
            data: {{
                labels: {json.dumps(chart_biomes_labels)},
                datasets: [{{
                    data: {json.dumps(chart_biomes_data)},
                    backgroundColor: {json.dumps(chart_biomes_colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'right' }},
                    title: {{ display: true, text: 'Biome Distribution (Area) - Excluding Marine' }}
                }}
            }}
        }});

        // States Chart (Horizontal Bar)
        const ctxStates = document.getElementById('statesChart').getContext('2d');
        new Chart(ctxStates, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_states_labels)},
                datasets: [{{
                    label: 'Population',
                    data: {json.dumps(chart_states_data)},
                    backgroundColor: {json.dumps(chart_states_colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: true, text: 'State Populations' }}
                }}
            }}
        }});

        // Burgs Chart (Horizontal Bar)
        const ctxBurgs = document.getElementById('burgsChart').getContext('2d');
        new Chart(ctxBurgs, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_burgs_labels)},
                datasets: [{{
                    label: 'Population',
                    data: {json.dumps(chart_burgs_data)},
                    backgroundColor: {json.dumps(chart_burgs_colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: true, text: 'Top 20 Burgs by Population' }}
                }}
            }}
        }});

        // Smallest Burgs Chart (Horizontal Bar)
        const ctxSmallestBurgs = document.getElementById('smallestBurgsChart').getContext('2d');
        new Chart(ctxSmallestBurgs, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_smallest_burgs_labels)},
                datasets: [{{
                    label: 'Population',
                    data: {json.dumps(chart_smallest_burgs_data)},
                    backgroundColor: {json.dumps(chart_smallest_burgs_colors)},
                    borderWidth: 1
                }}]
            }},
            options: {{
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ display: false }},
                    title: {{ display: true, text: 'Smallest 20 Burgs by Population' }}
                }}
            }}
        }});
    </script>
    </body>
    </html>
    """
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Report generated at: {OUTPUT_FILE}")

if __name__ == "__main__":
    data = load_data(INPUT_FILE)
    generate_html(data)
