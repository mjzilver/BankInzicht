from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView
import pandas as pd

from dataframe import DataFrameModel


class MaandNettoTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.model = DataFrameModel()
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table_view)

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def update(self, df, isAlleSelected):
        grouped_by_month = df.groupby(["Maand", "Maand_NL"], as_index=False)[
            "Netto"
        ].sum()

        if isAlleSelected:
            grouped_by_month["Jaar"] = grouped_by_month["Maand"].str[:4].astype(int)

            year_totals = grouped_by_month.groupby("Jaar", as_index=False)[
                "Netto"
            ].sum()

            year_totals["Maand_NL"] = "Totaal " + year_totals["Jaar"].astype(str)

            combined = pd.concat([year_totals, grouped_by_month], ignore_index=True)

            combined["_is_total"] = combined["Maand_NL"].str.startswith("Totaal")

            combined = combined.sort_values(
                by=["Jaar", "_is_total", "Maand"], ascending=[False, False, False]
            ).drop(columns="_is_total")

            display_df = combined[["Maand_NL", "Netto"]].rename(
                columns={"Maand_NL": "Maand"}
            )

            self.setDataFrame(display_df)
        else:
            self.setDataFrame(
                grouped_by_month.sort_values(by="Maand", ascending=False)
                .drop(columns="Maand")
                .rename(columns={"Maand_NL": "Maand"})
            )
