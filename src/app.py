import copy
import io
import os
import sys

import pandas as pd
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import constants
import settings
from analysis import summarize_monthly_totals_by_label
from data_loader import DataFrameColumn
from importer import import_files, load_initial_data
from label_db import init_db
from plot_window import PopoutPlotWindow
from tabs.label_chart import LabelChartTab
from tabs.label_details import LabelDetailsViewer
from tabs.label_editor import LabelsEditorTab
from tabs.label_netto import LabelNettoTab
from tabs.label_tegenpartij import LabelTegenpartijTab
from tabs.maand_netto import MaandNettoTab
from tabs.maand_overzicht import MaandoverzichtTab
from tabs.tegenpartij_chart import TegenpartijChartTab
from tabs.tegenpartij_netto import TegenpartijNettoTab
from tabs.tijdlijn_chart import TijdlijnChartTab
from visualization import plot_time_line


class FinanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financieel Overzicht")
        self.setWindowIcon(QtGui.QIcon("app_icon.ico"))
        self.resize(1200, 800)
        self.setAcceptDrops(True)

        init_db()
        self.df, self.summary_df = load_initial_data()

        self.top_tabs_map = []
        self.main_tabs_map = []

        self._setup_ui()

        if not self.summary_df.empty:
            self.no_data_label.hide()
            self.update_all_views()
        else:
            self.no_data_label.show()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.setLayout(main_layout)

        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addLayout(self._setup_top_controls())
        main_layout.addWidget(splitter)

        self._init_tabs()
        splitter.addWidget(self.top_tabs)
        splitter.addWidget(self.main_tabs)

        self.no_data_label = QLabel(
            "Geen data geladen. Klik op 'Importeer bestanden' of sleep CSV-bestanden hierheen.",
        )
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.no_data_label)

    def _setup_top_controls(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Filter op maand:"))

        self.month_combo = QComboBox()
        if not self.summary_df.empty and {
            DataFrameColumn.MONTH.value,
            DataFrameColumn.MONTH_NL.value,
        }.issubset(set(self.summary_df.columns)):
            months = (
                self.summary_df.drop_duplicates(DataFrameColumn.MONTH.value)[
                    [DataFrameColumn.MONTH.value, DataFrameColumn.MONTH_NL.value]
                ]
                .sort_values(DataFrameColumn.MONTH.value)
                .reset_index(drop=True)
            )
        else:
            months = pd.DataFrame(
                columns=[DataFrameColumn.MONTH.value, DataFrameColumn.MONTH_NL.value],
            )

        self.months_df = months
        self.month_combo.addItem(constants.MonthFilter.ALL.value)
        for m in months[DataFrameColumn.MONTH_NL.value]:
            self.month_combo.addItem(m)
        self.month_combo.currentTextChanged.connect(self.on_month_changed)
        layout.addWidget(self.month_combo)

        self.theme_button = QPushButton(
            "Dark mode" if settings.UI_THEME == "light" else "Light mode",
        )
        self.theme_button.clicked.connect(self.toggle_theme)
        layout.addWidget(self.theme_button)

        self.import_button = QPushButton("Importeer bestanden")
        self.import_button.clicked.connect(self.on_import_button_clicked)
        layout.addWidget(self.import_button)

        layout.addStretch()
        return layout

    def _init_tabs(self):
        self.top_tabs = QTabWidget()
        self.tegenpartij_netto_tab = TegenpartijNettoTab(app=self)
        self.label_netto_tab = LabelNettoTab(app=self)
        self.maand_netto_tab = MaandNettoTab(app=self)

        self.top_tabs_map = [
            self.tegenpartij_netto_tab,
            self.label_netto_tab,
            self.maand_netto_tab,
        ]

        self.top_tabs.addTab(self.tegenpartij_netto_tab, "Tegenpartij Netto")
        self.top_tabs.addTab(self.label_netto_tab, "Label Netto")
        self.top_tabs.addTab(self.maand_netto_tab, "Maand Netto")

        self.main_tabs = QTabWidget()
        self.tegenpartij_chart_tab = TegenpartijChartTab(app=self)
        self.label_tab = LabelChartTab(app=self)
        self.monthly_tab = MaandoverzichtTab(app=self)
        self.tijdlijn_tab = TijdlijnChartTab(app=self)
        self.label_tegenpartij_tab = LabelTegenpartijTab(app=self)
        self.labels_editor_tab = LabelsEditorTab(app=self)
        self.label_details_viewer = LabelDetailsViewer(app=self)

        self.main_tabs_map = [
            self.tegenpartij_chart_tab,
            self.label_tab,
            self.monthly_tab,
            self.tijdlijn_tab,
            self.label_tegenpartij_tab,
            self.labels_editor_tab,
        ]

        self.main_tabs.addTab(self.tegenpartij_chart_tab, "Per Tegenpartij")
        self.main_tabs.addTab(self.label_tab, "Per Label")
        self.main_tabs.addTab(self.monthly_tab, "Maandoverzicht")
        self.main_tabs.addTab(self.tijdlijn_tab, "Tijdlijn")
        self.main_tabs.addTab(self.label_tegenpartij_tab, "Tegenpartijen per Label")
        self.main_tabs.addTab(self.labels_editor_tab, "Label Editor")

        self.top_tabs.currentChanged.connect(self._on_top_tab_changed)
        self.main_tabs.currentChanged.connect(self._on_main_tab_changed)

        for tab in self.top_tabs_map + self.main_tabs_map:
            tab.dirty = False

    def get_filtered_by_selected_month(self):
        selected = self.month_combo.currentText()
        if selected == constants.MonthFilter.ALL.value:
            return self.summary_df, selected
        maand_val = self.months_df.loc[
            self.months_df[DataFrameColumn.MONTH_NL.value] == selected,
            DataFrameColumn.MONTH.value,
        ].iloc[0]
        return (
            self.summary_df[self.summary_df[DataFrameColumn.MONTH.value] == maand_val],
            selected,
        )

    def on_month_changed(self, _):
        self.update_all_views()

    def update_all_views(self):
        filtered_df, selected_month = self.get_filtered_by_selected_month()
        isAlleSelected = selected_month == constants.MonthFilter.ALL.value

        for i, tab in enumerate(self.top_tabs_map):
            if i == self.top_tabs.currentIndex():
                tab.dirty = False
                (
                    tab.update(filtered_df, isAlleSelected)
                    if tab is self.maand_netto_tab
                    else tab.update(filtered_df)
                )
            else:
                tab.dirty = True

        for i, tab in enumerate(self.main_tabs_map):
            if i == self.main_tabs.currentIndex():
                tab.dirty = False
                if tab is self.tegenpartij_chart_tab or tab is self.label_tab:
                    tab.update_plot(filtered_df, selected_month)
                elif tab is self.monthly_tab:
                    tab.update_plot()
                elif tab is self.label_tegenpartij_tab and getattr(
                    tab, "current_label", None,
                ):
                    tab.update_for_label(tab.current_label)
                elif tab is self.labels_editor_tab:
                    tab.populate()
            else:
                tab.dirty = True

    def _on_top_tab_changed(self, index):
        filtered_df, selected_month = self.get_filtered_by_selected_month()
        if 0 <= index < len(self.top_tabs_map):
            tab = self.top_tabs_map[index]
            if getattr(tab, "dirty", False):
                (
                    tab.update(
                        filtered_df, selected_month == constants.MonthFilter.ALL.value,
                    )
                    if tab is self.maand_netto_tab
                    else tab.update(filtered_df)
                )
                tab.dirty = False

    def _on_main_tab_changed(self, index):
        filtered_df, selected_month = self.get_filtered_by_selected_month()
        if 0 <= index < len(self.main_tabs_map):
            tab = self.main_tabs_map[index]
            if getattr(tab, "dirty", False):
                if tab is self.tegenpartij_chart_tab or tab is self.label_tab:
                    tab.update_plot(filtered_df, selected_month)
                elif tab is self.monthly_tab:
                    tab.update_plot()
                elif tab is self.label_tegenpartij_tab and getattr(
                    tab, "current_label", None,
                ):
                    tab.update_for_label(tab.current_label)
                elif tab is self.labels_editor_tab:
                    tab.populate()
                tab.dirty = False

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
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding,
            )
            canvas.setSizePolicy(policy)
            canvas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            canvas.customContextMenuRequested.connect(
                lambda pos: self.show_canvas_context_menu(canvas, pos),
            )
            layout.addWidget(canvas)
            layout.setStretchFactor(canvas, 1)
        if info_label:
            info_label.setText(info_text or "")

    def show_canvas_context_menu(self, canvas, position):
        menu = QMenu()
        action_copy = menu.addAction("Kopieer grafiek")
        action_open = menu.addAction("Open in nieuw venster")
        action = menu.exec(canvas.mapToGlobal(position))
        if action == action_copy:
            self.copy_canvas_to_clipboard(canvas)
        elif action == action_open:
            self.open_plot_window(canvas)

    def open_plot_window(self, canvas):
        fig_copy = copy.deepcopy(canvas.figure)
        win = PopoutPlotWindow(fig_copy, parent=self)
        win.show()

    def copy_canvas_to_clipboard(self, canvas):
        buf = io.BytesIO()
        canvas.figure.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)
        pixmap = QPixmap()
        pixmap.loadFromData(buf.read())
        QApplication.clipboard().setPixmap(pixmap)
        buf.close()

    def detail_context_menu(self, position, index_name, table_view, model):
        index = table_view.indexAt(position)
        if not index.isValid():
            return
        view_model = table_view.model()
        if hasattr(view_model, "mapToSource"):
            source_index = view_model.mapToSource(index)
            source_model = view_model.sourceModel()
        else:
            source_index = index
            source_model = view_model
        value = source_model._df.iloc[source_index.row()][index_name]
        filtered_df = self.summary_df[self.summary_df[index_name] == value].copy()
        monthly = summarize_monthly_totals_by_label(filtered_df)
        avg = filtered_df[DataFrameColumn.NETTO.value].mean()
        fig = plot_time_line(
            monthly, title=f"Tijdlijn voor: {value} - Gemiddeld: {avg:.2f} per maand",
        )
        self.set_canvas(self.tijdlijn_tab, fig)
        self.main_tabs.setCurrentWidget(self.tijdlijn_tab)
        self.tijdlijn_tab.info_label.setText("")
        self.tijdlijn_tab.info_label.hide()

    def on_import_button_clicked(self):
        start_dir = (
            settings.DATA_DIR
            if os.path.exists(settings.DATA_DIR)
            else os.path.expanduser("~")
        )
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Selecteer CSV-bestanden om te importeren",
            start_dir,
            "CSV Files (*.csv);;All Files (*)",
        )
        if files:
            self._handle_import_files(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        csvs = [
            u.toLocalFile()
            for u in event.mimeData().urls()
            if u.isLocalFile() and u.toLocalFile().lower().endswith(".csv")
        ]
        if csvs:
            self._handle_import_files(csvs)

    def _handle_import_files(self, file_paths: list[str]):
        try:
            self.df, self.summary_df, import_messages = import_files(
                self.df if not self.df.empty else None, file_paths, copy_files=True,
            )
            self.update_all_views()
            if import_messages:
                QMessageBox.information(
                    self, "Import resultaat", "\n".join(import_messages),
                )
        except Exception as e:
            QMessageBox.critical(self, "Import fout", str(e))

    def toggle_theme(self):
        new_theme = "dark" if settings.UI_THEME == "light" else "light"
        settings.set_theme(new_theme)
        style_path = os.path.join("style", f"{new_theme}.qss")
        if os.path.exists(style_path):
            with open(style_path) as f:
                self.setStyleSheet(f.read())
        self.theme_button.setText("Dark mode" if new_theme == "light" else "Light mode")


def main():
    app = QApplication(sys.argv)
    styleFile = os.path.join("style", f"{settings.UI_THEME}.qss")
    if os.path.exists(styleFile):
        with open(styleFile) as f:
            app.setStyleSheet(f.read())
    win = FinanceApp()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
