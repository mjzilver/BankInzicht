import os
from glob import glob
import pandas as pd
from typing import Tuple, Optional, List

import settings
from data_loader import (
    load_csvs,
    clean_transactions,
    merge_and_clean_labels,
    import_and_merge,
)
from analysis import summarize_by_counterparty_per_month
from utils import format_month
from label_db import get_labels

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
        summary_df["Maand_NL"] = summary_df["Maand"].apply(format_month)
        summary_df = summary_df.sort_values(by=["Maand", "Netto"], ascending=[True, False])
        summary_df = merge_and_clean_labels(summary_df, get_labels())

    return df, summary_df


def import_files(existing_df: Optional[pd.DataFrame], file_paths: List[str], copy_files: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = import_and_merge(existing_df if existing_df is not None and not existing_df.empty else None, file_paths, copy_files=copy_files)

    summary_df = pd.DataFrame()
    if not df.empty:
        summary_df = summarize_by_counterparty_per_month(df)
        summary_df["Maand_NL"] = summary_df["Maand"].apply(format_month)
        summary_df = merge_and_clean_labels(summary_df, get_labels())

    return df, summary_df
