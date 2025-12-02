import json

filepath = r'c:\Github_Projects\fantasy-world\fantasy_maps\Bouzonia Full 2025-12-02-20-29.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Root keys:", data.keys())
if 'pack' in data:
    print("Pack keys:", data['pack'].keys())

# Check for specific interesting data
interesting_keys = ['religions', 'cultures', 'states', 'provinces', 'rivers', 'markers']
for key in interesting_keys:
    if key in data:
        print(f"Found {key}: {len(data[key])} items")
    elif 'pack' in data and key in data['pack']:
        print(f"Found {key} in pack")

# Check cell attributes
if 'pack' in data and 'cells' in data['pack']:
    cells = data['pack']['cells']
    if cells:
        # If it's a list of objects
        if isinstance(cells[0], dict):
            print("Cell attributes:", cells[0].keys())
        # If it's column-based (Azgaar sometimes uses arrays for properties)
        else:
            print("Cells might be packed arrays. Checking other keys in pack for cell data...")
            # Common packed keys: 'c' (culture), 's' (state), 'r' (religion), 'p' (province), 'h' (height), 'temp', 'prec'
            potential_cell_data = ['c', 's', 'r', 'p', 'h', 'temp', 'prec', 'pop']
            found = [k for k in potential_cell_data if k in data['pack']]
            print("Potential cell data arrays in pack:", found)
