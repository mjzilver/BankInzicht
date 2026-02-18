from analysis import summarize_monthly_totals_by_label
from visualization import plot_time_line
from data_loader import DataFrameColumn


class LabelDetailsViewer:
    def __init__(self, app):
        self.app = app

    def show_tijdlijn_for_label(self, label_value):
        filtered_df = self.app.summary_df[
            self.app.summary_df[DataFrameColumn.LABEL.value] == label_value
        ].copy()
        monthly = summarize_monthly_totals_by_label(filtered_df)
        avg = filtered_df[DataFrameColumn.NETTO.value].mean()
        fig = plot_time_line(
            monthly,
            title=f"Tijdlijn voor: {label_value} - Gemiddeld: {avg:.2f} per maand",
        )
        self.app.set_canvas(self.app.tijdlijn_tab, fig)
        self.app.main_tabs.setCurrentWidget(self.app.tijdlijn_tab)
        self.app.tijdlijn_tab.info_label.setText("")
        self.app.tijdlijn_tab.info_label.hide()

    def show_tegenpartijen_for_label(self, label_value):
        if hasattr(self.app, "label_tegenpartij_tab"):
            self.app.label_tegenpartij_tab.update_for_label(label_value, focus=True)
