from enum import Enum
import re
import pandas as pd
import os
import shutil
from glob import glob
from pathlib import Path
from typing import List

from utils import format_zakelijk
import settings
from settings import IGNORED_ACCOUNT_NAMES

CSV_GLOB = "*.csv"


class DataFrameColumn(str, Enum):
    DATE = "date"
    AMOUNT = "Bedrag"
    COUNTERPARTY = "Tegenpartij"
    COUNTERPARTY_IBAN = "iban tegenpartij"
    IBAN = "iban"
    MONTH = "Maand"
    MONTH_NL = "Maand_NL"
    LABEL = "Label"
    BUSINESS = "Zakelijk"
    NOT_BUSINESS = "Niet-zakelijk"
    BUSINESS_NL = "Zakelijk_NL"
    INCOME = "Inkomsten"
    EXPENSE = "Uitgaven"
    NETTO = "Netto"


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
            "Date": DataFrameColumn.DATE.value,
            "Amount (EUR)": DataFrameColumn.AMOUNT.value,
            "Name / Description": DataFrameColumn.COUNTERPARTY.value,
            "Counterparty": DataFrameColumn.COUNTERPARTY_IBAN.value,
            "Account": DataFrameColumn.IBAN.value,
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
            "Datum": DataFrameColumn.DATE.value,
            "Bedrag": DataFrameColumn.AMOUNT.value,
            "Naam tegenpartij": DataFrameColumn.COUNTERPARTY.value,
            "Tegenrekening IBAN/BBAN": DataFrameColumn.COUNTERPARTY_IBAN.value,
            "IBAN/BBAN": DataFrameColumn.IBAN.value,
        },
        "date_format": None,
        "amount_processor": None,
    },
}


def load_csvs(directory):
    files = glob(os.path.join(directory, CSV_GLOB))
    dfs = [
        pd.read_csv(f, sep=",", dtype=str, encoding="latin1").rename(columns=str.strip)
        for f in files
    ]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def _read_single_file(path):
    encodings = ("utf-8", "latin1")
    last_exc = None
    for enc in encodings:
        try:
            return pd.read_csv(path, sep=",", dtype=str, encoding=enc).rename(
                columns=str.strip
            )
        except Exception as e:
            last_exc = e
            continue
    raise last_exc


def _copy_into_data_dir(src_paths, dest_dir=None):
    if dest_dir is None:
        dest_dir = settings.DATA_DIR
    Path(dest_dir).mkdir(parents=True, exist_ok=True)
    out_paths = []
    for src in src_paths:
        srcp = Path(src)
        destp = Path(dest_dir) / srcp.name

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


def import_and_merge(existing_df, file_paths, copy_files=True):
    if not file_paths:
        return existing_df if existing_df is not None else pd.DataFrame()

    read_paths = list(file_paths)
    if copy_files:
        try:
            read_paths = _copy_into_data_dir(file_paths, settings.DATA_DIR)
        except Exception:
            read_paths = list(file_paths)

    cleaned_frames: List[pd.DataFrame] = []
    for p in read_paths:
        try:
            df_raw = _read_single_file(p)
            cleaned = clean_transactions(df_raw)
            if not cleaned.empty:
                cleaned_frames.append(cleaned)
        except Exception:
            continue

    if not cleaned_frames:
        return existing_df if existing_df is not None else pd.DataFrame()

    cleaned = pd.concat(cleaned_frames, ignore_index=True)

    cleaned = cleaned.drop_duplicates(
        subset=[
            DataFrameColumn.DATE.value,
            DataFrameColumn.AMOUNT.value,
            DataFrameColumn.COUNTERPARTY.value,
        ]
    )

    if existing_df is None or existing_df.empty:
        return cleaned

    merged = pd.concat([existing_df, cleaned], ignore_index=True)
    return merged.drop_duplicates(
        subset=[
            DataFrameColumn.DATE.value,
            DataFrameColumn.AMOUNT.value,
            DataFrameColumn.COUNTERPARTY.value,
        ]
    )


def detect_bank_format(df):
    df_cols = set(df.columns)
    for bank_name, cfg in BANK_CONFIGS.items():
        if cfg["required_columns"].issubset(df_cols):
            return bank_name
    return "UNKNOWN"


def ing_amount_processor(df):
    df[DataFrameColumn.AMOUNT.value] = (
        df[DataFrameColumn.AMOUNT.value]
        .str.replace(",", ".")
        .astype(float, errors="ignore")
    )
    debit = df["debit_credit"].str.strip().str.lower() == "debit"
    df.loc[debit, DataFrameColumn.AMOUNT.value] *= -1
    df.drop(columns=["debit_credit"], inplace=True)
    return df


def default_amount_processor(df):
    df[DataFrameColumn.AMOUNT.value] = (
        df[DataFrameColumn.AMOUNT.value]
        .str.replace(",", ".")
        .astype(float, errors="ignore")
    )
    return df


def filter_own_ibans(df):
    if (
        DataFrameColumn.IBAN.value in df.columns
        and DataFrameColumn.COUNTERPARTY_IBAN.value in df.columns
    ):
        own_ibans = df[DataFrameColumn.IBAN.value].dropna().unique()
        df = df[~df[DataFrameColumn.COUNTERPARTY_IBAN.value].isin(own_ibans)]
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
        df[DataFrameColumn.DATE.value] = pd.to_datetime(
            df[DataFrameColumn.DATE.value], format=cfg["date_format"], errors="coerce"
        )
    else:
        df[DataFrameColumn.DATE.value] = pd.to_datetime(
            df[DataFrameColumn.DATE.value], errors="coerce"
        )

    if cfg["amount_processor"]:
        df = cfg["amount_processor"](df)
    else:
        df = default_amount_processor(df)

    df[DataFrameColumn.COUNTERPARTY.value] = df[
        DataFrameColumn.COUNTERPARTY.value
    ].fillna("Onbekend")

    df = df.dropna(subset=[DataFrameColumn.DATE.value, DataFrameColumn.AMOUNT.value])
    df = filter_own_ibans(df)
    df = shared_cleaning(df, DataFrameColumn.COUNTERPARTY.value)

    df[DataFrameColumn.MONTH.value] = df[DataFrameColumn.DATE.value].dt.to_period("M")

    return df.drop_duplicates(
        subset=[
            DataFrameColumn.DATE.value,
            DataFrameColumn.AMOUNT.value,
            DataFrameColumn.COUNTERPARTY.value,
        ]
    )


def merge_and_clean_labels(summary_df, label_df):
    df = summary_df.merge(label_df, on=DataFrameColumn.COUNTERPARTY.value, how="left")
    df[DataFrameColumn.LABEL.value] = (
        df[DataFrameColumn.LABEL.value].fillna("").str.strip().replace("", "geen label")
    )
    df[DataFrameColumn.BUSINESS.value] = (
        df[DataFrameColumn.BUSINESS.value].fillna(False).astype(bool)
    )
    df[DataFrameColumn.BUSINESS_NL.value] = df[DataFrameColumn.BUSINESS.value].apply(
        format_zakelijk
    )
    return df
