from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableView,
    QHeaderView,
    QComboBox,
    QHBoxLayout,
    QLineEdit,
    QStyledItemDelegate,
)

from label_db import get_labels, save_label
from PyQt6.QtCore import Qt, QModelIndex
from PyQt6.QtWidgets import QAbstractItemView
import pandas as pd

from dataframe import DataFrameModel


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
            editor.setCurrentText("Zakelijk" if val else "Niet-zakelijk")
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
        layout.addWidget(self.table)

        self.model = None
        self.proxy = None

    def populate(self):
        parties = sorted(self.app.summary_df["Tegenpartij"].str.strip().unique())
        labels_df = get_labels()

        rows = []
        for tp in parties:
            row = labels_df[labels_df["Tegenpartij"] == tp]
            if not row.empty:
                label = row.iloc[0]["Label"]
                zakelijk = row.iloc[0]["Zakelijk"]
            else:
                label = ""
                zakelijk = False
            rows.append(
                {
                    "Tegenpartij": tp,
                    "Label": label,
                    "Zakelijk": "Zakelijk" if zakelijk else "Niet-zakelijk",
                }
            )

        df = pd.DataFrame(rows, columns=["Tegenpartij", "Label", "Zakelijk"])

        self.model = DataFrameModel(df, parent=self, editable=True)
        self.proxy = self.model.createProxy(parent=self)
        self.table.setModel(self.proxy)

        delegate = ComboBoxDelegate(["Zakelijk", "Niet-zakelijk"], parent=self.table)
        self.table.setItemDelegateForColumn(2, delegate)

        self.search_box.textChanged.connect(
            lambda t: self.proxy.setFilterWildcard(f"*{t}*")
        )

        self.model.dataChanged.connect(self.on_model_changed)

    def on_model_changed(
        self, topLeft: QModelIndex, bottomRight: QModelIndex, roles=None
    ):
        df = self.model.getDataFrame()

        start = topLeft.row()
        end = bottomRight.row()
        changed_any = False
        for r in range(start, end + 1):
            tp = df.iloc[r]["Tegenpartij"]
            label = df.iloc[r]["Label"]
            zak_text = df.iloc[r]["Zakelijk"]
            zakelijk = True if str(zak_text).lower().startswith("z") else False

            mask = self.app.summary_df["Tegenpartij"] == tp
            if mask.any():
                current_label = self.app.summary_df.loc[mask, "Label"].iloc[0]
                current_zak = bool(self.app.summary_df.loc[mask, "Zakelijk"].iloc[0])
            else:
                current_label = None
                current_zak = None

            normalized_label = label.strip() if label else ""
            normalized_label = normalized_label if normalized_label else "geen label"

            if current_label == normalized_label and current_zak == bool(zakelijk):
                continue

            save_label(tp, label, zakelijk)
            self.app.summary_df.loc[mask, "Label"] = normalized_label
            self.app.summary_df.loc[mask, "Zakelijk"] = bool(zakelijk)
            self.app.summary_df.loc[mask, "Zakelijk_NL"] = (
                "Zakelijk" if zakelijk else "Niet-zakelijk"
            )
            changed_any = True

        if changed_any:
            self.app.update_all_views()
