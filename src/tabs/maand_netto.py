from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView
import pandas as pd

from dataframe import DataFrameModel
from analysis import aggregate_month_netto


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
        display_df = aggregate_month_netto(df, include_year_totals=isAlleSelected)
        self.setDataFrame(display_df)
