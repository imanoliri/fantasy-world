from typing import Callable

import numpy as np
import pandas as pd


def summary_data(df: pd.DataFrame, summary_datum_function: Callable) -> pd.DataFrame:
    return summaries_data(df, summary_datum_function).apply(summarize_summaries).T


def summarize_summaries(s: pd.Series) -> pd.Series:
    stat_names = ["Median", "Mean", "Mode", "Min", "Max", "Sum"]
    try:
        return pd.Series(
            [
                s.median(),
                s.mean(),
                ("__".join(str(v) for v in s.mode().iloc[::2].values)),
                s.min(),
                s.max(),
                s.sum(),
            ],
            stat_names,
        ).round(1)
    except:
        sc = s.value_counts()
        return pd.Series(
            [
                np.NaN,
                np.NaN,
                np.NaN,
                sc.idxmin(),
                sc.idxmax(),
                np.NaN,
            ],
            stat_names,
        )


def summaries_data(df: pd.DataFrame, summary_datum_function: Callable) -> pd.DataFrame:
    return df.apply(summary_datum_function, axis=1)
