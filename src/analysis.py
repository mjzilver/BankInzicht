from data_loader import DataFrameColumn
import pandas as pd
from utils import format_month
from constants import Zakelijkheid


def summarize_by_counterparty_per_month(df):
    monthly = (
        df.groupby([DataFrameColumn.MONTH.value, DataFrameColumn.COUNTERPARTY.value])[
            DataFrameColumn.AMOUNT.value
        ]
        .sum()
        .reset_index()
    )
    monthly.columns = [
        DataFrameColumn.MONTH.value,
        DataFrameColumn.COUNTERPARTY.value,
        DataFrameColumn.NETTO.value,
    ]
    monthly[DataFrameColumn.MONTH.value] = monthly[DataFrameColumn.MONTH.value].astype(
        str
    )
    return monthly


def summarize_monthly_totals(summary_df):
    df = summary_df.copy()
    if DataFrameColumn.MONTH_NL.value not in df.columns:
        df[DataFrameColumn.MONTH_NL.value] = df[DataFrameColumn.MONTH.value].apply(
            format_month
        )

    return (
        df.groupby([DataFrameColumn.MONTH.value, DataFrameColumn.MONTH_NL.value])[
            DataFrameColumn.NETTO.value
        ]
        .agg(
            **{
                DataFrameColumn.INCOME.value: lambda x: x[x > 0].sum(),
                DataFrameColumn.EXPENSE.value: lambda x: x[x < 0].sum(),
                DataFrameColumn.NETTO.value: "sum",
            }
        )
        .reset_index()
        .sort_values(DataFrameColumn.MONTH.value)
    )


def summarize_monthly_totals_by_label(summary_df):
    return (
        summary_df.groupby(
            [DataFrameColumn.MONTH.value, DataFrameColumn.LABEL.value], as_index=False
        )[DataFrameColumn.NETTO.value]
        .agg(
            **{
                DataFrameColumn.INCOME.value: lambda x: x[x > 0].sum(),
                DataFrameColumn.EXPENSE.value: lambda x: x[x < 0].sum(),
                DataFrameColumn.NETTO.value: "sum",
            }
        )
        .assign(
            **{
                DataFrameColumn.MONTH_NL.value: lambda df: df[
                    DataFrameColumn.MONTH.value
                ].apply(format_month)
            }
        )
        .sort_values(DataFrameColumn.MONTH.value)
    )


def filter_zakelijkheid(summary_df, zakelijkheid):
    if zakelijkheid == Zakelijkheid.BUSINESS.value:
        return summary_df[summary_df[DataFrameColumn.BUSINESS.value]]
    elif zakelijkheid == Zakelijkheid.NON_BUSINESS.value:
        return summary_df[~summary_df[DataFrameColumn.BUSINESS.value]]
    else:
        return summary_df


def aggregate_label_netto(df):
    result = (
        df.copy()
        .groupby([DataFrameColumn.LABEL.value], as_index=False)[
            DataFrameColumn.NETTO.value
        ]
        .sum()
        .sort_values(by=DataFrameColumn.NETTO.value, ascending=False)
    )
    return result


def aggregate_tegenpartij_label_zakelijk(df):
    temp = df[
        [
            DataFrameColumn.COUNTERPARTY.value,
            DataFrameColumn.NETTO.value,
            DataFrameColumn.LABEL.value,
            DataFrameColumn.BUSINESS_NL.value,
        ]
    ].copy()
    temp = temp.rename(
        columns={DataFrameColumn.BUSINESS_NL.value: DataFrameColumn.BUSINESS.value}
    )
    result = (
        temp.groupby(
            [
                DataFrameColumn.COUNTERPARTY.value,
                DataFrameColumn.LABEL.value,
                DataFrameColumn.BUSINESS.value,
            ],
            as_index=False,
        )[DataFrameColumn.NETTO.value]
        .sum()
        .sort_values(by=DataFrameColumn.NETTO.value, ascending=False)
    )
    return result


def aggregate_month_netto(df, include_year_totals=False):
    grouped_by_month = df.groupby(
        [DataFrameColumn.MONTH.value, DataFrameColumn.MONTH_NL.value], as_index=False
    )[DataFrameColumn.NETTO.value].sum()

    if include_year_totals:
        JAAR_COL = "Jaar"
        IS_TOTAL_COL = "_is_total"
        gb = grouped_by_month.copy()
        gb[JAAR_COL] = gb[DataFrameColumn.MONTH.value].str[:4].astype(int)
        year_totals = gb.groupby(JAAR_COL, as_index=False)[
            DataFrameColumn.NETTO.value
        ].sum()
        year_totals[DataFrameColumn.MONTH_NL.value] = "Totaal " + year_totals[
            JAAR_COL
        ].astype(str)
        combined = pd.concat([year_totals, gb], ignore_index=True)
        combined[IS_TOTAL_COL] = combined[
            DataFrameColumn.MONTH_NL.value
        ].str.startswith("Totaal")
        combined = combined.sort_values(
            by=[JAAR_COL, IS_TOTAL_COL, DataFrameColumn.MONTH.value],
            ascending=[False, False, False],
        ).drop(columns=[IS_TOTAL_COL, JAAR_COL], errors="ignore")
        display_df = combined[
            [DataFrameColumn.MONTH_NL.value, DataFrameColumn.NETTO.value]
        ].rename(columns={DataFrameColumn.MONTH_NL.value: DataFrameColumn.MONTH.value})
        return display_df
    else:
        return (
            grouped_by_month.sort_values(
                by=DataFrameColumn.MONTH.value, ascending=False
            )
            .drop(columns=DataFrameColumn.MONTH.value)
            .rename(
                columns={DataFrameColumn.MONTH_NL.value: DataFrameColumn.MONTH.value}
            )
        )


def aggregate_tegenpartijen_for_label(summary_df, label_value):
    filtered_df = summary_df[
        summary_df[DataFrameColumn.LABEL.value] == label_value
    ].copy()
    tegenpartij_summary = (
        filtered_df.groupby(DataFrameColumn.COUNTERPARTY.value, as_index=False)[
            DataFrameColumn.NETTO.value
        ]
        .sum()
        .sort_values(by=DataFrameColumn.NETTO.value, ascending=False)
    )
    total = tegenpartij_summary[DataFrameColumn.NETTO.value].sum()
    count = len(tegenpartij_summary)
    return tegenpartij_summary, total, count
