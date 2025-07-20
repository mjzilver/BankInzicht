def summarize_by_counterparty_per_month(
    df, date_col="Maand", party_col="Naam tegenpartij", amount_col="Bedrag"
):
    monthly = df.groupby([date_col, party_col])[amount_col].sum().reset_index()
    monthly.columns = ["Maand", "Tegenpartij", "Netto"]
    monthly["Maand"] = monthly["Maand"].astype(str)
    return monthly


def summarize_monthly_totals(summary_df):
    return (
        summary_df.groupby(["Maand", "Maand_NL"])["Netto"]
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
        summary_df.groupby(["Maand", "Maand_NL", "Label"])["Netto"]
        .agg(
            inkomsten=lambda x: x[x > 0].sum(),
            uitgaven=lambda x: x[x < 0].sum(),
            netto="sum",
        )
        .reset_index()
        .sort_values("Maand")
    )
    
def filter_zakelijkheid(summary_df, zakelijkheid):
    if zakelijkheid == "Zakelijk":
        return summary_df[summary_df["Zakelijk"] == True]
    elif zakelijkheid == "Niet-zakelijk":
        return summary_df[summary_df["Zakelijk"] == False]
    else:
        return summary_df
