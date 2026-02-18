import pandas as pd
from utils import format_month


def summarize_by_counterparty_per_month(df):
    monthly = df.groupby(["Maand", "Tegenpartij"])["Bedrag"].sum().reset_index()
    monthly.columns = ["Maand", "Tegenpartij", "Netto"]
    monthly["Maand"] = monthly["Maand"].astype(str)
    return monthly


def summarize_monthly_totals(summary_df):
    df = summary_df.copy()
    if "Maand_NL" not in df.columns:
        df["Maand_NL"] = df["Maand"].apply(format_month)

    return (
        df.groupby(["Maand", "Maand_NL"])["Netto"]
        .agg(
            inkomsten=lambda x: x[x > 0].sum(),
            uitgaven=lambda x: x[x < 0].sum(),
            netto="sum",
        )
        .reset_index()
        .sort_values("Maand")
    )


def summarize_monthly_totals_by_label(summary_df):
    return (
        summary_df.groupby(["Maand", "Label"], as_index=False)["Netto"]
        .agg(
            inkomsten=lambda x: x[x > 0].sum(),
            uitgaven=lambda x: x[x < 0].sum(),
            netto="sum",
        )
        .assign(Maand_NL=lambda df: df["Maand"].apply(format_month))
        .sort_values("Maand")
    )


def filter_zakelijkheid(summary_df, zakelijkheid):
    if zakelijkheid == "Zakelijk":
        return summary_df[summary_df["Zakelijk"]]
    elif zakelijkheid == "Niet-zakelijk":
        return summary_df[~summary_df["Zakelijk"]]
    else:
        return summary_df


def aggregate_label_netto(df):
    result = (
        df.copy()
        .groupby(["Label"], as_index=False)["Netto"]
        .sum()
        .sort_values(by="Netto", ascending=False)
    )
    return result


def aggregate_tegenpartij_label_zakelijk(df):
    temp = df[["Tegenpartij", "Netto", "Label", "Zakelijk_NL"]].copy()
    temp = temp.rename(columns={"Zakelijk_NL": "Zakelijk"})
    result = (
        temp.groupby(["Tegenpartij", "Label", "Zakelijk"], as_index=False)["Netto"]
        .sum()
        .sort_values(by="Netto", ascending=False)
    )
    return result


def aggregate_month_netto(df, include_year_totals=False):
    grouped_by_month = df.groupby(["Maand", "Maand_NL"], as_index=False)["Netto"].sum()

    if include_year_totals:
        gb = grouped_by_month.copy()
        gb["Jaar"] = gb["Maand"].str[:4].astype(int)
        year_totals = gb.groupby("Jaar", as_index=False)["Netto"].sum()
        year_totals["Maand_NL"] = "Totaal " + year_totals["Jaar"].astype(str)
        combined = pd.concat([year_totals, gb], ignore_index=True)
        combined["_is_total"] = combined["Maand_NL"].str.startswith("Totaal")
        combined = combined.sort_values(
            by=["Jaar", "_is_total", "Maand"], ascending=[False, False, False]
        ).drop(columns=["_is_total", "Jaar"], errors="ignore")
        display_df = combined[["Maand_NL", "Netto"]].rename(
            columns={"Maand_NL": "Maand"}
        )
        return display_df
    else:
        return (
            grouped_by_month.sort_values(by="Maand", ascending=False)
            .drop(columns="Maand")
            .rename(columns={"Maand_NL": "Maand"})
        )


def aggregate_tegenpartijen_for_label(summary_df, label_value):
    filtered_df = summary_df[summary_df["Label"] == label_value].copy()
    tegenpartij_summary = (
        filtered_df.groupby("Tegenpartij", as_index=False)["Netto"]
        .sum()
        .sort_values(by="Netto", ascending=False)
    )
    total = tegenpartij_summary["Netto"].sum()
    count = len(tegenpartij_summary)
    return tegenpartij_summary, total, count
