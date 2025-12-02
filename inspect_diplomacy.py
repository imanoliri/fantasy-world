import json

filepath = r'c:\Github_Projects\fantasy-world\fantasy_maps\Bouzonia Full 2025-12-02-20-29.json'

with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

states = data.get('pack', {}).get('states', [])
print(f"Number of states: {len(states)}")
if len(states) > 1:
    print("Example state keys:", states[1].keys())
    if 'diplomacy' in states[1]:
        print("Diplomacy data example:", states[1]['diplomacy'])
    else:
        print("No 'diplomacy' key in state object. Checking for global diplomacy data...")
        # Check root or pack for diplomacy
        if 'diplomacy' in data:
            print("Found 'diplomacy' in root")
        elif 'pack' in data and 'diplomacy' in data['pack']:
             print("Found 'diplomacy' in pack")
