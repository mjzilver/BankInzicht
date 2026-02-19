import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QStackedLayout,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from constants import Zakelijkheid
from data_loader import DataFrameColumn
from dataframe import DataFrameModel
from label_db import get_labels, save_label


class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items

    def createEditor(self, parent, option, index):
        cb = QComboBox(parent)
        cb.addItems(self.items)
        return cb

    def setEditorData(self, editor, index):
        val = index.model().data(index, Qt.ItemDataRole.EditRole)
        if val is None:
            val = index.model().data(index, Qt.ItemDataRole.DisplayRole)
        if isinstance(val, bool):
            editor.setCurrentText(
                Zakelijkheid.BUSINESS.value if val else Zakelijkheid.NON_BUSINESS.value
            )
        else:
            editor.setCurrentText(str(val))

    def setModelData(self, editor, model, index):
        text = editor.currentText()
        model.setData(index, text, Qt.ItemDataRole.EditRole)


class LabelsEditorTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        top_hbox = QHBoxLayout()
        top_hbox.addStretch()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Zoek")
        top_hbox.addWidget(self.search_box)
        layout.addLayout(top_hbox)

        self.table = QTableView()
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.AllEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.table)
        self.stacked_layout.setCurrentWidget(self.table)
        layout.addLayout(self.stacked_layout)

        empty_df = pd.DataFrame(
            columns=[
                DataFrameColumn.COUNTERPARTY.value,
                DataFrameColumn.LABEL.value,
                DataFrameColumn.BUSINESS.value,
            ]
        )
        self.model = DataFrameModel(empty_df, parent=self, editable=True)
        self.proxy = self.model.createProxy(parent=self)
        self.table.setModel(self.proxy)

        delegate = ComboBoxDelegate(
            [Zakelijkheid.BUSINESS.value, Zakelijkheid.NON_BUSINESS.value],
            parent=self.table,
        )
        self.table.setItemDelegateForColumn(2, delegate)

        self.search_box.textChanged.connect(self._on_search_text_changed)
        self.model.dataChanged.connect(self.on_model_changed)
        self.search_box.installEventFilter(self)

    def eventFilter(self, obj, event):
        if obj == self.search_box:
            from PyQt6.QtCore import QEvent
            if event.type() == QEvent.Type.FocusIn:
                self.table.clearSelection()
                self.table.closePersistentEditor(self.table.currentIndex())
                self.table.setCurrentIndex(self.table.rootIndex())
        return super().eventFilter(obj, event)

    def _on_search_text_changed(self, t):
        if self.proxy:
            self.proxy.setFilterWildcard(f"*{t}*")

    def populate(self):
        current_search = self.search_box.text()
        header = self.table.horizontalHeader()
        sort_col = (
            header.sortIndicatorSection() if header.isSortIndicatorShown() else -1
        )
        sort_order = (
            header.sortIndicatorOrder() if header.isSortIndicatorShown() else None
        )
        v_scroll = self.table.verticalScrollBar().value() if self.table.model() else 0
        h_scroll = self.table.horizontalScrollBar().value() if self.table.model() else 0

        self.update_labels_in_place()

        if current_search:
            self.search_box.setText(current_search)
            self.proxy.setFilterWildcard(f"*{current_search}*")

        if sort_col >= 0 and sort_order is not None:
            self.table.sortByColumn(sort_col, sort_order)

        self.table.verticalScrollBar().setValue(v_scroll)
        self.table.horizontalScrollBar().setValue(h_scroll)

        self.stacked_layout.setCurrentWidget(self.table)

    def update_labels_in_place(self):
        labels_df = get_labels()
        parties = sorted(
            self.app.summary_df[DataFrameColumn.COUNTERPARTY.value].str.strip().unique()
        )
        labels_lookup = {
            row[DataFrameColumn.COUNTERPARTY.value]: row
            for _, row in labels_df.iterrows()
        }
        rows = []
        for tp in parties:
            if tp in labels_lookup:
                label_row = labels_lookup[tp]
                label = label_row[DataFrameColumn.LABEL.value]
                zakelijk = (
                    Zakelijkheid.BUSINESS.value
                    if label_row[DataFrameColumn.BUSINESS.value]
                    else Zakelijkheid.NON_BUSINESS.value
                )
            else:
                label = ""
                zakelijk = Zakelijkheid.NON_BUSINESS.value
            rows.append(
                {
                    DataFrameColumn.COUNTERPARTY.value: tp,
                    DataFrameColumn.LABEL.value: label,
                    DataFrameColumn.BUSINESS.value: zakelijk,
                }
            )
        new_df = pd.DataFrame(
            rows,
            columns=[
                DataFrameColumn.COUNTERPARTY.value,
                DataFrameColumn.LABEL.value,
                DataFrameColumn.BUSINESS.value,
            ],
        )
        current_df = self.model.getDataFrame()

        if not current_df.equals(new_df):
            self.model.setDataFrame(new_df)

    def on_model_changed(self, topLeft, bottomRight, roles=None):
        df = self.model.getDataFrame()

        start = topLeft.row()
        end = bottomRight.row()
        changed_any = False
        for r in range(start, end + 1):
            tp = df.iloc[r][DataFrameColumn.COUNTERPARTY.value]
            label = df.iloc[r][DataFrameColumn.LABEL.value]
            zak_text = df.iloc[r][DataFrameColumn.BUSINESS.value]
            zakelijk = True if zak_text == Zakelijkheid.BUSINESS.value else False

            mask = self.app.summary_df[DataFrameColumn.COUNTERPARTY.value] == tp
            if mask.any():
                current_label = self.app.summary_df.loc[
                    mask, DataFrameColumn.LABEL.value
                ].iloc[0]
                current_zak = bool(
                    self.app.summary_df.loc[mask, DataFrameColumn.BUSINESS.value].iloc[
                        0
                    ]
                )
            else:
                current_label = None
                current_zak = None

            normalized_label = label.strip() if label else ""
            normalized_label = normalized_label if normalized_label else "geen label"

            if current_label == normalized_label and current_zak == bool(zakelijk):
                continue

            save_label(tp, label, zakelijk)
            self.app.summary_df.loc[mask, DataFrameColumn.LABEL.value] = (
                normalized_label
            )
            self.app.summary_df.loc[mask, DataFrameColumn.BUSINESS.value] = bool(
                zakelijk
            )
            self.app.summary_df.loc[mask, DataFrameColumn.BUSINESS_NL.value] = (
                Zakelijkheid.BUSINESS.value
                if zakelijk
                else Zakelijkheid.NON_BUSINESS.value
            )
            changed_any = True

        if changed_any:
            self.app.update_all_views()
