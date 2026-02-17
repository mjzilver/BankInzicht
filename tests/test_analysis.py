import pandas as pd

from analysis import (
    aggregate_label_netto,
    aggregate_tegenpartij_label_zakelijk,
    aggregate_month_netto,
    aggregate_tegenpartijen_for_label,
    summarize_by_counterparty_per_month,
    summarize_monthly_totals,
    summarize_monthly_totals_by_label,
)


def test_aggregate_label_and_counterparty_and_month(summary_df):
    summary = summary_df

    label_agg = aggregate_label_netto(summary)
    assert set(label_agg.columns) >= {"Label", "Netto"}
    assert label_agg[label_agg["Label"] == "L1"]["Netto"].iloc[0] == 70.0

    tp_agg = aggregate_tegenpartij_label_zakelijk(summary)
    assert "Tegenpartij" in tp_agg.columns
    a_sum = tp_agg[tp_agg["Tegenpartij"] == "A"]["Netto"].sum()
    assert a_sum == 70.0

    month_view = aggregate_month_netto(summary, include_year_totals=False)
    assert "Maand" in month_view.columns

    month_year = aggregate_month_netto(summary, include_year_totals=True)
    assert any(month_year["Maand"].str.startswith("Totaal"))

    tegen_summary, total, count = aggregate_tegenpartijen_for_label(summary, "L1")
    assert total == 70.0
    assert count == 1


def test_summarize_by_counterparty_and_month_and_monthly_totals(raw_transactions):
    df = raw_transactions
    df["date"] = pd.to_datetime(df["Date"].astype(str))
    df["Maand"] = [d.strftime("%Y-%m") for d in pd.to_datetime(df["date"])]
    sum_by_cp = summarize_by_counterparty_per_month(df)
    assert "Netto" in sum_by_cp.columns

    monthly = summarize_monthly_totals(sum_by_cp)
    assert "inkomsten" in monthly.columns and "uitgaven" in monthly.columns and "netto" in monthly.columns

