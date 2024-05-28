import numpy as np
import pandas as pd

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
    return summaries_burgs(df).apply(get_summary_burgs_parameter).T


def get_summary_burgs_parameter(s: pd.Series) -> pd.Series:
    stat_names = ["Median", "Mean", "Mode", "Min", "Max"]
    try:
        return pd.Series(
            [
                s.median(),
                s.mean(),
                ("__".join(str(v) for v in s.mode().iloc[::2].values)),
                s.min(),
                s.max(),
            ],
            stat_names,
        ).round(1)
    except:
        sc = s.value_counts()
        return pd.Series([np.NaN, np.NaN, np.NaN, sc.idxmin(), sc.idxmax()], stat_names)


def summaries_burgs(df: pd.DataFrame) -> pd.DataFrame:
    return df.apply(summary_burg, axis=1)


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
