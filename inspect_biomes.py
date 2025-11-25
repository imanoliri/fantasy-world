import json

file_path = r'c:\Github_Projects\fantasy-world\fantasy_map\Montreia Full 2024-05-23-10-01.json'

with open(file_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

biomes = data.get('biomesData')
print("Type:", type(biomes))
if isinstance(biomes, list):
    print("Length:", len(biomes))
    if len(biomes) > 0:
        print("First item:", biomes[0])
elif isinstance(biomes, dict):
    print("Keys:", list(biomes.keys()))
    first_key = list(biomes.keys())[0]
    print("First item:", biomes[first_key])
else:
    print("Content:", biomes)
