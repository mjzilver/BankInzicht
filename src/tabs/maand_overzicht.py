from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from constants import MonthFilter, Zakelijkheid
from data_loader import DataFrameColumn
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
        self.zakelijkheid_combo.addItems(
            [
                Zakelijkheid.ALL.value,
                Zakelijkheid.BUSINESS.value,
                Zakelijkheid.NON_BUSINESS.value,
            ]
        )
        self.zakelijkheid_combo.currentTextChanged.connect(self.update_plot)
        filter_layout.addWidget(self.zakelijkheid_combo)

        filter_layout.addWidget(QLabel("Filter per maand:"))
        self.maand_combo = QComboBox()
        self.maand_combo.addItem(MonthFilter.ALL.value)
        self.maand_combo.currentTextChanged.connect(self.update_plot)
        filter_layout.addWidget(self.maand_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

    def update_plot(self):
        zakelijkheid = self.zakelijkheid_combo.currentText()
        filtered_label_df = filter_zakelijkheid(self.app.summary_df, zakelijkheid)
        monthly = summarize_monthly_totals_by_label(filtered_label_df)

        for maand in monthly[DataFrameColumn.MONTH.value].unique():
            if maand not in [
                self.maand_combo.itemText(i) for i in range(self.maand_combo.count())
            ]:
                self.maand_combo.addItem(maand)

        if self.maand_combo.currentText() != MonthFilter.ALL.value:
            monthly = monthly[
                monthly[DataFrameColumn.MONTH.value] == self.maand_combo.currentText()
            ]

        fig = plot_monthly_overview(monthly)
        self.app.set_canvas(self, fig)
