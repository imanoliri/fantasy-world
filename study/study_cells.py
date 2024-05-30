import pandas as pd

from study.summaries import summaries_data, summary_data

location_params = [
    "c",
    "p",
    "g",
    "h",
    "area",
    "biome",
]
property_params = ["state", "religion", "province", "culture"]
characteristics = ["burg", "road", "crossroad", "haven", "harbor"]

parameter_groups_cells = [
    ("Location", location_params),
    ("Property", property_params),
    ("Infrastructure", characteristics),
]


def summary_cells(df: pd.DataFrame) -> pd.DataFrame:
    return summary_data(df, summary_cell)


def summaries_cells(df: pd.DataFrame) -> pd.DataFrame:
    return summaries_data(df, summary_cell)


def summary_cell(sb: pd.Series) -> pd.Series:
    all_params = [v for name, params in parameter_groups_cells for v in params]
    return sb.loc[all_params]
