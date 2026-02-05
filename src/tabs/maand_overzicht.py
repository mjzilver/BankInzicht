from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox

from analysis import filter_zakelijkheid, summarize_monthly_totals_by_label
from visualization import plot_monthly_overview


class MaandoverzichtTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter op zakelijkheid:"))
        self.zakelijkheid_combo = QComboBox()
        self.zakelijkheid_combo.addItems(["Alle", "Zakelijk", "Niet-zakelijk"])
        self.zakelijkheid_combo.currentTextChanged.connect(self.update_plot)
        filter_layout.addWidget(self.zakelijkheid_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)

    def update_plot(self):
        zakelijkheid = self.zakelijkheid_combo.currentText()
        filtered_label_df = filter_zakelijkheid(self.app.summary_df, zakelijkheid)
        monthly = summarize_monthly_totals_by_label(filtered_label_df)
        fig = plot_monthly_overview(monthly)
        self.app.set_canvas(self, fig)
