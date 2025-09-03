from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

class OutOfServicePage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        layout = QVBoxLayout(self)
        self.message_label = QLabel("暂停服务")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 24px; color: #dc3545;")
        layout.addWidget(self.message_label)
    
    def setup_page(self, reason="maintenance", **kwargs):
        messages = {
            "maintenance": "设备维护中",
            "materials": "物料不足", 
            "network": "网络连接中",
            "error": "设备故障"
        }
        self.message_label.setText(messages.get(reason, "暂停服务"))