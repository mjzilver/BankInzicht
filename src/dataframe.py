from PyQt6.QtCore import (
    Qt,
    QAbstractTableModel,
    QModelIndex,
    QVariant,
    QSortFilterProxyModel,
)
import pandas as pd


class DataFrameModel(QAbstractTableModel):
    def __init__(self, df=pd.DataFrame(), parent=None, editable: bool = False):
        super().__init__(parent)
        self._df = df.reset_index(drop=True)
        self._editable = editable

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
        # For editing, return the raw value for EditRole
        if role == Qt.ItemDataRole.EditRole:
            val = self._df.iloc[index.row(), index.column()]
            return val
        if role == Qt.ItemDataRole.DisplayRole:
            val = self._df.iloc[index.row(), index.column()]
            if isinstance(val, float):
                return f"{val:,.2f}"
            return str(val)
        return QVariant()

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if self._editable:
            if index.column() != 0:
                flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        row = index.row()
        col = index.column()
        # update underlying dataframe
        try:
            self._df.iat[row, col] = value
        except Exception:
            return False
        left = self.index(row, col)
        right = self.index(row, col)
        self.dataChanged.emit(left, right, [Qt.ItemDataRole.EditRole])
        return True

    def getDataFrame(self):
        return self._df

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

    def createProxy(self, parent=None, case_sensitive=False):
        proxy = QSortFilterProxyModel(parent)
        proxy.setSourceModel(self)
        cs = (
            Qt.CaseSensitivity.CaseSensitive
            if case_sensitive
            else Qt.CaseSensitivity.CaseInsensitive
        )
        proxy.setFilterCaseSensitivity(cs)
        proxy.setFilterKeyColumn(-1)
        return proxy
