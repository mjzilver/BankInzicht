from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView, QLabel
from PyQt6.QtCore import Qt

from dataframe import DataFrameModel
from visualization import plot_counterparty_netto


class TegenpartijChartTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.model = DataFrameModel()
        self.table_view.setModel(self.model)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self.tegenpartij_detail_context_menu
        )

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def update(self, df):
        tegenpartij_df = df[["Tegenpartij", "Netto", "Label", "Zakelijk_NL"]].copy()
        tegenpartij_df = tegenpartij_df.rename(columns={"Zakelijk_NL": "Zakelijk"})
        tegenpartij_df = (
            tegenpartij_df.groupby(
                ["Tegenpartij", "Label", "Zakelijk"], as_index=False
            )["Netto"]
            .sum()
            .sort_values(by="Netto", ascending=False)
        )
        self.setDataFrame(tegenpartij_df)

    def update_plot(self, df, selected_month):
        if selected_month == "Alle maanden":
            self.app.set_canvas(
                self,
                None,
                self.info_label,
                "Selecteer een specifieke maand om de grafiek te zien.",
            )
            return
        fig = plot_counterparty_netto(df)
        self.app.set_canvas(self, fig, self.info_label)

    def tegenpartij_detail_context_menu(self, position):
        self.app.detail_context_menu(
            position, "Tegenpartij", self.table_view, self.model
        )
