import io
import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QTabWidget,
    QSplitter,
    QPushButton,
    QMenu,
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QSizePolicy, QComboBox
from PyQt6 import QtGui
from PyQt6.QtGui import QPixmap

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
import pickle
from plot_window import PopoutPlotWindow

from data_loader import load_csvs, clean_transactions, merge_and_clean_labels
from analysis import (
    summarize_by_counterparty_per_month,
    summarize_monthly_totals_by_label,
)
import settings
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
from visualization import (
    plot_time_line,
)
from utils import format_month
from label_db import get_labels, init_db


class FinanceApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Financieel Overzicht")
        self.setWindowIcon(QtGui.QIcon("app_icon.ico"))
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
        self.tegenpartij_netto_tab = TegenpartijNettoTab(app=self)
        self.top_tabs.addTab(self.tegenpartij_netto_tab, "Tegenpartij Netto")

        # Labels Netto
        self.label_netto_tab = LabelNettoTab(app=self)
        self.top_tabs.addTab(self.label_netto_tab, "Label Netto")

        # Maand netto
        self.maand_netto_tab = MaandNettoTab(app=self)
        self.top_tabs.addTab(self.maand_netto_tab, "Maand Netto")

        self.main_tabs = QTabWidget()

        splitter.addWidget(self.top_tabs)
        splitter.addWidget(self.main_tabs)
        main_layout.addWidget(splitter)

        # Per Tegenpartij
        self.tegenpartij_chart_tab = TegenpartijChartTab(app=self)
        self.main_tabs.addTab(self.tegenpartij_chart_tab, "Per Tegenpartij")

        # Per Label
        self.label_tab = LabelChartTab(app=self)
        self.main_tabs.addTab(self.label_tab, "Per Label")

        # Maandoverzicht
        self.monthly_tab = MaandoverzichtTab(app=self)
        self.main_tabs.addTab(self.monthly_tab, "Maandoverzicht")

        # Label Editor
        self.labels_editor_tab = LabelsEditorTab(app=self)
        self.main_tabs.addTab(self.labels_editor_tab, "Label Editor")

        # Tijdlijn
        self.tijdlijn_tab = TijdlijnChartTab(app=self)
        self.main_tabs.addTab(self.tijdlijn_tab, "Tijdlijn")

        # Tegenpartijen per Label
        self.label_tegenpartij_tab = LabelTegenpartijTab(app=self)
        self.main_tabs.addTab(self.label_tegenpartij_tab, "Tegenpartijen per Label")

        # Label details viewer
        self.label_details_viewer = LabelDetailsViewer(app=self)

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
        isAlleSelected = selected_month == "Alle maanden"

        # Update tables
        self.tegenpartij_netto_tab.update(filtered_df)
        self.label_netto_tab.update(filtered_df)
        self.maand_netto_tab.update(filtered_df, isAlleSelected)

        # Update plots
        self.tegenpartij_chart_tab.update_plot(filtered_df, selected_month)
        self.label_tab.update_plot(filtered_df, selected_month)
        self.monthly_tab.update_plot()
        self.labels_editor_tab.populate()

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
            canvas.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            canvas.customContextMenuRequested.connect(
                lambda pos: self.show_canvas_context_menu(canvas, pos)
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
        fig = canvas.figure
        try:
            fig_copy = pickle.loads(pickle.dumps(fig))
        except Exception:
            fig_copy = fig

        win = PopoutPlotWindow(fig_copy, parent=self)
        win.show()

    def copy_canvas_to_clipboard(self, canvas):
        fig = canvas.figure

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
        buf.seek(0)

        pixmap = QPixmap()
        pixmap.loadFromData(buf.read())

        QApplication.clipboard().setPixmap(pixmap)

        buf.close()

    def detail_context_menu(self, position, index_name, table_view, model):
        index = table_view.indexAt(position)
        if not index.isValid():
            return

        # If the view is showing a proxy model, map the index to the source model
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
        avg = filtered_df["Netto"].mean()
        fig = plot_time_line(
            monthly, title=f"Tijdlijn voor: {value} - Gemiddeld: {avg:.2f} per maand"
        )
        self.set_canvas(self.tijdlijn_tab, fig)

        self.main_tabs.setCurrentWidget(self.tijdlijn_tab)

        self.tijdlijn_tab.info_label.setText("")
        self.tijdlijn_tab.info_label.hide()

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
