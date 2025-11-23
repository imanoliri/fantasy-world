import json
import os


CITIZEN_INFO_FILE = "info/citizen_info.json"
SETTLEMENT_HIERARCHY_FILE = "info/settlement_sizes.json"
ECONOMIC_CONSTANTS_FILE = "info/economic_constants.json"

AFMG_MAP_FILE = "fantasy_map/Montreia Full 2024-05-23-10-01.json" 

def load_json_file(filepath):
    """Loads and returns data from a JSON file."""
    if not os.path.exists(filepath):
        print(f"Error: Required file not found at path: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {filepath}. Check file format.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while reading {filepath}: {e}")
        return None


def load_simulation_data():
    """Loads all external simulation configuration files."""
    
    print("\n--- Loading External Simulation Data ---")
    
    citizen_data = load_json_file(CITIZEN_INFO_FILE)
    if citizen_data:
        print(f"Successfully loaded citizen data for {len(citizen_data.get('CITIZEN_INFO', []))} citizen types.")
    
    # 2. Load Settlement Hierarchy Data (for classification)
    hierarchy_data = load_json_file(SETTLEMENT_HIERARCHY_FILE)
    if hierarchy_data:
        print(f"Successfully loaded settlement hierarchy data.")
        
    # 3. Load Economic Constants (Quartier sizes, Ratios)
    constants_data = load_json_file(ECONOMIC_CONSTANTS_FILE)
    if constants_data:
        print(f"Successfully loaded economic constants.")

    return {
        "citizens": citizen_data.get("CITIZEN_INFO", []) if citizen_data else [],
        "hierarchy": hierarchy_data.get("SETTLEMENT_HIERARCHY", []) if hierarchy_data else [],
        "constants": constants_data.get("QUARTIER_DEFINITION", {}) if constants_data else {}
    }


def load_afmg_map_data(filepath):
    """Loads the entire AFMG JSON export and extracts the burgs."""
    
    print(f"\n--- Loading AFMG Map Data from {filepath} ---")
    map_data = load_json_file(filepath)
    
    if map_data and 'burgs' in map_data:
        burgs = map_data.get('burgs')
        print(f"Successfully loaded map containing {len(burgs)} burgs.")
        
        print(f"Example burg loaded: {burgs.get('name') if burgs else 'N/A'}")

        return burgs
    
    elif map_data:
        print("Map data loaded, but 'burgs' array was not found. Check AFMG export format.")
        return []
    
    return []


def process_burgs(burgs, config):
    """
    Placeholder for the core simulation logic.
    This is where you would calculate Quartiers and Net Resources 
    (Net Food, Net Gold) for each burg.
    """
    if not burgs or not config.get('citizens'):
        print("\nCannot run simulation: Missing burg or citizen data.")
        return

    print("\n--- Running Burg Economy Calculation (Simulation Placeholder) ---")
    

    min_inhabitants = config['constants'].get('Min_Inhabitants_Per_Quartier')
    
    if min_inhabitants:
        print(f"Using Min Inhabitants per Quartier: {min_inhabitants}")
    
    
    print("Burg processing complete. New economic data would now be appended to burg objects.")
    # The processed burg list, now containing 'NetFood', 'NetGold', etc., 
    # would be used for visualization in the AFMG fork [Conversation History].
    
    return burgs


if __name__ == "__main__":
    
    config_data = load_simulation_data()
    
    burg_list = load_afmg_map_data(AFMG_MAP_FILE)


    if burg_list and config_data['citizens'] and config_data['constants']:
        processed_burgs = process_burgs(burg_list, config_data)
        
        # In a full implementation, you might save this processed data 
        # or load it back into the front-end environment of the AFMG fork.
    else:
        print("\nSystem initialization failed due to missing configuration or map files.")