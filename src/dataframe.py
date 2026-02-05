from PyQt6.QtCore import Qt, QAbstractTableModel, QModelIndex, QVariant
import pandas as pd


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

    def sort(self, column, order):
        colname = self._df.columns[column]

        self.layoutAboutToBeChanged.emit()

        self._df.sort_values(
            by=colname,
            ascending=(order == Qt.SortOrder.AscendingOrder),
            inplace=True,
            kind="mergesort",
        )
        self._df.reset_index(drop=True, inplace=True)

        self.layoutChanged.emit()
