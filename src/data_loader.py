import re
import pandas as pd
import os
import shutil
from glob import glob
from pathlib import Path
from typing import List, Optional

from utils import format_zakelijk
import settings
from settings import IGNORED_ACCOUNT_NAMES

CSV_GLOB = "*.csv"

COMMON_COLS = {
    "date": "date",
    "amount": "Bedrag",
    "counterparty": "Tegenpartij",
    "counterparty_iban": "iban tegenpartij",
    "iban": "iban",
    "month": "Maand",
    "month_nl": "Maand_NL",
    "label": "Label",
    "business": "Zakelijk",
    "not_business": "Niet-zakelijk",
    "business_nl": "Zakelijk_NL",
    "net_amount": "Netto",
    "income": "Inkomsten",
    "expense": "Uitgaven",
}

BANK_CONFIGS = {
    "ING": {
        "required_columns": {
            "Date",
            "Amount (EUR)",
            "Name / Description",
            "Counterparty",
            "Debit/credit",
            "Account",
        },
        "rename_map": {
            "Date": COMMON_COLS["date"],
            "Amount (EUR)": COMMON_COLS["amount"],
            "Name / Description": COMMON_COLS["counterparty"],
            "Counterparty": COMMON_COLS["counterparty_iban"],
            "Account": COMMON_COLS["iban"],
            "Debit/credit": "debit_credit",
        },
        "date_format": "%Y%m%d",
        "amount_processor": lambda df: ing_amount_processor(df),
    },
    "RABO": {
        "required_columns": {
            "Datum",
            "Bedrag",
            "Naam tegenpartij",
            "Tegenrekening IBAN/BBAN",
            "IBAN/BBAN",
        },
        "rename_map": {
            "Datum": COMMON_COLS["date"],
            "Bedrag": COMMON_COLS["amount"],
            "Naam tegenpartij": COMMON_COLS["counterparty"],
            "Tegenrekening IBAN/BBAN": COMMON_COLS["counterparty_iban"],
            "IBAN/BBAN": COMMON_COLS["iban"],
        },
        "date_format": None,
        "amount_processor": None,
    },
}

# TODO: allow mixed formats in one directory, or detect per-file instead of per-directory
def load_csvs(directory):
    files = glob(os.path.join(directory, CSV_GLOB))
    dfs = [
        pd.read_csv(f, sep=",", dtype=str, encoding="latin1").rename(columns=str.strip)
        for f in files
    ]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def _read_single_file(path: str) -> pd.DataFrame:
    """Read a single CSV/TSV file with an encoding fallback and return a DataFrame.

    Keeps dtype as str on read to allow downstream cleaning.
    """
    encodings = ("utf-8", "latin1")
    last_exc = None
    for enc in encodings:
        try:
            return pd.read_csv(path, sep=",", dtype=str, encoding=enc).rename(columns=str.strip)
        except Exception as e:
            last_exc = e
            continue
    raise last_exc


def load_files(file_paths: List[str]) -> pd.DataFrame:
    """Load multiple files (paths) and return a concatenated DataFrame.

    This is a per-file import helper intended for the import button / drag-drop flows.
    """
    dfs = []
    for p in file_paths:
        try:
            dfs.append(_read_single_file(p))
        except Exception:
            # skip unreadable files; caller should handle reporting
            continue
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def _copy_into_data_dir(src_paths: List[str], dest_dir: Optional[str] = None) -> List[str]:
    """Copy source files into dest_dir (defaults to settings.DATA_DIR) and return new paths."""
    if dest_dir is None:
        dest_dir = settings.DATA_DIR
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    out_paths = []
    for src in src_paths:
        srcp = Path(src)
        destp = Path(dest_dir) / srcp.name
        # avoid overwriting existing files
        if destp.exists():
            stem = destp.stem
            suffix = destp.suffix
            i = 1
            while True:
                candidate = Path(dest_dir) / f"{stem}_{i}{suffix}"
                if not candidate.exists():
                    destp = candidate
                    break
                i += 1
        shutil.copy2(srcp, destp)
        out_paths.append(str(destp))
    return out_paths


def import_and_merge(
    existing_df: Optional[pd.DataFrame], file_paths: List[str], copy_files: bool = True
) -> pd.DataFrame:
    """Import files, optionally copy them into `settings.DATA_DIR`, clean and merge with existing_df.

    - Reads files with `load_files`
    - If `copy_files`, copies originals into `settings.DATA_DIR`
    - Runs `clean_transactions` on the concatenated new data
    - Concatenates with `existing_df` (if any) and drops duplicates using the
      same subset used by `clean_transactions`
    """
    if not file_paths:
        return existing_df if existing_df is not None else pd.DataFrame()


    read_paths = list(file_paths)
    if copy_files:
        try:
            read_paths = _copy_into_data_dir(file_paths, settings.DATA_DIR)
        except Exception:
            # if copy fails, continue and read in-place
            read_paths = list(file_paths)


    cleaned_frames: List[pd.DataFrame] = []
    for p in read_paths:
        try:
            df_raw = _read_single_file(p)
            cleaned = clean_transactions(df_raw)
            if not cleaned.empty:
                cleaned_frames.append(cleaned)
        except Exception:
            # skip files that fail to read or clean; caller/UI should report if needed
            continue

    if not cleaned_frames:
        return existing_df if existing_df is not None else pd.DataFrame()

    cleaned = pd.concat(cleaned_frames, ignore_index=True)
    # always drop duplicates from the newly imported data
    cleaned = cleaned.drop_duplicates(
        subset=[COMMON_COLS["date"], COMMON_COLS["amount"], COMMON_COLS["counterparty"]]
    )

    if existing_df is None or existing_df.empty:
        return cleaned

    merged = pd.concat([existing_df, cleaned], ignore_index=True)
    return merged.drop_duplicates(
        subset=[COMMON_COLS["date"], COMMON_COLS["amount"], COMMON_COLS["counterparty"]]
    )


def detect_bank_format(df):
    df_cols = set(df.columns)
    for bank_name, cfg in BANK_CONFIGS.items():
        if cfg["required_columns"].issubset(df_cols):
            return bank_name
    return "UNKNOWN"


def ing_amount_processor(df):
    df[COMMON_COLS["amount"]] = (
        df[COMMON_COLS["amount"]].str.replace(",", ".").astype(float, errors="ignore")
    )
    debit = df["debit_credit"].str.strip().str.lower() == "debit"
    df.loc[debit, COMMON_COLS["amount"]] *= -1
    df.drop(columns=["debit_credit"], inplace=True)
    return df


def default_amount_processor(df):
    df[COMMON_COLS["amount"]] = (
        df[COMMON_COLS["amount"]].str.replace(",", ".").astype(float, errors="ignore")
    )
    return df


def filter_own_ibans(df):
    if (
        COMMON_COLS["iban"] in df.columns
        and COMMON_COLS["counterparty_iban"] in df.columns
    ):
        own_ibans = df[COMMON_COLS["iban"]].dropna().unique()
        df = df[~df[COMMON_COLS["counterparty_iban"]].isin(own_ibans)]
    return df


def shared_cleaning(df, counterparty_col):
    if IGNORED_ACCOUNT_NAMES:
        pattern = "|".join(map(re.escape, IGNORED_ACCOUNT_NAMES))
        df = df[~df[counterparty_col].str.contains(pattern, case=False, na=False)]
    return df


def clean_transactions(df):
    if df.empty:
        return df

    bank_type = detect_bank_format(df)
    if bank_type == "UNKNOWN":
        raise ValueError("Unsupported bank format detected.")
    cfg = BANK_CONFIGS[bank_type]

    df = df.rename(columns=cfg["rename_map"])

    if cfg["date_format"]:
        df[COMMON_COLS["date"]] = pd.to_datetime(
            df[COMMON_COLS["date"]], format=cfg["date_format"], errors="coerce"
        )
    else:
        df[COMMON_COLS["date"]] = pd.to_datetime(
            df[COMMON_COLS["date"]], errors="coerce"
        )

    if cfg["amount_processor"]:
        df = cfg["amount_processor"](df)
    else:
        df = default_amount_processor(df)

    df[COMMON_COLS["counterparty"]] = df[COMMON_COLS["counterparty"]].fillna("Onbekend")

    df = df.dropna(subset=[COMMON_COLS["date"], COMMON_COLS["amount"]])
    df = filter_own_ibans(df)
    df = shared_cleaning(df, COMMON_COLS["counterparty"])

    df[COMMON_COLS["month"]] = df[COMMON_COLS["date"]].dt.to_period("M")

    return df.drop_duplicates(
        subset=[COMMON_COLS["date"], COMMON_COLS["amount"], COMMON_COLS["counterparty"]]
    )


def merge_and_clean_labels(summary_df, label_df):
    df = summary_df.merge(label_df, on=COMMON_COLS["counterparty"], how="left")
    df[COMMON_COLS["label"]] = (
        df[COMMON_COLS["label"]].fillna("").str.strip().replace("", "geen label")
    )
    df[COMMON_COLS["business"]] = df[COMMON_COLS["business"]].fillna(False).astype(bool)
    df[COMMON_COLS["business_nl"]] = df[COMMON_COLS["business"]].apply(format_zakelijk)
    return df
