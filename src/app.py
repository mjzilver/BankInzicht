import os
import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTabWidget,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QSplitter,
    QPushButton,
)
from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt6.QtWidgets import QSizePolicy, QComboBox

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from data_loader import load_csvs, clean_transactions, merge_and_clean_labels
from analysis import (
    filter_zakelijkheid,
    summarize_by_counterparty_per_month,
    summarize_monthly_totals_by_label,
)
import settings
from visualization import (
    plot_counterparty_netto,
    plot_label_netto,
    plot_monthly_overview,
)
from utils import format_month
from label_db import get_labels, save_label, init_db


class DataFrameModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None):
        super().__init__(parent)
        self._df = df.reset_index(drop=True)

    def setDataFrame(self, df):
        self.beginResetModel()
        self._df = df.reset_index(drop=True)
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()):
        return len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return 0 if self._df.empty else len(self._df.columns)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return QVariant()
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            if isinstance(val, float):
                return f"{val:,.2f}"
            return str(val)
        return QVariant()

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._df.columns[section])
            else:
                return str(section)
        return QVariant()


class FinanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financieel Overzicht")
        self.resize(1200, 800)

        init_db()
        self.df = clean_transactions(load_csvs(settings.DATA_DIR))

        if self.df.empty:
            self.show_empty()
            return

        self.summary_df = summarize_by_counterparty_per_month(self.df)
        self.summary_df["Maand_NL"] = self.summary_df["Maand"].apply(format_month)
        self.summary_df = self.summary_df.sort_values(
            by=["Maand", "Netto"], ascending=[True, False]
        )
        self.summary_df = merge_and_clean_labels(self.summary_df, get_labels())

        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Maand filter ---
        top_controls = QHBoxLayout()
        top_controls.addWidget(QLabel("Filter op maand:"))

        self.month_combo = QComboBox()
        months = self.summary_df.drop_duplicates("Maand")[
            ["Maand", "Maand_NL"]
        ].sort_values("Maand")
        self.months_df = months
        self.month_combo.addItem("Alle maanden")
        for m in months["Maand_NL"]:
            self.month_combo.addItem(m)
        self.month_combo.currentTextChanged.connect(self.on_month_changed)
        top_controls.addWidget(self.month_combo)

        # --- Thema button ---
        self.theme_button = QPushButton(
            "Dark mode" if settings.UI_THEME == "light" else "Light mode"
        )
        self.theme_button.clicked.connect(self.toggle_theme)
        top_controls.addWidget(self.theme_button)

        top_controls.addStretch()
        main_layout.addLayout(top_controls)

        self.top_tabs = QTabWidget()

        # Tegenpartij Netto
        self.table_tp = QTableView()
        self.model_tp = DataFrameModel()
        self.table_tp.setModel(self.model_tp)
        self.table_tp.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.top_tabs.addTab(self.table_tp, "Tegenpartij Netto")

        # Labels Netto
        self.table_label = QTableView()
        self.model_label = DataFrameModel()
        self.table_label.setModel(self.model_label)
        self.table_label.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.top_tabs.addTab(self.table_label, "Label Netto")

        self.main_tabs = QTabWidget()

        splitter.addWidget(self.top_tabs)
        splitter.addWidget(self.main_tabs)
        main_layout.addWidget(splitter)

        # Per Tegenpartij
        self.tab_tp = QWidget()
        tp_layout = QVBoxLayout(self.tab_tp)
        self.info_tp = QLabel()
        self.info_tp.setWordWrap(True)
        tp_layout.addWidget(self.info_tp)
        self.main_tabs.addTab(self.tab_tp, "Per Tegenpartij")

        # Per Label
        self.tab_label = QWidget()
        label_layout = QVBoxLayout(self.tab_label)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        label_layout.addWidget(self.info_label)
        self.main_tabs.addTab(self.tab_label, "Per Label")

        # Maandelijkse Samenvatting
        self.tab_monthly = QWidget()
        monthly_layout = QVBoxLayout(self.tab_monthly)
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter op zakelijkheid:"))
        self.zakelijkheid_combo = QComboBox()
        self.zakelijkheid_combo.addItems(["Alle", "Zakelijk", "Niet-zakelijk"])
        self.zakelijkheid_combo.currentTextChanged.connect(self.update_monthly_plot)
        filter_layout.addWidget(self.zakelijkheid_combo)
        filter_layout.addStretch()
        monthly_layout.addLayout(filter_layout)
        self.main_tabs.addTab(self.tab_monthly, "Maandelijkse Samenvatting")

        # Tegenpartij Labels
        self.tab_labels_editor = QWidget()
        ed_layout = QVBoxLayout(self.tab_labels_editor)
        self.labels_table = QTableWidget()
        self.labels_table.itemChanged.connect(self.label_item_changed)
        ed_layout.addWidget(self.labels_table)
        self.main_tabs.addTab(self.tab_labels_editor, "Tegenpartij Labels")

        self.update_all_views()

    def get_filtered_by_selected_month(self):
        selected = self.month_combo.currentText()
        if selected == "Alle maanden":
            return self.summary_df, selected
        maand_val = self.months_df[self.months_df["Maand_NL"] == selected][
            "Maand"
        ].iloc[0]
        return self.summary_df[self.summary_df["Maand"] == maand_val], selected

    def on_month_changed(self, _):
        self.update_all_views()

    def update_all_views(self):
        filtered_df, selected_month = self.get_filtered_by_selected_month()
        self.update_tables(filtered_df)
        self.update_tp_plot(filtered_df, selected_month)
        self.update_label_plot(filtered_df, selected_month)
        self.update_monthly_plot()
        self.populate_labels_editor()

    def update_tables(self, df):
        df1 = df[["Tegenpartij", "Netto", "Label", "Zakelijk_NL"]].copy()
        self.model_tp.setDataFrame(df1)
        grouped = (
            df.groupby(["Label", "Zakelijk_NL"], as_index=False)["Netto"]
            .sum()
            .sort_values(by="Netto", ascending=False)
        )
        self.model_label.setDataFrame(grouped)

    def update_tp_plot(self, df, selected_month):
        if selected_month == "Alle maanden":
            self.set_canvas(
                self.tab_tp,
                None,
                self.info_tp,
                "Selecteer een specifieke maand om de grafiek te zien.",
            )
            return
        fig = plot_counterparty_netto(df)
        self.set_canvas(self.tab_tp, fig, self.info_tp)

    def update_label_plot(self, df, selected_month):
        if selected_month == "Alle maanden":
            self.set_canvas(
                self.tab_label,
                None,
                self.info_label,
                "Selecteer een specifieke maand om de grafiek te zien.",
            )
            return
        fig = plot_label_netto(df)
        self.set_canvas(self.tab_label, fig, self.info_label)

    def update_monthly_plot(self):
        zakelijkheid = self.zakelijkheid_combo.currentText()
        filtered_label_df = filter_zakelijkheid(self.summary_df, zakelijkheid)
        monthly = summarize_monthly_totals_by_label(filtered_label_df)
        fig = plot_monthly_overview(monthly)
        self.set_canvas(self.tab_monthly, fig)

    def set_canvas(self, tab_widget, fig, info_label=None, info_text=None):
        layout = tab_widget.layout()
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if isinstance(widget, FigureCanvasQTAgg):
                layout.removeWidget(widget)
                widget.setParent(None)
        if fig is not None:
            canvas = FigureCanvasQTAgg(fig)
            policy = QSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            canvas.setSizePolicy(policy)
            layout.addWidget(canvas)
            layout.setStretchFactor(canvas, 1)
        if info_label:
            info_label.setText(info_text or "")

    # --- Label Editor ---
    def populate_labels_editor(self):
        parties = sorted(self.summary_df["Tegenpartij"].str.strip().unique())
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

            existing = labels_df[labels_df["Tegenpartij"] == tp]
            label_val = existing["Label"].values[0] if not existing.empty else ""
            zakelijk_val = (
                existing["Zakelijk"].values[0] if not existing.empty else False
            )

            item_label = QTableWidgetItem(label_val)
            self.labels_table.setItem(i, 1, item_label)

            combo = QComboBox()
            combo.addItems(["Zakelijk", "Niet-zakelijk"])
            combo.setCurrentIndex(0 if zakelijk_val else 1)
            combo.currentIndexChanged.connect(
                lambda _, row=i: self.save_label_from_row(row)
            )
            self.labels_table.setCellWidget(i, 2, combo)

        self.labels_table.blockSignals(False)

    def label_item_changed(self, item):
        if item.column() == 1:
            row = item.row()
            self.save_label_from_row(row)

    def save_label_from_row(self, row):
        tp = self.labels_table.item(row, 0).text()
        label_item = self.labels_table.item(row, 1)
        label = label_item.text() if label_item else ""
        combo = self.labels_table.cellWidget(row, 2)
        zakelijk = combo.currentText() == "Zakelijk" if combo else False

        save_label(tp, label, zakelijk)

        mask = self.summary_df["Tegenpartij"] == tp
        self.summary_df.loc[mask, "Label"] = label or "geen label"
        self.summary_df.loc[mask, "Zakelijk_NL"] = (
            "Zakelijk" if zakelijk else "Niet-zakelijk"
        )

        self.update_all_views()

    def show_empty(self):
        layout = QVBoxLayout(self)
        msg = QLabel(
            "Geen transactiebestanden gevonden.\n"
            "Plaats CSV-bestanden in de data-map en start de applicatie opnieuw."
        )
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)
        self.setLayout(layout)

    def toggle_theme(self):
        new_theme = "dark" if settings.UI_THEME == "light" else "light"
        settings.set_theme(new_theme)

        style_path = os.path.join("style", f"{new_theme}.qss")
        if os.path.exists(style_path):
            with open(style_path, "r") as f:
                self.window().setStyleSheet(f.read())

        self.theme_button.setText("Dark mode" if new_theme == "light" else "Light mode")


def main():
    app = QApplication(sys.argv)

    styleFile = os.path.join("style", f"{settings.UI_THEME}.qss")
    with open(styleFile, "r") as f:
        app.setStyleSheet(f.read())

    win = FinanceApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
