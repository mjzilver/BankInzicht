from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLineEdit,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from dataframe import DataFrameModel


class TableTabBase(QWidget):
    def __init__(self, app, show_search: bool = True, editable: bool = False):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        if show_search:
            top_hbox = QHBoxLayout()
            top_hbox.addStretch()
            self.search_box = QLineEdit()
            self.search_box.setPlaceholderText("Zoek")
            top_hbox.addWidget(self.search_box)
            layout.addLayout(top_hbox)
        else:
            self.search_box = None

        self.table_view = QTableView()
        self.table_view.setSortingEnabled(True)
        self.table_view.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch,
        )
        layout.addWidget(self.table_view)

        self.model = DataFrameModel(editable=editable)
        self.proxy = self.model.createProxy(parent=self)
        self.table_view.setModel(self.proxy)

        if self.search_box is not None:
            self.search_box.textChanged.connect(
                lambda t: self.proxy.setFilterWildcard(f"*{t}*"),
            )

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def get_selected_source_row(self, view_index):
        if hasattr(self.proxy, "mapToSource"):
            src_idx = self.proxy.mapToSource(view_index)
            return src_idx.row()
        return view_index.row()
