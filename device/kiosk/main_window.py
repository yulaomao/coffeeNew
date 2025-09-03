from PySide6.QtWidgets import QMainWindow, QStackedWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, Signal, QThread, QObject
from PySide6.QtGui import QPalette, QColor
from loguru import logger
from ..config import config
from ..utils.i18n import i18n, t
from ..utils.sse import event_bus, EVENT_UI_PAGE_CHANGED
from ..agent.supervisor import agent_supervisor

# Import all page widgets (will create these)
from .widgets.idle import IdlePage
from .widgets.menu import MenuPage
from .widgets.product_detail import ProductDetailPage
from .widgets.confirm import ConfirmPage
from .widgets.payment import PaymentPage
from .widgets.qr import QRPage
from .widgets.brewing import BrewingPage
from .widgets.done import DonePage
from .widgets.out_of_service import OutOfServicePage
from .widgets.maintenance.entry import MaintenanceEntryPage

class CoffeeMachineMainWindow(QMainWindow):
    """Main window for coffee machine UI"""
    
    # Signals
    page_changed = Signal(str)
    
    def __init__(self):
        super().__init__()
        self.current_page = "idle"
        self.pages = {}
        
        self.init_ui()
        self.setup_pages()
        self.setup_timers()
        self.connect_events()
        
        # Start with idle page
        self.show_page("idle")
    
    def init_ui(self):
        """Initialize main UI"""
        self.setWindowTitle(t("app_name", "智能咖啡机"))
        self.setFixedSize(config.UI_SCREEN_WIDTH, config.UI_SCREEN_HEIGHT)
        
        # Set window flags for kiosk mode
        if config.UI_FULLSCREEN:
            self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        
        # Setup color scheme
        self.setup_theme()
        
        # Central widget with stacked layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Stacked widget for pages
        self.stacked_widget = QStackedWidget()
        self.layout.addWidget(self.stacked_widget)
    
    def setup_theme(self):
        """Setup UI theme"""
        palette = QPalette()
        
        # Light theme colors
        palette.setColor(QPalette.Window, QColor(248, 249, 250))
        palette.setColor(QPalette.WindowText, QColor(33, 37, 41))
        palette.setColor(QPalette.Base, QColor(255, 255, 255))
        palette.setColor(QPalette.AlternateBase, QColor(233, 236, 239))
        palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ToolTipText, QColor(33, 37, 41))
        palette.setColor(QPalette.Text, QColor(33, 37, 41))
        palette.setColor(QPalette.Button, QColor(248, 249, 250))
        palette.setColor(QPalette.ButtonText, QColor(33, 37, 41))
        palette.setColor(QPalette.BrightText, QColor(220, 53, 69))
        palette.setColor(QPalette.Link, QColor(0, 123, 255))
        palette.setColor(QPalette.Highlight, QColor(0, 123, 255))
        palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
        
        self.setPalette(palette)
        
        # Set stylesheet for custom styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            
            QPushButton {
                background-color: #007bff;
                border: none;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            
            QPushButton:hover {
                background-color: #0056b3;
            }
            
            QPushButton:pressed {
                background-color: #004085;
            }
            
            QPushButton:disabled {
                background-color: #6c757d;
            }
            
            QLabel {
                color: #212529;
            }
            
            .title {
                font-size: 24px;
                font-weight: bold;
                color: #212529;
            }
            
            .subtitle {
                font-size: 18px;
                color: #6c757d;
            }
            
            .price {
                font-size: 20px;
                font-weight: bold;
                color: #28a745;
            }
            
            .error {
                color: #dc3545;
            }
            
            .warning {
                color: #ffc107;
            }
            
            .success {
                color: #28a745;
            }
        """)
    
    def setup_pages(self):
        """Setup all UI pages"""
        logger.info("Setting up UI pages...")
        
        try:
            # Create page instances
            self.pages["idle"] = IdlePage(self)
            self.pages["menu"] = MenuPage(self)
            self.pages["product_detail"] = ProductDetailPage(self)
            self.pages["confirm"] = ConfirmPage(self)
            self.pages["payment"] = PaymentPage(self)
            self.pages["qr"] = QRPage(self)
            self.pages["brewing"] = BrewingPage(self)
            self.pages["done"] = DonePage(self)
            self.pages["out_of_service"] = OutOfServicePage(self)
            self.pages["maintenance"] = MaintenanceEntryPage(self)
            
            # Add pages to stacked widget
            for page_name, page_widget in self.pages.items():
                self.stacked_widget.addWidget(page_widget)
                logger.debug(f"Added page: {page_name}")
            
            logger.info(f"Setup {len(self.pages)} UI pages")
        
        except Exception as e:
            logger.error(f"Failed to setup pages: {e}")
            # Create a minimal error page if setup fails
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            from PySide6.QtWidgets import QLabel
            error_label = QLabel("UI Setup Error")
            error_label.setAlignment(Qt.AlignCenter)
            error_layout.addWidget(error_label)
            self.stacked_widget.addWidget(error_widget)
    
    def setup_timers(self):
        """Setup periodic timers"""
        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.periodic_update)
        self.update_timer.start(1000)  # 1 second
        
        # Timer for idle timeout
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.handle_idle_timeout)
        self.idle_timer.setSingleShot(True)
    
    def connect_events(self):
        """Connect to event bus"""
        # Listen for various events
        event_bus.subscribe("device_status_changed", self.on_device_status_changed)
        event_bus.subscribe("material_updated", self.on_material_updated)
        event_bus.subscribe("order_status_changed", self.on_order_status_changed)
        event_bus.subscribe("payment_status_changed", self.on_payment_status_changed)
        event_bus.subscribe("network_status_changed", self.on_network_status_changed)
        
        # Connect page navigation signals
        self.page_changed.connect(self.on_page_changed)
    
    def show_page(self, page_name: str, **kwargs):
        """Show specific page"""
        if page_name not in self.pages:
            logger.error(f"Page not found: {page_name}")
            return
        
        try:
            # Update current page
            old_page = self.current_page
            self.current_page = page_name
            
            # Get page widget
            page_widget = self.pages[page_name]
            
            # Call page setup if available
            if hasattr(page_widget, 'setup_page'):
                page_widget.setup_page(**kwargs)
            
            # Show page
            self.stacked_widget.setCurrentWidget(page_widget)
            
            # Reset idle timer for customer pages
            if page_name in ["idle", "menu", "product_detail", "confirm", "payment", "qr", "brewing", "done"]:
                self.reset_idle_timer()
            else:
                self.idle_timer.stop()
            
            # Emit events
            self.page_changed.emit(page_name)
            event_bus.emit(EVENT_UI_PAGE_CHANGED, {
                "from_page": old_page,
                "to_page": page_name,
                "kwargs": kwargs
            })
            
            logger.info(f"Showed page: {page_name}")
        
        except Exception as e:
            logger.error(f"Failed to show page {page_name}: {e}")
    
    def reset_idle_timer(self):
        """Reset idle timer"""
        from ..constants import IDLE_TIMEOUT_SEC
        self.idle_timer.start(IDLE_TIMEOUT_SEC * 1000)
    
    def handle_idle_timeout(self):
        """Handle idle timeout"""
        if self.current_page != "idle" and self.current_page != "maintenance":
            logger.info("Idle timeout, returning to idle page")
            self.show_page("idle")
    
    def periodic_update(self):
        """Periodic update handler"""
        try:
            # Update current page if it has update method
            current_widget = self.stacked_widget.currentWidget()
            if hasattr(current_widget, 'periodic_update'):
                current_widget.periodic_update()
            
            # Check if device should show out of service
            self.check_service_status()
        
        except Exception as e:
            logger.error(f"Periodic update error: {e}")
    
    def check_service_status(self):
        """Check if device should show out of service page"""
        try:
            from ..agent.offline import offline_manager
            from ..agent.materials import material_manager
            from ..agent.state import state_manager
            
            # Check offline status
            if offline_manager.is_offline:
                if self.current_page not in ["out_of_service", "maintenance"]:
                    self.show_page("out_of_service", reason="network")
                return
            
            # Check material status
            empty_bins = material_manager.get_empty_bins()
            if empty_bins:
                if self.current_page not in ["out_of_service", "maintenance"]:
                    self.show_page("out_of_service", reason="materials")
                return
            
            # Check hardware status
            current_status = state_manager.get_current_status()
            if current_status == "error":
                if self.current_page not in ["out_of_service", "maintenance"]:
                    self.show_page("out_of_service", reason="error")
                return
            
            # If was showing out of service but now OK, return to idle
            if self.current_page == "out_of_service":
                self.show_page("idle")
        
        except Exception as e:
            logger.error(f"Service status check error: {e}")
    
    def on_page_changed(self, page_name: str):
        """Handle page change"""
        logger.debug(f"Page changed to: {page_name}")
    
    def on_device_status_changed(self, event):
        """Handle device status change"""
        pass
    
    def on_material_updated(self, event):
        """Handle material update"""
        pass
    
    def on_order_status_changed(self, event):
        """Handle order status change"""
        pass
    
    def on_payment_status_changed(self, event):
        """Handle payment status change"""
        pass
    
    def on_network_status_changed(self, event):
        """Handle network status change"""
        pass
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # ESC key to exit fullscreen (development mode)
        if event.key() == Qt.Key_Escape and config.UI_FULLSCREEN:
            self.showNormal()
        
        # F11 to toggle fullscreen
        elif event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()
            else:
                self.showFullScreen()
        
        super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle close event"""
        logger.info("Main window closing")
        event.accept()