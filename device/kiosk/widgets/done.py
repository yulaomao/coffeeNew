from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class DonePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        layout = QVBoxLayout(self)
        label = QLabel("制作完成页面 (开发中)")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
    
    def setup_page(self, **kwargs):
        pass