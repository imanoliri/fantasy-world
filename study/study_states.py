import pandas as pd

from study.study_burgs import summaries_burgs
from study.study_cells import summaries_cells
from study.summaries import summaries_data, summary_data

location_params = ["cells", "center"]
identification_params = ["name", "color", "type", "culture"]
population_params = [
    "burgs",
    "provinces",
    "urban",
    "rural",
]
relations_params = ["neighbors", "diplomacy", "expansionism", "campaigns", "alert"]
parameter_groups_states = [
    ("Identification", identification_params),
    ("Location", location_params),
    ("Population", population_params),
    ("Relations", relations_params),
]


def extend_states(
    states: pd.DataFrame, burgs: pd.DataFrame, cells: pd.DataFrame
) -> pd.DataFrame:
    burgs_sum_by_state = burgs.groupby("state").sum()
    burgs_summaries_sum_by_state = summaries_burgs(burgs).groupby("state").sum()
    cells_summaries_sum_by_state = summaries_cells(cells).groupby("state").sum()

    # Add relevant infos from more general to more specific
    states_extended = states.copy()

    # BURGS
    states_extended = pd.merge(
        states_extended,
        burgs_summaries_sum_by_state,
        how="left",
        left_on="name",
        right_on="state",
    )
    states_extended = pd.merge(
        states_extended,
        burgs_sum_by_state.Infrastructure.Buildings,
        how="left",
        left_on="name",
        right_on="state",
    )
    states_extended = pd.merge(
        states_extended,
        burgs_sum_by_state.Citizens.Nr,
        how="left",
        left_on="name",
        right_on="state",
    )

    # CELLS
    params_cells_old = ["area", "biome", "religion", "culture", "haven", "harbor"]
    params_cells = [f"{p}_cells" for p in params_cells_old]
    states_extended = pd.merge(
        states_extended,
        cells_summaries_sum_by_state.rename(
            columns=dict(zip(params_cells_old, params_cells))
        ).loc[:, params_cells],
        how="left",
        left_on="i",
        right_on="state",
    )

    return states_extended


def summary_states(df: pd.DataFrame) -> pd.DataFrame:
    return summary_data(df, summary_state)


def summaries_states(df: pd.DataFrame) -> pd.DataFrame:
    return summaries_data(df, summary_state)


def summary_state(sb: pd.Series) -> pd.Series:
    location_params = ["cells", "area", "center"]  ## add cells by biome
    identification_params = ["name", "color", "type", "culture"]
    population_params = [
        "burgs",
        "provinces",
        "urban",
        "rural",
    ]
    relations_params = ["neighbors", "diplomacy", "expansionism", "campaigns", "alert"]
    parameter_groups_states = [
        ("Identification", identification_params),
        ("Location", location_params),
        ("Population", population_params),
        ("Relations", relations_params),
    ]

    all_params = [v for name, params in parameter_groups_states for v in params]
    return sb.loc[all_params]
