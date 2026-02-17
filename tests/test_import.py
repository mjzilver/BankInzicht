from pathlib import Path

import settings
from data_loader import load_files, import_and_merge


def test_load_files_reads_multiple(tmp_path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    p1.write_text(
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n20260101,1234,Party A,IBAN1,Credit,ACC1\n"
    )
    p2.write_text(
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n20260201,567,Party B,IBAN2,Debit,ACC1\n"
    )

    df = load_files([str(p1), str(p2)])
    assert len(df) == 2
    assert "Date" in df.columns


def test_import_and_merge_copies_and_dedupes(tmp_path):
    p1 = tmp_path / "a.csv"
    p2 = tmp_path / "b.csv"
    content = (
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n"
        "20260101,1234,Party A,IBAN1,Credit,ACC1\n"
    )
    p1.write_text(content)
    p2.write_text(content)

    settings.DATA_DIR = str(tmp_path / "data")
    res = import_and_merge(None, [str(p1), str(p2)], copy_files=True)

    assert len(res) == 1
    
    files = list(Path(settings.DATA_DIR).glob("*.csv"))
    assert len(files) >= 1


def test_import_and_merge_mixed_formats(tmp_path):
    p_ing = tmp_path / "ing.csv"
    p_rabo = tmp_path / "rabo.csv"

    p_ing.write_text(
        "Date,Amount (EUR),Name / Description,Counterparty,Debit/credit,Account\n"
        "20260101,1234,Desc ING,CPING,Credit,ACC1\n"
    )

    p_rabo.write_text(
        "Datum,Bedrag,Naam tegenpartij,Tegenrekening IBAN/BBAN,IBAN/BBAN\n"
        "2026-01-15,567,Desc RABO,IBAN_OTHER,IBAN2\n"
    )

    # do not copy files during test
    res = import_and_merge(None, [str(p_ing), str(p_rabo)], copy_files=False)

    # both rows should be present and normalized
    assert len(res) == 2
    assert "Bedrag" in res.columns
    assert "Tegenpartij" in res.columns

