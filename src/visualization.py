from matplotlib import cm
from matplotlib.colors import to_hex
import matplotlib.pyplot as plt
import numpy as np


def plot_horizontal_bar(df, value_col, category_col, title="", highlight=None):
    df = df.copy()
    df[category_col] = df[category_col].replace("", f"geen {category_col.lower()}")

    df = df.sort_values(by=value_col, ascending=False)
    n_rows = len(df)
    fig_height = max(4, n_rows * 0.1)
    fig, ax = plt.subplots(figsize=(8, fig_height))

    colors = df[value_col].apply(lambda x: "green" if x >= 0 else "red")
    bars = ax.barh(df[category_col][::-1], df[value_col][::-1], color=colors[::-1])

    offset = 2
    for i, bar in enumerate(bars):
        width = bar.get_width()
        y = bar.get_y() + bar.get_height() / 2

        ax.annotate(
            f"{width:,.2f}€",
            xy=(width, y),
            xytext=(offset if width >= 0 else -offset, 0),
            textcoords="offset points",
            ha="left" if width >= 0 else "right",
            va="center",
            fontsize=6,
            color="black",
        )

        cat_text = df[category_col].iloc[::-1].iloc[i]
        ax.annotate(
            cat_text[:50],
            xy=(0, y),
            xytext=(-offset if width >= 0 else offset, 0),
            textcoords="offset points",
            ha="right" if width >= 0 else "left",
            va="center",
            fontsize=6,
            color="black",
        )

    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_title(title)
    plt.tight_layout()
    return fig


def plot_counterparty_netto(filtered_df, highlight=None):
    return plot_horizontal_bar(
        filtered_df,
        value_col="Netto",
        category_col="Tegenpartij",
        title="Netto per Tegenpartij",
        highlight=highlight,
    )


def plot_label_netto(filtered_df, highlight=None):
    df = filtered_df.copy()
    df["Label"] = df["Label"].replace("", "geen label")

    grouped = (
        df.groupby("Label")
        .agg(
            Netto=("Netto", "sum"),
            Positief=("Netto", lambda x: (x > 0).sum()),
            Negatief=("Netto", lambda x: (x < 0).sum()),
            Aantal=("Tegenpartij", "count"),
        )
        .reset_index()
    )

    return plot_horizontal_bar(
        grouped,
        value_col="Netto",
        category_col="Label",
        title="Netto per Label",
        highlight=highlight,
    )


def plot_monthly_overview(monthly):
    fig, ax = plt.subplots(figsize=(12, 5))

    monthly["Label"] = monthly["Label"].replace("", "geen label")

    months = monthly["Maand_NL"].unique()
    labels = monthly["Label"].unique()

    x = np.arange(len(months))
    width = 0.8

    cmap = cm.get_cmap("tab20", len(labels))
    label_colors = {label: to_hex(cmap(i)) for i, label in enumerate(labels)}

    income_bottom = np.zeros(len(months))
    expense_bottom = np.zeros(len(months))

    for label in labels:
        subset = monthly[monthly["Label"] == label]
        subset = subset.set_index("Maand_NL").reindex(months, fill_value=0)

        inkomsten = subset["inkomsten"].values
        uitgaven = subset["uitgaven"].abs().values

        ax.bar(
            x,
            inkomsten,
            width=width / 3,
            bottom=income_bottom,
            label=label,
            color=label_colors[label],
        )
        ax.bar(
            x + width / 3,
            uitgaven,
            width=width / 3,
            bottom=expense_bottom,
            label=None,
            color=label_colors[label],
            hatch="/",
        )

        income_bottom += inkomsten
        expense_bottom += uitgaven

    netto = income_bottom - expense_bottom
    total_bar = ax.bar(
        x + width * 2 / 3,
        netto,
        width=width / 3,
        color="gray",
        alpha=0.5,
        label="Netto totaal",
        zorder=3,
    )
    for i, bar in enumerate(total_bar):
        ax.annotate(
            f"{netto[i]:,.2f}€",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3 if netto[i] >= 0 else -9),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=8,
            color="black",
        )

    ax.set_ylabel("Bedrag (€)")
    ax.set_xticks(x + width / 4)
    ax.set_xticklabels(months, rotation=45, ha="right")
    ax.legend(title="Labelkleur en soort", bbox_to_anchor=(1.05, 1), loc="upper left")
    ax.set_title("Maandelijkse Inkomsten -- Gestreept is negatief")
    ax.margins(y=0.1)
    plt.tight_layout()
    return fig
