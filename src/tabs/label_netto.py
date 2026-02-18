from PyQt6.QtWidgets import QMenu
from PyQt6.QtCore import Qt

from tabs.table_base import TableTabBase
from analysis import aggregate_label_netto


class LabelNettoTab(TableTabBase):
    def __init__(self, app):
        super().__init__(app, show_search=True, editable=False)
        self.table_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table_view.customContextMenuRequested.connect(
            self.label_detail_context_menu
        )

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def update(self, df):
        grouped_by_label = aggregate_label_netto(df)
        self.setDataFrame(grouped_by_label)

    def label_detail_context_menu(self, position):
        index = self.table_view.indexAt(position)
        if not index.isValid():
            return

        src_row = self.get_selected_source_row(index)
        label_value = self.model._df.iloc[src_row]["Label"]

        menu = QMenu()
        action_tijdlijn = menu.addAction(f"Tijdlijn voor '{label_value}'")
        action_tegenpartijen = menu.addAction(f"Tegenpartijen voor '{label_value}'")

        action = menu.exec(self.table_view.viewport().mapToGlobal(position))

        if action == action_tijdlijn:
            self.app.label_details_viewer.show_tijdlijn_for_label(label_value)
        elif action == action_tegenpartijen:
            self.app.label_details_viewer.show_tegenpartijen_for_label(label_value)
