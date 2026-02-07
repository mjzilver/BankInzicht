from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class LabelTegenpartijTab(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        self.info_label = QLabel(
            "Klik rechts op een label in de bovenste tabellen om de tegenpartijen per label te zien."
        )
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
