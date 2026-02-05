from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QComboBox,
)

from label_db import get_labels, save_label
from PyQt6.QtCore import Qt


class LabelsEditorTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.labels_table = QTableWidget()
        self.labels_table.setSortingEnabled(True)
        self.labels_table.itemChanged.connect(self.label_item_changed)
        layout.addWidget(self.labels_table)

    def populate(self):
        parties = sorted(self.app.summary_df["Tegenpartij"].str.strip().unique())
        labels_df = get_labels()

        self.labels_table.blockSignals(True)
        self.labels_table.clear()
        self.labels_table.setColumnCount(3)
        self.labels_table.setRowCount(len(parties))
        self.labels_table.setHorizontalHeaderLabels(
            ["Tegenpartij", "Label", "Zakelijk"]
        )
        self.labels_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        for i, tp in enumerate(parties):
            item_tp = QTableWidgetItem(tp)
            item_tp.setFlags(item_tp.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.labels_table.setItem(i, 0, item_tp)

            row = labels_df[labels_df["Tegenpartij"] == tp]
            if not row.empty:
                label = row.iloc[0]["Label"]
                zakelijk = row.iloc[0]["Zakelijk"]
                self.labels_table.setItem(i, 1, QTableWidgetItem(label))
                combo = QComboBox()
                combo.addItems(["Zakelijk", "Niet-zakelijk"])
                combo.setCurrentText("Zakelijk" if zakelijk else "Niet-zakelijk")
                combo.currentTextChanged.connect(
                    lambda _, r=i: self.save_label_from_row(r)
                )
                self.labels_table.setCellWidget(i, 2, combo)
            else:
                self.labels_table.setItem(i, 1, QTableWidgetItem(""))
                combo = QComboBox()
                combo.addItems(["Zakelijk", "Niet-zakelijk"])
                combo.setCurrentText("Niet-zakelijk")
                combo.currentTextChanged.connect(
                    lambda _, r=i: self.save_label_from_row(r)
                )
                self.labels_table.setCellWidget(i, 2, combo)

        self.labels_table.blockSignals(False)

    def label_item_changed(self, item):
        if item.column() == 1:
            self.save_label_from_row(item.row())

    def save_label_from_row(self, row):
        tp = self.labels_table.item(row, 0).text()
        label_item = self.labels_table.item(row, 1)
        label = label_item.text() if label_item else ""
        combo = self.labels_table.cellWidget(row, 2)
        zakelijk = combo.currentText() == "Zakelijk" if combo else False

        save_label(tp, label, zakelijk)

        mask = self.app.summary_df["Tegenpartij"] == tp
        self.app.summary_df.loc[mask, "Label"] = label
        self.app.summary_df.loc[mask, "Zakelijk"] = bool(zakelijk)
        self.app.summary_df.loc[mask, "Zakelijk_NL"] = (
            "Zakelijk" if zakelijk else "Niet-zakelijk"
        )

        self.app.update_all_views()
