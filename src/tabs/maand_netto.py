from analysis import aggregate_month_netto
from tabs.table_base import TableTabBase


class MaandNettoTab(TableTabBase):
    def __init__(self, app):
        super().__init__(app, show_search=True, editable=False)

    def setDataFrame(self, df):
        self.model.setDataFrame(df)

    def update(self, df, isAlleSelected):
        display_df = aggregate_month_netto(df, include_year_totals=isAlleSelected)
        self.setDataFrame(display_df)
