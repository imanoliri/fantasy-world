import pandas as pd

from study.summaries import summaries_data, summary_data

city_params = [
    ("Population", "Total", "Heads"),
    ("Political", "Characteristics", "Type"),
    ("Infrastructure", "Buildings", "Capital"),
    ("Infrastructure", "Buildings", "Port"),
    ("Infrastructure", "Buildings", "Castle"),
    ("Infrastructure", "Buildings", "Market"),
    ("Infrastructure", "Buildings", "Church"),
    ("Infrastructure", "Buildings", "Shanty Town"),
    ("Infrastructure", "Network", "road"),
]

location_params = [
    ("Nature", "Characteristics", "Biome"),
]  # , river, sea, altitude
size_params = [
    ("Urban", "Area", "Min (ha)"),
    ("Urban", "Area", "Max (ha)"),
    ("Farmland", "Area", "Min (ha)"),
    ("Farmland", "Area", "Max (ha)"),
]
production_params = [
    ("Net", "Total", "Food"),
    ("Net", "Total", "Gold"),
]
parameter_groups_burgs = [
    ("City", city_params),
    ("Location", location_params),
    ("Size", size_params),
    ("Production", production_params),
]


def summary_burgs(df: pd.DataFrame) -> pd.DataFrame:
    return summary_data(df, summary_burg)


def summaries_burgs(df: pd.DataFrame) -> pd.DataFrame:
    return summaries_data(df, summary_burg)


def summary_burg(sb: pd.Series) -> pd.Series:
    return pd.Series(
        [
            *sb.loc[
                [
                    ("Population", "Total", "Heads"),
                    ("Political", "Characteristics", "Type"),
                    ("Nature", "Characteristics", "Biome"),
                ]
            ].values,
            sb.loc[
                [
                    ("Infrastructure", "Buildings", "Capital"),
                    ("Infrastructure", "Buildings", "Port"),
                    ("Infrastructure", "Buildings", "Castle"),
                    ("Infrastructure", "Buildings", "Market"),
                    ("Infrastructure", "Buildings", "Church"),
                    ("Infrastructure", "Buildings", "Shanty Town"),
                ]
            ].sum(),
            *sb.loc[[("Infrastructure", "Network", "road")]].values,
            sb.loc[("Net", "Total", "Food")],
            sb.loc[("Net", "Total", "Gold")],
            sb.loc[
                [("Farmland", "Area", "Min (ha)"), ("Farmland", "Area", "Max (ha)")]
            ].mean(),
            sb.loc[
                [("Urban", "Area", "Min (ha)"), ("Urban", "Area", "Max (ha)")]
            ].mean(),
        ],
        index=[
            "Total_Population",
            "Type",
            "Biome",
            "Buildings",
            "Roads",
            "Production_Food",
            "Production_Gold",
            "Farmland Area",
            "Urban Area",
        ],
    )
