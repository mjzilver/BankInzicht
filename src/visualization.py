import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import to_hex

from constants import Label
from data_loader import DataFrameColumn


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
    fig.tight_layout()
    plt.close(fig)
    return fig


def plot_counterparty_netto(filtered_df, selected_month, highlight=None):
    return plot_horizontal_bar(
        filtered_df,
        value_col=DataFrameColumn.NETTO.value,
        category_col=DataFrameColumn.COUNTERPARTY.value,
        title=f"Netto per Tegenpartij - {selected_month}",
        highlight=highlight,
    )


def plot_label_netto(filtered_df, selected_month, highlight=None):
    df = filtered_df.copy()
    df[DataFrameColumn.LABEL.value] = df[DataFrameColumn.LABEL.value].replace(
        "", Label.GEEN.value
    )

    grouped = (
        df.groupby(DataFrameColumn.LABEL.value)
        .agg(
            Netto=(DataFrameColumn.NETTO.value, "sum"),
            Positief=(DataFrameColumn.NETTO.value, lambda x: (x > 0).sum()),
            Negatief=(DataFrameColumn.NETTO.value, lambda x: (x < 0).sum()),
            Aantal=(DataFrameColumn.COUNTERPARTY.value, "count"),
        )
        .reset_index()
    )

    return plot_horizontal_bar(
        grouped,
        value_col=DataFrameColumn.NETTO.value,
        category_col=DataFrameColumn.LABEL.value,
        title=f"Netto per Label - {selected_month}",
        highlight=highlight,
    )


def plot_time_line(df, title):
    fig, ax = plt.subplots()
    if (df[DataFrameColumn.INCOME.value] != 0).any():
        _ = ax.plot(
            df[DataFrameColumn.MONTH_NL.value],
            df[DataFrameColumn.INCOME.value],
            label="Inkomsten",
            color="green",
            marker="o",
        )
        for i, (x, y) in enumerate(
            zip(df[DataFrameColumn.MONTH_NL.value], df[DataFrameColumn.INCOME.value])
        ):
            ax.annotate(
                f"{y:,.2f}€",
                xy=(x, y),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="black",
            )

    if (df[DataFrameColumn.EXPENSE.value] != 0).any():
        ax.plot(
            df[DataFrameColumn.MONTH_NL.value],
            df[DataFrameColumn.EXPENSE.value],
            label="Uitgaven",
            color="red",
            marker="o",
        )
        for i, (x, y) in enumerate(
            zip(df[DataFrameColumn.MONTH_NL.value], df[DataFrameColumn.EXPENSE.value])
        ):
            ax.annotate(
                f"{y:,.2f}€",
                xy=(x, y),
                xytext=(0, -15),
                textcoords="offset points",
                ha="center",
                fontsize=8,
                color="black",
            )

    ax.set_title(title)
    ax.set_xlabel("Maand")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_ylabel("Bedrag (€)")
    ax.legend()
    ax.grid(True)
    fig.set_size_inches(10, 5)
    fig.tight_layout()
    plt.close(fig)
    return fig


def plot_monthly_overview(df):
    fig, ax = plt.subplots(figsize=(12, 5))

    df[DataFrameColumn.LABEL.value] = df[DataFrameColumn.LABEL.value].replace(
        "", Label.GEEN.value
    )

    months = df[DataFrameColumn.MONTH_NL.value].unique()
    labels = df[DataFrameColumn.LABEL.value].unique()

    x = np.arange(len(months))
    width = 0.8

    cmap = cm.get_cmap("tab20b", len(labels) + 1)
    label_colors = {label: to_hex(cmap(i)) for i, label in enumerate(labels)}

    income_bottom = np.zeros(len(months))
    expense_bottom = np.zeros(len(months))

    for label in labels:
        subset = df[df[DataFrameColumn.LABEL.value] == label]
        subset = subset.set_index(DataFrameColumn.MONTH_NL.value).reindex(months)

        # Fill NaN values with 0 for numeric columns
        num_cols = subset.select_dtypes(include="number").columns
        subset[num_cols] = subset[num_cols].fillna(0)
        # Fill empty labels with "geen label"
        subset[DataFrameColumn.LABEL.value] = subset[
            DataFrameColumn.LABEL.value
        ].fillna(Label.GEEN.value)

        inkomsten = subset[DataFrameColumn.INCOME.value].values
        uitgaven = subset[DataFrameColumn.EXPENSE.value].abs().values

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
    fig.subplots_adjust(right=0.75)

    n_labels = len(labels)
    ncol = 1
    if n_labels > 20:
        ncol = int(np.ceil(n_labels / 20))

    ax.legend(
        title="Labelkleur en soort",
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        fontsize=8,
        title_fontsize=9,
        ncol=ncol,
    )
    ax.set_title("Maandelijkse Inkomsten -- Gestreept is negatief")
    ax.margins(y=0.1)
    fig.tight_layout()
    plt.close(fig)
    return fig
