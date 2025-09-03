import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
import json
from datetime import datetime
from loguru import logger
from ..config import config
from ..utils.time import utc_now, iso_format, parse_iso
from .models import *

class Database:
    """SQLite database manager"""
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            config.ensure_directories()
            db_path = config.CACHE_DIR / "device.db"
        
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn
    
    def init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Key-value storage for config and simple data
            conn.execute("""
                CREATE TABLE IF NOT EXISTS kv (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT
                )
            """)
            
            # Orders storage
            conn.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    order_id TEXT PRIMARY KEY,
                    data TEXT,
                    status TEXT,
                    payment_status TEXT,
                    is_uploaded BOOLEAN DEFAULT FALSE,
                    created_at TEXT,
                    updated_at TEXT
                )
            """)
            
            # Command results queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS command_results (
                    command_id TEXT PRIMARY KEY,
                    data TEXT,
                    is_uploaded BOOLEAN DEFAULT FALSE,
                    created_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT
                )
            """)
            
            # Material snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS material_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    is_uploaded BOOLEAN DEFAULT FALSE,
                    created_at TEXT
                )
            """)
            
            # Device status snapshots
            conn.execute("""
                CREATE TABLE IF NOT EXISTS status_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT,
                    is_uploaded BOOLEAN DEFAULT FALSE,
                    created_at TEXT
                )
            """)
            
            # Bins current state
            conn.execute("""
                CREATE TABLE IF NOT EXISTS bins (
                    bin_index INTEGER PRIMARY KEY,
                    material_code TEXT,
                    remaining REAL,
                    capacity REAL,
                    unit TEXT,
                    threshold_low_pct INTEGER,
                    updated_at TEXT
                )
            """)
            
            # Recipes index
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipes (
                    recipe_id INTEGER PRIMARY KEY,
                    name TEXT,
                    data TEXT,
                    package_version TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    updated_at TEXT
                )
            """)
            
            # Recipe packages
            conn.execute("""
                CREATE TABLE IF NOT EXISTS recipe_packages (
                    package_id TEXT PRIMARY KEY,
                    version TEXT,
                    data TEXT,
                    downloaded_at TEXT,
                    installed_at TEXT,
                    is_active BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Operation logs
            conn.execute("""
                CREATE TABLE IF NOT EXISTS operation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    operation TEXT,
                    user TEXT,
                    details TEXT,
                    device_id TEXT
                )
            """)
            
            # Upload queue for various items
            conn.execute("""
                CREATE TABLE IF NOT EXISTS upload_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_type TEXT,
                    item_id TEXT,
                    payload TEXT,
                    created_at TEXT,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    max_retries INTEGER DEFAULT 3
                )
            """)
            
            conn.commit()
        
        logger.info(f"Database initialized: {self.db_path}")
    
    # Key-Value operations
    def set_kv(self, key: str, value: Any):
        """Set key-value pair"""
        with self.get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO kv (key, value, updated_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), iso_format(utc_now()))
            )
    
    def get_kv(self, key: str, default: Any = None) -> Any:
        """Get value by key"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM kv WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["value"])
                except json.JSONDecodeError:
                    return row["value"]
            return default
    
    def delete_kv(self, key: str):
        """Delete key-value pair"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM kv WHERE key = ?", (key,))
    
    # Order operations
    def save_order(self, order: Order):
        """Save order to database"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO orders 
                (order_id, data, status, payment_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                order.order_id,
                order.model_dump_json(),
                order.status,
                order.payment_status,
                iso_format(order.created_at),
                iso_format(utc_now())
            ))
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT data FROM orders WHERE order_id = ?", (order_id,))
            row = cursor.fetchone()
            if row:
                return Order.model_validate_json(row["data"])
            return None
    
    def get_unuploaded_orders(self) -> List[Order]:
        """Get orders that haven't been uploaded to backend"""
        orders = []
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT data FROM orders WHERE is_uploaded = FALSE")
            for row in cursor.fetchall():
                try:
                    order = Order.model_validate_json(row["data"])
                    orders.append(order)
                except Exception as e:
                    logger.error(f"Failed to parse order data: {e}")
        return orders
    
    def mark_order_uploaded(self, order_id: str):
        """Mark order as uploaded"""
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE orders SET is_uploaded = TRUE WHERE order_id = ?",
                (order_id,)
            )
    
    # Bin operations  
    def save_bins(self, bins: List[Bin]):
        """Save bins state"""
        with self.get_connection() as conn:
            for bin_data in bins:
                conn.execute("""
                    INSERT OR REPLACE INTO bins 
                    (bin_index, material_code, remaining, capacity, unit, threshold_low_pct, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    bin_data.bin_index,
                    bin_data.material_code,
                    bin_data.remaining,
                    bin_data.capacity,
                    bin_data.unit,
                    bin_data.threshold_low_pct,
                    iso_format(utc_now())
                ))
    
    def get_bins(self) -> List[Bin]:
        """Get all bins"""
        bins = []
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT bin_index, material_code, remaining, capacity, unit, 
                       threshold_low_pct, updated_at 
                FROM bins ORDER BY bin_index
            """)
            for row in cursor.fetchall():
                bin_data = Bin(
                    bin_index=row["bin_index"],
                    material_code=row["material_code"],
                    remaining=row["remaining"],
                    capacity=row["capacity"],
                    unit=row["unit"],
                    threshold_low_pct=row["threshold_low_pct"],
                    last_updated=parse_iso(row["updated_at"]) or utc_now()
                )
                bins.append(bin_data)
        return bins
    
    # Recipe operations
    def save_recipes(self, recipes: List[Recipe], package_version: str):
        """Save recipes from package"""
        with self.get_connection() as conn:
            # First mark existing recipes as inactive
            conn.execute("UPDATE recipes SET is_active = FALSE")
            
            # Insert new recipes
            for recipe in recipes:
                conn.execute("""
                    INSERT OR REPLACE INTO recipes 
                    (recipe_id, name, data, package_version, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    recipe.id,
                    recipe.name,
                    recipe.model_dump_json(),
                    package_version,
                    True,
                    iso_format(utc_now())
                ))
    
    def get_active_recipes(self) -> List[Recipe]:
        """Get active recipes"""
        recipes = []
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT data FROM recipes WHERE is_active = TRUE")
            for row in cursor.fetchall():
                try:
                    recipe = Recipe.model_validate_json(row["data"])
                    recipes.append(recipe)
                except Exception as e:
                    logger.error(f"Failed to parse recipe data: {e}")
        return recipes
    
    # Queue operations
    def add_to_queue(self, item: QueueItem):
        """Add item to upload queue"""
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO upload_queue 
                (item_type, item_id, payload, created_at, max_retries)
                VALUES (?, ?, ?, ?, ?)
            """, (
                item.item_type,
                item.item_id,
                json.dumps(item.payload),
                iso_format(item.created_at),
                item.max_retries
            ))
    
    def get_pending_queue_items(self, item_type: Optional[str] = None) -> List[QueueItem]:
        """Get pending queue items"""
        items = []
        with self.get_connection() as conn:
            if item_type:
                cursor = conn.execute("""
                    SELECT * FROM upload_queue 
                    WHERE item_type = ? AND retry_count < max_retries
                    ORDER BY created_at
                """, (item_type,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM upload_queue 
                    WHERE retry_count < max_retries
                    ORDER BY created_at
                """)
            
            for row in cursor.fetchall():
                try:
                    item = QueueItem(
                        id=row["id"],
                        item_type=row["item_type"],
                        item_id=row["item_id"],
                        payload=json.loads(row["payload"]),
                        created_at=parse_iso(row["created_at"]) or utc_now(),
                        retry_count=row["retry_count"],
                        last_error=row["last_error"],
                        max_retries=row["max_retries"]
                    )
                    items.append(item)
                except Exception as e:
                    logger.error(f"Failed to parse queue item: {e}")
        
        return items
    
    def mark_queue_item_processed(self, item_id: int):
        """Mark queue item as processed (delete it)"""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM upload_queue WHERE id = ?", (item_id,))
    
    def increment_queue_retry(self, item_id: int, error_message: str):
        """Increment retry count for queue item"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE upload_queue 
                SET retry_count = retry_count + 1, last_error = ?
                WHERE id = ?
            """, (error_message, item_id))
    
    # Operation log
    def add_operation_log(self, operation: str, user: str = "system", 
                         details: Dict[str, Any] = None, device_id: str = ""):
        """Add operation log entry"""
        if details is None:
            details = {}
        
        with self.get_connection() as conn:
            conn.execute("""
                INSERT INTO operation_logs 
                (timestamp, operation, user, details, device_id)
                VALUES (?, ?, ?, ?, ?)
            """, (
                iso_format(utc_now()),
                operation,
                user,
                json.dumps(details),
                device_id
            ))
    
    def get_recent_logs(self, limit: int = 200) -> List[OperationLog]:
        """Get recent operation logs"""
        logs = []
        with self.get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM operation_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            for row in cursor.fetchall():
                try:
                    log = OperationLog(
                        id=row["id"],
                        timestamp=parse_iso(row["timestamp"]) or utc_now(),
                        operation=row["operation"],
                        user=row["user"],
                        details=json.loads(row["details"]) if row["details"] else {},
                        device_id=row["device_id"]
                    )
                    logs.append(log)
                except Exception as e:
                    logger.error(f"Failed to parse log entry: {e}")
        
        return logs

# Global database instance
db = Database()