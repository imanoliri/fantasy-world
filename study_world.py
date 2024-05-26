import pandas as pd

from plot.plot_independent_params import plot_histograms


def study_burgs(df: pd.DataFrame, plot_dir: str, name: str = "burgs"):

    # Single parameters
    plot_histograms(df, plot_dir=f"{plot_dir}/{name}/parameters")
