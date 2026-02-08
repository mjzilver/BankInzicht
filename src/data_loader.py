import re
import pandas as pd
import os
from glob import glob

from utils import format_zakelijk
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


def load_csvs(directory):
    files = glob(os.path.join(directory, CSV_GLOB))
    dfs = [
        pd.read_csv(f, sep=",", dtype=str, encoding="latin1").rename(columns=str.strip)
        for f in files
    ]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


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
