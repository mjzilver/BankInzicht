import pandas as pd
from src.data_loader import DataFrameColumn

from analysis import (
    aggregate_label_netto,
    aggregate_tegenpartij_label_zakelijk,
    aggregate_month_netto,
    aggregate_tegenpartijen_for_label,
    summarize_by_counterparty_per_month,
    summarize_monthly_totals,
)


def test_aggregate_label_and_counterparty_and_month(summary_df):
    summary = summary_df

    label_agg = aggregate_label_netto(summary)

    assert set(label_agg.columns) >= {
        DataFrameColumn.LABEL.value,
        DataFrameColumn.NETTO.value,
    }
    assert (
        label_agg[label_agg[DataFrameColumn.LABEL.value] == "L1"][
            DataFrameColumn.NETTO.value
        ].iloc[0]
        == 70.0
    )

    tp_agg = aggregate_tegenpartij_label_zakelijk(summary)
    assert DataFrameColumn.COUNTERPARTY.value in tp_agg.columns
    a_sum = tp_agg[tp_agg[DataFrameColumn.COUNTERPARTY.value] == "A"][
        DataFrameColumn.NETTO.value
    ].sum()
    assert a_sum == 70.0

    month_view = aggregate_month_netto(summary, include_year_totals=False)
    assert DataFrameColumn.MONTH.value in month_view.columns

    month_year = aggregate_month_netto(summary, include_year_totals=True)
    assert any(month_year[DataFrameColumn.MONTH.value].str.startswith("Totaal"))

    tegen_summary, total, count = aggregate_tegenpartijen_for_label(summary, "L1")
    assert total == 70.0
    assert count == 1


def test_summarize_by_counterparty_and_month_and_monthly_totals(raw_transactions):
    df = raw_transactions

    df[DataFrameColumn.DATE.value] = pd.to_datetime(df["Date"].astype(str))
    df[DataFrameColumn.MONTH.value] = [
        d.strftime("%Y-%m") for d in pd.to_datetime(df[DataFrameColumn.DATE.value])
    ]
    sum_by_cp = summarize_by_counterparty_per_month(df)
    assert DataFrameColumn.NETTO.value in sum_by_cp.columns

    monthly = summarize_monthly_totals(sum_by_cp)

    assert (
        DataFrameColumn.INCOME.value in monthly.columns
        and DataFrameColumn.EXPENSE.value in monthly.columns
        and DataFrameColumn.NETTO.value in monthly.columns
    )
