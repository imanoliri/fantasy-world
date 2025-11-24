import pandas as pd

burg_models = pd.read_json('burg_models.json')
df_burgs = pd.DataFrame.from_records(burg_models)
df_burgs_net_production = pd.DataFrame.from_records(df_burgs.net_production_burg)




print(f'\tTotal world production:\n{repr(df_burgs_net_production.sum())}')
print(f'\tTotal world quartiers: {df_burgs.nr_quartiers.sum()}')

print(f'Each quartier produces on average: {round(df_burgs_net_production.Net_Food.sum() / df_burgs.nr_quartiers.sum(), 2)}x excess of its own food consumption.')
print(f'Each quartier produces on average: {round(df_burgs_net_production.Net_Gold.sum() / df_burgs.nr_quartiers.sum(), 2)}x excess gold production (consumer quartiers are already discounted).')

