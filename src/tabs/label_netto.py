from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QTableView, QMenu
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

    def update(self, df):
        grouped_by_label = (
            df.groupby(["Label"], as_index=False)["Netto"]
            .sum()
            .sort_values(by="Netto", ascending=False)
        )
        self.setDataFrame(grouped_by_label)

    def label_detail_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        label_value = self.model._df.iloc[index.row()]["Label"]
        
        menu = QMenu()
        action_tijdlijn = menu.addAction("Tijdlijn voor label")
        action_tegenpartijen = menu.addAction("Tegenpartijen per label")
        
        action = menu.exec(self.table_view.viewport().mapToGlobal(position))
        
        if action == action_tijdlijn:
            self.app.label_details_viewer.show_tijdlijn_for_label(label_value)
        elif action == action_tegenpartijen:
            self.app.label_details_viewer.show_tegenpartijen_for_label(label_value)
