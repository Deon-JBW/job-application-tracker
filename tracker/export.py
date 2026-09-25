import pandas as pd

from tracker.db import COLUMNS


def rows_to_df(rows):
    return pd.DataFrame(rows, columns=COLUMNS)


def to_csv_bytes(rows):
    return rows_to_df(rows).to_csv(index=False).encode("utf-8")
