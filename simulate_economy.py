import json
import statistics

CITIZEN_INFO_FILE = "info/citizen_info.json"
SETTLEMENT_INFO_FILE = "info/settlement_info.json"
ECONOMY_INFO_FILE = "info/economy_info.json"

def load_json_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: File not found: {filepath}")
        return None

def load_simulation_config():
    """Loads all external simulation configuration files."""
    
    print("\n--- Loading External Simulation Data ---")
    
    citizen_data = load_json_file(CITIZEN_INFO_FILE)
    if citizen_data:
        print(f"Successfully loaded citizen info.")
    
    settlements_data = load_json_file(SETTLEMENT_INFO_FILE)
    if settlements_data:
        print(f"Successfully loaded settlement info.")
        
    economy_data = load_json_file(ECONOMY_INFO_FILE)
    if economy_data:
        print(f"Successfully loaded economy info.")

    return {
        "citizens": citizen_data if citizen_data else [],
        "settlements": settlements_data if settlements_data else [],
        "economy": economy_data if economy_data else {}
    }

def process_map_data(map_data, config):
    """
    Processes the map data (loaded JSON) and adds simulation data to burgs.
    Returns the list of processed burg models.
    """
    print(f"\n--- Processing Map Data ---")
    
    if not map_data:
        print("Error: No map data provided.")
        return []

    burgs = []
    if 'burgs' in map_data.get('pack', {}):
        burgs = map_data.get('pack').get('burgs')
        print(f"Found {len(burgs)} burgs in map data.")
    else:
        print("Warning: No 'burgs' found in map data pack.")
        return []

    # Filter out empty/invalid burgs (often the first one is a placeholder)
    valid_burgs = [b for b in burgs if isinstance(b, dict) and 'name' in b]
    
    return get_burg_models(valid_burgs, config)

def get_burg_models(burgs, config):
    print("\n--- Processing burgs ---")

    l = len(burgs)
    burg_models = []
    for b, burg in enumerate(burgs):
        # print(f"Processing burg {b + 1} of {l}: {burg.get('name', 'Unknown')}")
        if burg:
            burg_models.append(get_burg_model(burg, config))

    print(f"Burg processing complete. Processed {len(burg_models)} burgs.")
    
    return burg_models

# BURG > GET MODEL
def get_burg_model(burg, config):
    """
    Process a burg. Generate the citizens and quartiers based on the simulation configuration.
    """

    citizens = get_citizens_for_burg(burg, config)
    quartiers = get_quartiers_for_burg(citizens, config)
    # net_production_per_quartier_type = get_net_production_and_consumption_per_quartier_type_for_burg(quartiers, config)
    net_production_burg = get_net_production_for_burg(quartiers, config)
    area_requirements_burg = get_area_requirements_for_burg(burg, config)

    return {
        'id': burg.get('i'), 
        'name': burg.get('name'), 
        'cell': burg.get('cell'), # Important for map mapping
        'x': burg.get('x'), 
        'y': burg.get('y'), 
        'type': burg.get('type'), 
        'state': burg.get('state'),
        'capital': burg.get('capital'), 
        'population': round(burg.get('population')*1000), 
        'citizens': citizens, 
        'nr_quartiers': sum(quartiers.values()), 
        'quartiers': quartiers, 
        'net_production_burg': net_production_burg, 
        'area_requirements_burg': area_requirements_burg
    }


# BURG > CITIZENS
def get_citizens_for_burg(burg, config):
    population = round(burg.get('population')*1000)
    citizen_frequencies_modified = get_citizen_frequencies_for_burg(burg, config)
    total_frequency = sum(citizen_frequencies_modified.values())
    if total_frequency == 0:
        return {}
    citizen_frequencies_normalized = {cn: cf / total_frequency for cn, cf in citizen_frequencies_modified.items()}
    return {citizen_name: round(population * citizen_frequency) for citizen_name, citizen_frequency in citizen_frequencies_normalized.items()}


def get_citizen_frequencies_for_burg(burg, config):
    return {citizen.get('Citizen'): max(0, get_citizen_frequency(citizen, burg)) for citizen in config['citizens']}


def get_citizen_frequency(citizen, burg):
    return citizen.get('Base_Frequency') + get_citizen_burg_type_modifier(citizen, burg) + get_citizen_burg_features_modifier(citizen, burg)


def get_citizen_burg_type_modifier(citizen, burg):
    modifiers = citizen.get('Burg_Type_Frequency_Modifiers')
    return modifiers.get(burg.get('type'), 0)

def get_citizen_burg_features_modifier(citizen, burg):
    modifiers = citizen.get('Burg_Features_Frequency_Modifiers')
    modifiers = {k.lower(): v for k,v in modifiers.items()} # lowercase dictionary of modifiers
    return sum([modifiers.get(feature) for feature, exists in burg.items() if feature.lower() in modifiers and exists > 0])



# BURG > QUARTIERS
def get_quartiers_for_burg(citizens, config):
    quartiers_config = config.get('economy', {}).get('Quartiers')
    if not quartiers_config:
        return {}
    return {citizen_name: get_number_of_quartiers_for_citizen_population(citizen_population, quartiers_config) for citizen_name, citizen_population in citizens.items()}

def get_number_of_quartiers_for_citizen_population(citizen_population, quartiers_config):
    avg_inhabitants = statistics.mean([quartiers_config.get('Min_Inhabitants_Per_Quartier', 100), quartiers_config.get('Max_Inhabitants_Per_Quartier', 1000)])
    if avg_inhabitants == 0: return 0
    return int(citizen_population / avg_inhabitants)



# BURG > PRODUCTION
def get_net_production_for_burg(quartiers, config):
    return get_net_production_from_per_quartier_type(get_net_production_and_consumption_per_quartier_type_for_burg(quartiers, config))


def get_net_production_and_consumption_per_quartier_type_for_burg(quartiers, config):
    return {citizen_name: get_net_production_and_consumption_for_quartier(quartier_number, [citizen for citizen in config.get('citizens') if citizen.get('Citizen') == citizen_name][0]) for citizen_name, quartier_number in quartiers.items()}


def get_net_production_and_consumption_for_quartier(quartier_number, citizen_config):
    return {
            'Net_Food': quartier_number * citizen_config.get('Production_Food', 0) + quartier_number * citizen_config.get('Consumption_Food', 0),
            'Net_Gold': quartier_number * citizen_config.get('Production_Gold', 0) + quartier_number * citizen_config.get('Consumption_Gold', 0)
    }

def get_net_production_from_per_quartier_type(net_production_per_quartier_type):
    return {
            'Net_Food': sum(net_quartier.get('Net_Food') for net_quartier in net_production_per_quartier_type.values()),
            'Net_Gold': sum(net_quartier.get('Net_Gold') for net_quartier in net_production_per_quartier_type.values())
    }


# BURG > AREA REQUIREMENTS
def get_area_requirements_for_burg(burg, config):
    population = round(burg.get('population')*1000)
    area_requirements = config.get('economy', {}).get('Area_Requirements')
    if not area_requirements:
        return {}
        
    return {
        "Farmland_to_Feed_Burg_ha_Min": round(population * area_requirements.get('Farmland_to_Feed_Person_ha_Min', 0)),
        "Farmland_to_Feed_Burg_ha_Max": round(population * area_requirements.get('Farmland_to_Feed_Person_ha_Max', 0)),
        "Urban_Area_Burg_ha_Min": round(population * area_requirements.get('Urban_Area_Per_Person_m2_Min', 0) / 10_000),
        "Urban_Area_Burg_ha_Max": round(population * area_requirements.get('Urban_Area_Per_Person_m2_Max', 0) / 10_000),
    }
    

def get_area_requirement_for_citizen_quartiers(citizen_name, quartier_number, config):
    citizen_config = [citizen for citizen in config.get('citizens') if citizen.get('Citizen') == citizen_name][0]
    area_per_quartier = citizen_config.get('Area_Requirement_ha_Per_Quartier', 0)
    return quartier_number * area_per_quartier
