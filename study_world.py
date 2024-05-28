import pathlib

import pandas as pd

from plot.plot_independent_params import plot_histograms, summaries_burgs, summary_burgs
from plot.plot_related_params import plot_pairplot


def study_burgs(df: pd.DataFrame, plot_dir: str, name: str = "burgs"):

    # Single parameters
    df_summary = summary_burgs(df).T
    fpath = f"{plot_dir}/{name}/parameters/burgs_summary.csv"
    pathlib.Path(fpath).parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(fpath)

    df_summaries = summaries_burgs(df)
    plot_histograms(df, plot_dir=f"{plot_dir}/{name}/parameters")
    plot_histograms(df_summaries, plot_dir=f"{plot_dir}/{name}/parameters_summaries")

    # Related parameters
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
        ("Farmland", "Area", "Min (ha)"),
        ("Farmland", "Area", "Max (ha)"),
    ]
    production_params = [
        ("Net", "Total", "Food"),
        ("Net", "Total", "Gold"),
    ]
    parameter_groups = [
        ("City", city_params),
        ("Location", location_params),
        ("Size", size_params),
        ("Production", production_params),
    ]

    for group_1, params_1 in parameter_groups:
        for group_2, params_2 in parameter_groups:
            pair_name = f"{group_1} vs {group_2}"
            pair_name_str = pair_name.replace(" ", "_")
            plot_pairplot(
                df,
                plot_dir=f"{plot_dir}/{name}/parameter_relations",
                name=pair_name_str,
                x_vars=params_1,
                y_vars=params_2,
            )

    # Repeat by kingdom, continent etc
