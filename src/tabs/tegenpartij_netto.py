from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView, QMenu
from PyQt6.QtCore import Qt

from dataframe import DataFrameModel
from analysis import aggregate_tegenpartij_label_zakelijk


class TegenpartijNettoTab(QWidget):
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
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self.tegenpartij_detail_context_menu
        )
        layout.addWidget(self.table_view)

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def update(self, df):
        result = aggregate_tegenpartij_label_zakelijk(df)
        self.setDataFrame(result)
        return result

    def tegenpartij_detail_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        menu = QMenu()
        action_tijdlijn = menu.addAction("Tijdlijn voor tegenpartij")

        action = menu.exec(self.table_view.viewport().mapToGlobal(position))

        if action == action_tijdlijn:
            self.app.detail_context_menu(
                position, "Tegenpartij", self.table_view, self.model
            )
