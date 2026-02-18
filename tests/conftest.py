from src.constants import Zakelijkheid
import pandas as pd
import pandas.testing as pdt
import pytest


@pytest.fixture
def summary_df():
    return pd.DataFrame(
        {
            "Maand": ["2026-01", "2026-01", "2026-02", "2026-02"],
            "Maand_NL": ["jan 2026", "jan 2026", "feb 2026", "feb 2026"],
            "Tegenpartij": ["A", "A", "B", "C"],
            "Label": ["L1", "L1", "L2", ""],
            "Zakelijk": [True, True, False, False],
            "Zakelijk_NL": [
                Zakelijkheid.BUSINESS.value,
                Zakelijkheid.BUSINESS.value,
                Zakelijkheid.NON_BUSINESS.value,
                Zakelijkheid.NON_BUSINESS.value,
            ],
            "Netto": [100.0, -30.0, 50.0, -20.0],
        }
    )


@pytest.fixture
def transactions_df():
    return pd.DataFrame(
        {
            "Maand": ["2026-01", "2026-01", "2026-02"],
            "Tegenpartij": ["A", "A", "B"],
            "Bedrag": [70.0, 0.0, 50.0],
        }
    )


@pytest.fixture
def raw_transactions():
    # Dutch-style raw transactions
    return pd.DataFrame(
        {
            "Date": ["20260101", "20260115", "20260201"],
            "Bedrag": [1234.56, 0.00, 50.00],
            "Naam": ["Desc A", "Desc B", "Desc C"],
            "Tegenpartij": ["CP A", "CP B", "CP C"],
            "Debit/credit": ["Debit", "Credit", "Credit"],
            "Account": ["ACC1", "ACC1", "ACC1"],
        }
    )


@pytest.fixture
def raw_transactions_ing():
    # ING-style English raw transactions
    return pd.DataFrame(
        {
            "Date": ["20260101", "20260115", "20260201"],
            "Amount (EUR)": ["1234,56", "0,00", "50,00"],
            "Name / Description": ["Desc A", "Desc B", "Desc C"],
            "Counterparty": ["CP A", "CP B", "CP C"],
            "Debit/credit": ["Debit", "Credit", "Credit"],
            "Account": ["ACC1", "ACC1", "ACC1"],
        }
    )


@pytest.fixture
def own_ibans_df():
    return pd.DataFrame(
        {
            "iban": ["OWN1", "OWN1", "OTHER"],
            "iban tegenpartij": ["OTHER", "OWN1", "X"],
            "date": ["2026-01-01"] * 3,
            "Bedrag": [10, 20, 30],
            "Tegenpartij": ["A", "B", "C"],
        }
    )


def assert_no_mutation(func, df, *args, **kwargs):
    orig = df.copy(deep=True)
    result = func(df, *args, **kwargs)
    pdt.assert_frame_equal(df, orig)
    return result
