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
