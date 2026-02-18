import os
from glob import glob
from typing import Tuple

import pandas as pd

import settings
from analysis import summarize_by_counterparty_per_month
from data_loader import (
    DataFrameColumn,
    clean_transactions,
    import_and_merge,
    load_csvs,
    merge_and_clean_labels,
)
from label_db import get_labels
from utils import format_month


# Returns tuple of (transactions_df, summary_df)
def load_initial_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    data_dir = settings.DATA_DIR
    files = glob(os.path.join(data_dir, "*.csv")) if os.path.exists(data_dir) else []

    if files:
        try:
            raw = load_csvs(data_dir)
            df = clean_transactions(raw) if not raw.empty else pd.DataFrame()
        except Exception:
            try:
                df = import_and_merge(None, files, copy_files=False)
            except Exception:
                df = pd.DataFrame()
    else:
        df = pd.DataFrame()

    summary_df = pd.DataFrame()
    if not df.empty:
        summary_df = summarize_by_counterparty_per_month(df)
        summary_df[DataFrameColumn.MONTH_NL.value] = summary_df[
            DataFrameColumn.MONTH.value
        ].apply(format_month)
        summary_df = summary_df.sort_values(
            by=[DataFrameColumn.MONTH.value, DataFrameColumn.NETTO.value],
            ascending=[True, False],
        )
        summary_df = merge_and_clean_labels(summary_df, get_labels())

    return df, summary_df


# Returns tuple of (transactions_df, summary_df)
def import_files(
    existing_df, file_paths, copy_files=True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = import_and_merge(
        existing_df if existing_df is not None and not existing_df.empty else None,
        file_paths,
        copy_files=copy_files,
    )

    summary_df = pd.DataFrame()
    if not df.empty:
        summary_df = summarize_by_counterparty_per_month(df)
        summary_df[DataFrameColumn.MONTH_NL.value] = summary_df[
            DataFrameColumn.MONTH.value
        ].apply(format_month)
        summary_df = merge_and_clean_labels(summary_df, get_labels())

    return df, summary_df
