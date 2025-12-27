
import json

path = "d:\\Imanol\\Projects\\fantasy-world\\fantasy_maps\\Montreia Full 2025-12-02-20-29.json"
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

cells = data.get('pack', {}).get('cells', [])
if cells:
    print("Keys in first cell:", cells[0].keys())
    print("First cell content:", cells[0])
    # check if 'c' is in all cells
    has_c = all('c' in cell for cell in cells)
    print(f"All cells have neighbors 'c': {has_c}")
else:
    print("No cells found")
