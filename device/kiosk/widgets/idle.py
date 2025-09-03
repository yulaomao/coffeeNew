from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QLabel, QScrollArea, QFrame)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap, QFont
from loguru import logger
from ...utils.i18n import t
from ...utils.images import image_manager

class IdlePage(QWidget):
    """Idle/Attraction screen page"""
    
    # Signals
    start_order_clicked = Signal()
    maintenance_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.maintenance_press_count = 0
        self.maintenance_timer = QTimer()
        self.maintenance_timer.timeout.connect(self.reset_maintenance_count)
        self.screensaver_timer = QTimer()
        self.screensaver_timer.timeout.connect(self.show_screensaver)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI"""
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
            }
            
            .welcome-title {
                font-size: 36px;
                font-weight: bold;
                color: #212529;
                margin: 20px 0;
            }
            
            .welcome-subtitle {
                font-size: 20px;
                color: #6c757d;
                margin: 10px 0;
            }
            
            .start-button {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 20px 40px;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                min-width: 300px;
                min-height: 80px;
            }
            
            .start-button:hover {
                background-color: #0056b3;
            }
            
            .start-button:pressed {
                background-color: #004085;
            }
            
            .feature-item {
                background-color: white;
                border: 1px solid #dee2e6;
                border-radius: 8px;
                padding: 20px;
                margin: 10px;
                min-width: 200px;
            }
            
            .maintenance-area {
                background-color: transparent;
                border: none;
                min-width: 60px;
                min-height: 60px;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Top area with logo and maintenance access
        top_layout = QHBoxLayout()
        
        # Logo
        logo_label = QLabel()
        logo_pixmap = image_manager.load_pixmap("logo.png", (200, 100))
        if logo_pixmap:
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("☕ " + t("app_name"))
            logo_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        top_layout.addWidget(logo_label)
        top_layout.addStretch()
        
        # Hidden maintenance access area (top-right corner)
        self.maintenance_area = QPushButton()
        self.maintenance_area.setStyleSheet("background-color: transparent; border: none;")
        self.maintenance_area.setFixedSize(60, 60)
        self.maintenance_area.clicked.connect(self.on_maintenance_area_clicked)
        top_layout.addWidget(self.maintenance_area)
        
        layout.addLayout(top_layout)
        
        # Center area with welcome content
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setAlignment(Qt.AlignCenter)
        center_layout.setSpacing(30)
        
        # Welcome message
        welcome_title = QLabel(t("welcome", "欢迎使用智能咖啡机"))
        welcome_title.setAlignment(Qt.AlignCenter)
        welcome_title.setObjectName("welcome-title")
        welcome_title.setStyleSheet("font-size: 36px; font-weight: bold; color: #212529;")
        center_layout.addWidget(welcome_title)
        
        subtitle = QLabel("享受美味咖啡，从这里开始")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("font-size: 20px; color: #6c757d;")
        center_layout.addWidget(subtitle)
        
        # Coffee image
        coffee_label = QLabel()
        coffee_pixmap = image_manager.load_pixmap("coffee_cup.png", (200, 200))
        if coffee_pixmap:
            coffee_label.setPixmap(coffee_pixmap)
        else:
            coffee_label.setText("☕")
            coffee_label.setStyleSheet("font-size: 100px;")
        coffee_label.setAlignment(Qt.AlignCenter)
        center_layout.addWidget(coffee_label)
        
        # Start order button
        self.start_button = QPushButton(t("start_order", "开始点单"))
        self.start_button.setObjectName("start-button")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 20px 40px;
                border-radius: 12px;
                font-size: 24px;
                font-weight: bold;
                min-width: 300px;
                min-height: 80px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.start_button.clicked.connect(self.on_start_order)
        center_layout.addWidget(self.start_button, 0, Qt.AlignCenter)
        
        layout.addWidget(center_widget, 1)
        
        # Bottom features area
        features_widget = QWidget()
        features_layout = QHBoxLayout(features_widget)
        features_layout.setAlignment(Qt.AlignCenter)
        
        # Feature highlights
        features = [
            ("🌟", "新鲜现磨", "每杯都是新鲜制作"),
            ("⚡", "快速制作", "2分钟内完成"),
            ("💰", "价格实惠", "高品质低价格"),
            ("📱", "移动支付", "微信支付宝都支持")
        ]
        
        for icon, title, desc in features:
            feature_frame = QFrame()
            feature_frame.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 15px;
                    margin: 5px;
                }
            """)
            feature_layout = QVBoxLayout(feature_frame)
            
            icon_label = QLabel(icon)
            icon_label.setAlignment(Qt.AlignCenter)
            icon_label.setStyleSheet("font-size: 32px; margin-bottom: 5px;")
            
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #212529;")
            
            desc_label = QLabel(desc)
            desc_label.setAlignment(Qt.AlignCenter)
            desc_label.setStyleSheet("font-size: 12px; color: #6c757d;")
            desc_label.setWordWrap(True)
            
            feature_layout.addWidget(icon_label)
            feature_layout.addWidget(title_label)
            feature_layout.addWidget(desc_label)
            
            features_layout.addWidget(feature_frame)
        
        layout.addWidget(features_widget)
        
        # Start screensaver timer
        self.start_screensaver_timer()
    
    def setup_page(self, **kwargs):
        """Setup page when shown"""
        logger.info("Showing idle page")
        self.maintenance_press_count = 0
        self.start_screensaver_timer()
    
    def start_screensaver_timer(self):
        """Start screensaver timer"""
        from ...constants import IDLE_TIMEOUT_SEC
        self.screensaver_timer.start(IDLE_TIMEOUT_SEC * 1000)
    
    def show_screensaver(self):
        """Show screensaver (for now just log)"""
        logger.debug("Would show screensaver")
        # In a full implementation, this would show a rotating slideshow
    
    def on_start_order(self):
        """Handle start order button click"""
        logger.info("Start order clicked")
        
        # Check if device can accept orders
        from ...agent.offline import offline_manager
        if not offline_manager.can_accept_orders():
            logger.warning("Cannot accept orders - device offline")
            self.main_window.show_page("out_of_service", reason="network")
            return
        
        # Go to menu page
        self.main_window.show_page("menu")
        self.start_order_clicked.emit()
    
    def on_maintenance_area_clicked(self):
        """Handle maintenance area click"""
        self.maintenance_press_count += 1
        logger.debug(f"Maintenance area clicked {self.maintenance_press_count} times")
        
        # Start or restart timer for reset
        self.maintenance_timer.start(3000)  # 3 seconds
        
        # Check if enough clicks
        if self.maintenance_press_count >= 3:
            logger.info("Maintenance access requested")
            self.maintenance_requested.emit()
            self.main_window.show_page("maintenance")
            self.maintenance_press_count = 0
            self.maintenance_timer.stop()
    
    def reset_maintenance_count(self):
        """Reset maintenance click count"""
        self.maintenance_press_count = 0
        self.maintenance_timer.stop()
    
    def periodic_update(self):
        """Periodic update"""
        # Check if device is still operational
        pass
    
    def mousePressEvent(self, event):
        """Handle mouse press (reset screensaver timer)"""
        self.start_screensaver_timer()
        super().mousePressEvent(event)