from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

import constants
from visualization import plot_counterparty_netto


class TegenpartijChartTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

    def update_plot(self, df, selected_month):
        if selected_month == constants.MonthFilter.ALL.value:
            self.app.set_canvas(
                self,
                None,
                self.info_label,
                "Selecteer een specifieke maand om de grafiek te zien.",
            )
            return
        fig = plot_counterparty_netto(df, selected_month)
        self.app.set_canvas(self, fig, self.info_label)
