import json
import statistics


CITIZEN_INFO_FILE = "info/citizen_info.json"
SETTLEMENT_INFO_FILE = "info/settlement_info.json"
ECONOMY_INFO_FILE = "info/economy_info.json"

AFMG_MAP_FILE = "fantasy_map/Montreia Full 2024-05-23-10-01.json" 

def load_json_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_to_json_file(data, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        


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


def get_burgs_from_afmg_map_data(filepath):
    """Loads the entire AFMG JSON export and extracts the burgs."""
    
    print(f"\n--- Loading AFMG Map Data from {filepath} ---")
    map_data = load_json_file(filepath)
    
    if map_data:
        if 'burgs' in map_data.get('pack'):
            burgs = map_data.get('pack').get('burgs')
            print(f"Successfully loaded map containing {len(burgs)} burgs.")
        
            print(f"Example burg loaded: {burgs[1] if burgs else 'N/A'}")

        return burgs
    



def get_burg_models(burgs, config):
    print("\n--- Processing burgs ---")

    l = len(burgs)
    burg_models = []
    for b, burg in enumerate(burgs):
        print(f"Processing burg {b + 1} of {l}: {burg.get('name', 'Unknown')}")
        if burg:
            burg_models.append(get_burg_model(burg, config))

    print("Burg processing complete. Info added to burg objects.")
    
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

    return {'id': burg.get('i'), 'name': burg.get('name'), 'x': burg.get('x'), 'y': burg.get('y'), 'type': burg.get('type'), 'capital': burg.get('capital'), 'population': round(burg.get('population')*1000), 'citizens': citizens, 'nr_quartiers': sum(quartiers.values()), 'quartiers': quartiers, 'net_production_burg': net_production_burg, 'area_requirements_burg': area_requirements_burg}


# BURG > CITIZENS
def get_citizens_for_burg(burg, config):
    population = round(burg.get('population')*1000)
    citizen_frequencies_modified = get_citizen_frequencies_for_burg(burg, config)
    total_frequency = sum(citizen_frequencies_modified.values())
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
    return {citizen_name: get_number_of_quartiers_for_citizen_population(citizen_population, config.get('economy').get('Quartiers')) for citizen_name, citizen_population in citizens.items()}

def get_number_of_quartiers_for_citizen_population(citizen_population, quartiers_config):
    return int(citizen_population / statistics.mean([quartiers_config.get('Min_Inhabitants_Per_Quartier'), quartiers_config.get('Max_Inhabitants_Per_Quartier')]))



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
    area_requirements = config.get('economy').get('Area_Requirements')
    return {
        "Farmland_to_Feed_Burg_ha_Min": round(population * area_requirements.get('Farmland_to_Feed_Person_ha_Min')),
        "Farmland_to_Feed_Burg_ha_Max": round(population * area_requirements.get('Farmland_to_Feed_Person_ha_Max')),
        "Urban_Area_Burg_ha_Min": round(population * area_requirements.get('Urban_Area_Per_Person_m2_Min') / 10_000),
        "Urban_Area_Burg_ha_Max": round(population * area_requirements.get('Urban_Area_Per_Person_m2_Max') / 10_000),
    }
    

def get_area_requirement_for_citizen_quartiers(citizen_name, quartier_number, config):
    citizen_config = [citizen for citizen in config.get('citizens') if citizen.get('Citizen') == citizen_name][0]
    area_per_quartier = citizen_config.get('Area_Requirement_ha_Per_Quartier', 0)
    return quartier_number * area_per_quartier


if __name__ == "__main__":
    
    simulation_config = load_simulation_config()
    
    burg_list = get_burgs_from_afmg_map_data(AFMG_MAP_FILE)

    burgs = get_burg_models(burg_list, simulation_config)

    write_to_json_file(burgs, 'data/burgs.json')
