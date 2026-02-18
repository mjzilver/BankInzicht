from data_loader import clean_transactions, filter_own_ibans, load_csvs
from src.data_loader import DataFrameColumn


def test_load_csvs_concatenates(tmp_path):
    d = tmp_path
    p1 = d / "a.csv"
    p2 = d / "b.csv"
    p1.write_text(
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n20260101,1234,Party A,IBAN1,Credit,ACC1\n"
    )
    p2.write_text(
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n20260201,567,Party B,IBAN2,Debit,ACC1\n"
    )

    df = load_csvs(str(d))
    assert len(df) == 2
    assert "Date" in df.columns


def test_clean_transactions_ing_parses_amounts_and_dates(raw_transactions_ing):
    df = raw_transactions_ing

    cleaned = clean_transactions(df)

    assert DataFrameColumn.MONTH.value in cleaned.columns
    assert cleaned[DataFrameColumn.AMOUNT.value].dtype.kind in "fi"


def test_filter_own_ibans(own_ibans_df):
    df = own_ibans_df
    res = filter_own_ibans(df)
    assert not any(res["iban tegenpartij"] == "OWN1")
