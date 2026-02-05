from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class TijdlijnChartTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.info_label = QLabel(
            "Klik op een label of tegenpartij in bovenste tabellen om de maandelijkse Tijdlijn te zien."
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
