from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel

from analysis import aggregate_tegenpartijen_for_label
from visualization import plot_horizontal_bar


class LabelTegenpartijTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.info_label = QLabel(
            "Klik met de rechtermuisknop op een label in de bovenste tabellen om de tegenpartijen per label te zien."
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.current_label = None

    def update_for_label(self, label_value, focus=False):
        filtered_summary_df, selected_month = self.app.get_filtered_by_selected_month()
        target_df = (
            self.app.summary_df
            if selected_month == "Alle maanden"
            else filtered_summary_df
        )

        tegenpartij_summary, total, count = aggregate_tegenpartijen_for_label(
            target_df, label_value
        )

        title = f"Tegenpartijen voor label: {label_value}"
        if selected_month != "Alle maanden":
            title += f" ({selected_month})"
        title += f"\nTotaal: {total:.2f}€ - Aantal: {count}"

        fig = plot_horizontal_bar(
            tegenpartij_summary,
            value_col="Netto",
            category_col="Tegenpartij",
            title=title,
        )

        self.current_label = label_value
        self.app.set_canvas(self, fig, self.info_label)

        if focus:
            self.app.main_tabs.setCurrentWidget(self)
        self.info_label.setText("")
        self.info_label.hide()
