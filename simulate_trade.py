import math

# Configuration
USE_TERRAIN_AND_INFRASTRUCTURE = True

def calculate_distance(burg1, burg2):
    """
    Calculates the distance between two burgs, optionally applying terrain and infrastructure modifiers.
    burg1 and burg2 can be dictionaries (burg objects) or tuples (x, y).
    """
    x1, y1 = burg1['x'], burg1['y']
    x2, y2 = burg2['x'], burg2['y']

    # Base Euclidean distance
    dist = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    # Apply Terrain & Infrastructure Modifiers
    if USE_TERRAIN_AND_INFRASTRUCTURE and isinstance(burg1, dict) and isinstance(burg2, dict):
        multiplier = 1.0
        
        # Sea/Haven (Fastest)
        # If both are havens (ports), sea travel is very efficient
        if burg1.get('haven') and burg2.get('haven'):
            multiplier *= 0.3

        # Roads (Faster)
        # If both have roads, we assume a connection (simplification)
        elif burg1.get('road') and burg2.get('road'):
            multiplier *= 0.5
            
            
        # Mountains (Slower)
        # Height difference is difficult to cross
        multiplier *= (1+ 3 * abs(burg1.get('h', 0) - burg2.get('h', 0)))
            
        # Political Borders (Infrastructure/Safety)
        # Trade within the same state is easier
        if burg1.get('state') == burg2.get('state'):
            multiplier *= 0.8
            
        dist = round(dist*multiplier, 2)
        
    return dist

def simulate_trade(burgs, commodities=['Net_Food', 'Net_Gold']):
    """
    Simulates trade between burgs based on supply and demand using a gravity model.
    """
    print(f"--- Simulating Trade (Terrain & Infrastructure: {'ON' if USE_TERRAIN_AND_INFRASTRUCTURE else 'OFF'}) ---")
    
    trades = []
    
    # Create a lookup for burgs by ID for easy access
    burg_lookup = {b['id']: b for b in burgs}
    
    for commodity in commodities:
        exporters = []
        importers = []
        
        # Identify Exporters and Importers
        for b in burgs:
            net = b.get('net_production_burg', {}).get(commodity, 0)
            if net > 0.01:
                exporters.append({'id': b['id'], 'supply': net, 'original_supply': net})
            elif net < -0.01:
                importers.append({'id': b['id'], 'demand': -net, 'original_demand': -net})
        
        print(f"--- Simulating Trade for {commodity} ---")
        print(f"Exporters: {len(exporters)}, Importers: {len(importers)}")
        
        # Gravity Model Matching
        # For each importer, calculate a score for each exporter: Supply / (Distance^2)
        for importer in importers:
            importer_burg = burg_lookup[importer['id']]
            scores = []
            
            for exporter in exporters:
                if exporter['supply'] <= 0: continue
                
                exporter_burg = burg_lookup[exporter['id']]
                
                # Pass full burg objects to calculate_distance
                dist = calculate_distance(importer_burg, exporter_burg)
                if dist < 1: dist = 1 # Avoid division by zero
                
                score = exporter['supply'] / (dist ** 2)
                scores.append({'exporter': exporter, 'score': score, 'distance': dist})
            
            # Sort by score (highest first)
            scores.sort(key=lambda x: x['score'], reverse=True)
            
            # Fulfill demand
            for match in scores:
                if importer['demand'] <= 0: break
                
                exporter = match['exporter']
                
                # Greedy consumption: take as much as possible from this exporter
                amount = min(importer['demand'], exporter['supply'])
                
                if amount > 0:
                    trades.append({
                        'From_ID': exporter['id'],
                        'To_ID': importer['id'],
                        'Commodity': commodity,
                        'Amount': amount,
                        'Distance': match['distance']
                    })
                    
                    importer['demand'] -= amount
                    exporter['supply'] -= amount
                    
        # Failsafe: If demand remains, try to find ANY exporter with supply (even if distant)
        # Actually, the greedy approach above already checks ALL exporters sorted by score.
        # If demand remains, it means GLOBAL supply is exhausted or unreachable.
        # The previous "failsafe" was just ensuring we check all exporters, which we do now.
        
    return trades
