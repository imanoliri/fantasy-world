import json
import math
import pandas as pd

BURGS_FILE = 'data/burgs.json'
OUTPUT_FILE = 'data/trade_routes.csv'

def load_burgs():
    with open(BURGS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_distance(b1, b2):
    return math.sqrt((b1['x'] - b2['x'])**2 + (b1['y'] - b2['y'])**2)

def simulate_trade(burgs):
    trades = []
    
    # Commodities to trade
    commodities = ['Net_Food', 'Net_Gold']
    
    for commodity in commodities:
        print(f"\n--- Simulating Trade for {commodity} ---")
        
        # Separate into Exporters and Importers
        exporters = []
        importers = []
        
        for b in burgs:
            net = b.get('net_production_burg', {}).get(commodity, 0)
            if net > 0.01: # Threshold to avoid floating point noise
                # Create a mutable copy for tracking remaining supply
                exporters.append({'id': b['id'], 'name': b['name'], 'x': b['x'], 'y': b['y'], 'supply': net, 'original_supply': net})
            elif net < -0.01:
                # Create a mutable copy for tracking remaining demand
                importers.append({'id': b['id'], 'name': b['name'], 'x': b['x'], 'y': b['y'], 'demand': -net, 'original_demand': -net})
        
        print(f"Exporters: {len(exporters)}, Importers: {len(importers)}")
        
        # Match Importers to Exporters
        for importer in importers:
            if importer['demand'] <= 0: continue
            
            # Calculate score for all exporters: Supply / Distance^2
            # We want high supply and low distance.
            # Gravity model: Interaction ~ (Mass1 * Mass2) / Distance^2
            # Here Mass1 is Demand, Mass2 is Supply.
            # Since we are iterating per importer, Mass1 is constant for the sort.
            # So we sort by Supply / Distance^2.
            
            candidates = []
            for exporter in exporters:
                if exporter['supply'] <= 0: continue
                
                dist = calculate_distance(importer, exporter)
                if dist < 1.0: dist = 1.0 # Avoid division by zero or huge spikes
                
                score = exporter['supply'] / (dist ** 2)
                candidates.append((score, dist, exporter))
            
            # Sort by score descending
            candidates.sort(key=lambda x: x[0], reverse=True)
            
            # Fulfill demand
            for score, dist, exporter in candidates:
                if importer['demand'] <= 0: break
                
                amount = min(importer['demand'], exporter['supply'])
                
                trades.append({
                    'From_ID': exporter['id'],
                    'From_Name': exporter['name'],
                    'To_ID': importer['id'],
                    'To_Name': importer['name'],
                    'Commodity': commodity,
                    'Amount': round(amount, 2),
                    'Distance': round(dist, 2)
                })
                
                # Update states
                importer['demand'] -= amount
                exporter['supply'] -= amount
                
    return trades

if __name__ == "__main__":
    print("Loading burgs...")
    burgs = load_burgs()
    
    print(f"Loaded {len(burgs)} burgs.")
    
    trades = simulate_trade(burgs)
    
    print(f"\nTotal trades generated: {len(trades)}")
    
    if trades:
        df = pd.DataFrame(trades)
        df.to_csv(OUTPUT_FILE, index=False)
        print(f"Trade routes saved to {OUTPUT_FILE}")
        
        # Summary
        print("\nTop 5 Trade Routes by Volume:")
        print(df.sort_values('Amount', ascending=False).head(5)[['From_Name', 'To_Name', 'Commodity', 'Amount']])
        
        print("\nTotal Volume per Commodity:")
        print(df.groupby('Commodity')['Amount'].sum())
    else:
        print("No trades occurred.")
