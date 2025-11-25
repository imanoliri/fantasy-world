import json

file_path = r'c:\Github_Projects\fantasy-world\fantasy_map\Montreia Full 2024-05-23-10-01.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("Root keys:", list(data.keys()))
if 'pack' in data:
    print("Pack keys:", list(data['pack'].keys()))
