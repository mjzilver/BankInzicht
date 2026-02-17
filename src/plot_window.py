from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT


class PopoutPlotWindow(QMainWindow):
    def __init__(self, figure, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Grafiek — Vergroot")

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.canvas = FigureCanvasQTAgg(figure)
        layout.addWidget(self.canvas)

        self.toolbar = NavigationToolbar2QT(self.canvas, self)

        for action in self.toolbar.actions():
            text = (action.text() or "").lower()
            if any(k in text for k in ("home", "back", "forward")):
                action.setVisible(False)

        layout.addWidget(self.toolbar)

        self.resize(900, 700)
