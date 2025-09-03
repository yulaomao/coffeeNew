# Device status constants
DEVICE_STATUS_IDLE = "idle"
DEVICE_STATUS_BREWING = "brewing"
DEVICE_STATUS_MAINTENANCE = "maintenance"
DEVICE_STATUS_OUT_OF_SERVICE = "out_of_service"
DEVICE_STATUS_ERROR = "error"

# Command types
COMMAND_MAKE_PRODUCT = "make_product"
COMMAND_OPEN_DOOR = "open_door"
COMMAND_UPGRADE = "upgrade"
COMMAND_SYNC = "sync"
COMMAND_SET_PARAMS = "set_params"
COMMAND_RESTART = "restart"

# Command status
COMMAND_STATUS_PENDING = "pending"
COMMAND_STATUS_SENT = "sent"
COMMAND_STATUS_SUCCESS = "success"
COMMAND_STATUS_FAIL = "fail"

# Payment status
PAYMENT_STATUS_PENDING = "pending"
PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_FAILED = "failed"
PAYMENT_STATUS_CANCELED = "canceled"

# Order status
ORDER_STATUS_PENDING = "pending"
ORDER_STATUS_PAID = "paid"
ORDER_STATUS_BREWING = "brewing"
ORDER_STATUS_COMPLETED = "completed"
ORDER_STATUS_FAILED = "failed"
ORDER_STATUS_CANCELED = "canceled"

# Material units
UNIT_GRAM = "g"
UNIT_ML = "ml"
UNIT_PIECE = "piece"

# Recipe actions
ACTION_GRIND = "grind"
ACTION_BREW = "brew"
ACTION_ADD_POWDER = "add_powder"
ACTION_MIX = "mix"
ACTION_HEAT = "heat"
ACTION_POUR = "pour"

# Material codes
MATERIAL_BEAN_A = "BEAN_A"
MATERIAL_BEAN_B = "BEAN_B"
MATERIAL_MILK_POWDER = "MILK_POWDER"
MATERIAL_SUGAR = "SUGAR"
MATERIAL_WATER = "WATER"

# UI page names
PAGE_IDLE = "idle"
PAGE_MENU = "menu"
PAGE_PRODUCT_DETAIL = "product_detail"
PAGE_CONFIRM = "confirm"
PAGE_PAYMENT = "payment"
PAGE_QR = "qr"
PAGE_BREWING = "brewing"
PAGE_DONE = "done"
PAGE_OUT_OF_SERVICE = "out_of_service"
PAGE_MAINTENANCE = "maintenance"

# Maintenance PIN
DEFAULT_MAINTENANCE_PIN = "0000"

# Timeouts
QR_CODE_TIMEOUT_SEC = 300  # 5 minutes
BREWING_TIMEOUT_SEC = 120  # 2 minutes
DONE_PAGE_TIMEOUT_SEC = 10  # 10 seconds
IDLE_TIMEOUT_SEC = 30  # 30 seconds for screensaver

# HTTP timeouts
HTTP_CONNECT_TIMEOUT = 10.0
HTTP_READ_TIMEOUT = 30.0

# Retry settings
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2