import pandas as pd

burgs = pd.read_json('data/burgs.json')
df_burgs = pd.DataFrame.from_records(burgs)

df_burgs_net_production = pd.DataFrame.from_records(df_burgs.net_production_burg)
df_burgs_net_production = pd.concat([df_burgs[['name','type','capital','nr_quartiers']], df_burgs_net_production], axis=1)
df_burgs_net_production.sort_values(by='Net_Food', ascending=False)
df_burgs_net_production.to_csv('data/burgs_net_production.csv')

df_burgs.sort_values(by='nr_quartiers', ascending=False)
df_burgs.to_csv('data/burgs.csv')

print(f'\tTotal world production:\n{repr(df_burgs_net_production.loc[:,['Net_Food', 'Net_Gold']].sum().to_dict())}')
print(f'\tTotal world quartiers: {df_burgs.nr_quartiers.sum()}')

print(f'Each quartier produces on average: {round(df_burgs_net_production.Net_Food.sum() / df_burgs.nr_quartiers.sum(), 2)}x excess of its own food consumption.')
print(f'Each quartier produces on average: {round(df_burgs_net_production.Net_Gold.sum() / df_burgs.nr_quartiers.sum(), 2)}x excess gold production (consumer quartiers are already discounted).')

