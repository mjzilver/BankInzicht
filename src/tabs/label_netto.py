from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView
from PyQt6.QtCore import Qt

from dataframe import DataFrameModel


class LabelNettoTab(QWidget):
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
            self.label_detail_context_menu
        )
        layout.addWidget(self.table_view)

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def label_detail_context_menu(self, position):
        self.app.detail_context_menu(position, "Label", self.table_view, self.model)
