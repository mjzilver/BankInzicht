from analysis import summarize_monthly_totals_by_label, aggregate_tegenpartijen_for_label
from visualization import plot_horizontal_bar, plot_time_line


class LabelDetailsViewer:
    def __init__(self, app):
        self.app = app

    def show_tijdlijn_for_label(self, label_value):
        filtered_df = self.app.summary_df[
            self.app.summary_df["Label"] == label_value
        ].copy()
        monthly = summarize_monthly_totals_by_label(filtered_df)
        avg = filtered_df["Netto"].mean()
        fig = plot_time_line(
            monthly,
            title=f"Tijdlijn voor: {label_value} - Gemiddeld: {avg:.2f} per maand",
        )
        self.app.set_canvas(self.app.tijdlijn_tab, fig)
        self.app.main_tabs.setCurrentWidget(self.app.tijdlijn_tab)
        self.app.tijdlijn_tab.info_label.setText("")
        self.app.tijdlijn_tab.info_label.hide()

    def show_tegenpartijen_for_label(self, label_value):
        tegenpartij_summary, total, count = aggregate_tegenpartijen_for_label(
            self.app.summary_df, label_value
        )

        fig = plot_horizontal_bar(
            tegenpartij_summary,
            value_col="Netto",
            category_col="Tegenpartij",
            title=f"Tegenpartijen voor label: {label_value}\nTotaal: {total:.2f}€ - Aantal: {count}",
        )

        self.app.set_canvas(self.app.label_tegenpartij_tab, fig)
        self.app.main_tabs.setCurrentWidget(self.app.label_tegenpartij_tab)
        self.app.label_tegenpartij_tab.info_label.setText("")
        self.app.label_tegenpartij_tab.info_label.hide()
