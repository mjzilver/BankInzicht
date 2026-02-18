import pandas.testing as pdt

from analysis import (
    aggregate_label_netto,
    aggregate_tegenpartij_label_zakelijk,
    aggregate_month_netto,
    summarize_by_counterparty_per_month,
    summarize_monthly_totals,
    summarize_monthly_totals_by_label,
    filter_zakelijkheid,
)

from conftest import assert_no_mutation


def test_aggregate_label_netto_no_mutation_and_conserves_sum(summary_df):
    df = summary_df
    orig = df.copy(deep=True)
    total = df["Netto"].sum()

    out = aggregate_label_netto(df)
    pdt.assert_frame_equal(df, orig)
    assert abs(out["Netto"].sum() - total) < 1e-9


def test_aggregate_tegenpartij_label_zakelijk_no_mutation_and_conserves_sum(summary_df):
    df = summary_df
    orig = df.copy(deep=True)
    total = df["Netto"].sum()

    out = aggregate_tegenpartij_label_zakelijk(df)
    pdt.assert_frame_equal(df, orig)
    assert abs(out["Netto"].sum() - total) < 1e-9


def test_aggregate_month_netto_no_mutation_and_conserves_sum(summary_df):
    df = summary_df
    orig = df.copy(deep=True)
    total = df["Netto"].sum()

    out1 = aggregate_month_netto(df, include_year_totals=False)
    pdt.assert_frame_equal(df, orig)
    assert abs(out1["Netto"].sum() - total) < 1e-9

    out2 = aggregate_month_netto(df, include_year_totals=True)
    pdt.assert_frame_equal(df, orig)

    # When year totals are included, the output contains 'Totaal <year>' rows
    assert any(out2["Maand"].str.startswith("Totaal"))
    non_total_sum = out2[~out2["Maand"].str.startswith("Totaal")]["Netto"].sum()
    assert abs(non_total_sum - total) < 1e-9


def test_summarize_by_counterparty_and_month_no_mutation_and_conserves_sum(
    transactions_df,
):
    summed = assert_no_mutation(summarize_by_counterparty_per_month, transactions_df)

    monthly_totals = summarize_monthly_totals(summed)
    assert abs(monthly_totals["netto"].sum() - transactions_df["Bedrag"].sum()) < 1e-9


def test_summarize_monthly_totals_by_label_no_mutation_and_values(summary_df):
    df = summary_df
    orig = df.copy(deep=True)

    res = summarize_monthly_totals_by_label(df)
    pdt.assert_frame_equal(df, orig)

    # verify expected value for January
    jan = res[res["Maand"] == "2026-01"]
    assert abs(jan["netto"].sum() - 70.0) < 1e-9


def test_filter_zakelijkheid_no_mutation(summary_df, transactions_df):
    df = summary_df
    # aggregate_label_netto
    out = assert_no_mutation(aggregate_label_netto, df)
    assert abs(out["Netto"].sum() - df["Netto"].sum()) < 1e-9

    # aggregate_tegenpartij_label_zakelijk
    out = assert_no_mutation(aggregate_tegenpartij_label_zakelijk, df)
    assert abs(out["Netto"].sum() - df["Netto"].sum()) < 1e-9

    # aggregate_month_netto without and with year totals
    out1 = assert_no_mutation(aggregate_month_netto, df, False)
    assert abs(out1["Netto"].sum() - df["Netto"].sum()) < 1e-9

    out2 = assert_no_mutation(aggregate_month_netto, df, True)
    assert any(out2["Maand"].str.startswith("Totaal"))
    non_total_sum = out2[~out2["Maand"].str.startswith("Totaal")]["Netto"].sum()
    assert abs(non_total_sum - df["Netto"].sum()) < 1e-9

    # summarize_by_counterparty_per_month and monthly totals
    summed = assert_no_mutation(summarize_by_counterparty_per_month, transactions_df)
    monthly_totals = summarize_monthly_totals(summed)
    assert abs(monthly_totals["netto"].sum() - transactions_df["Bedrag"].sum()) < 1e-9

    # summarize_monthly_totals_by_label
    res = assert_no_mutation(summarize_monthly_totals_by_label, df)
    jan = res[res["Maand"] == "2026-01"]
    assert abs(jan["netto"].sum() - 70.0) < 1e-9

    # filter_zakelijkheid
    assert_no_mutation(filter_zakelijkheid, df, "Zakelijk")
    assert_no_mutation(filter_zakelijkheid, df, "Niet-zakelijk")
