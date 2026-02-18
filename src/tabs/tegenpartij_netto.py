from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu

from analysis import aggregate_tegenpartij_label_zakelijk
from data_loader import DataFrameColumn
from tabs.table_base import TableTabBase


class TegenpartijNettoTab(TableTabBase):
    def __init__(self, app):
        super().__init__(app, show_search=True, editable=False)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self.tegenpartij_detail_context_menu
        )

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

        src_row = self.get_selected_source_row(index)
        tegenpartij = self.model._df.iloc[src_row][DataFrameColumn.COUNTERPARTY.value]

        menu = QMenu()
        action_tijdlijn = menu.addAction(f"Tijdlijn voor '{tegenpartij}'")

        action = menu.exec(self.table_view.viewport().mapToGlobal(position))

        if action == action_tijdlijn:
            self.app.detail_context_menu(
                position, "Tegenpartij", self.table_view, self.model
            )
