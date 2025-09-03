from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, declared_attr
from app import db

# Base model class with common fields
class BaseModel(db.Model):
    __abstract__ = True
    # By default, models get an auto-increment integer primary key `id`.
    # Models that define their own natural primary key should set __use_id_pk__ = False.
    __use_id_pk__ = True

    @declared_attr
    def id(cls):  # type: ignore[override]
        if getattr(cls, '__use_id_pk__', True):
            return Column(Integer, primary_key=True, autoincrement=True)
        # If not using id PK, omit the column entirely
        return None  # type: ignore[return-value]

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

# Import models to register them with SQLAlchemy's mapper for string-based relationship() resolution
# Avoid circular import issues by placing at end of file
from .user import User  # noqa: E402,F401
from .merchant import Merchant  # noqa: E402,F401
from .location import Location  # noqa: E402,F401
from .device import Device  # noqa: E402,F401
from .device_bin import DeviceBin  # noqa: E402,F401
from .material_dictionary import MaterialDictionary  # noqa: E402,F401
from .order import Order  # noqa: E402,F401
from .order_item import OrderItem  # noqa: E402,F401
from .recipe import Recipe  # noqa: E402,F401
from .recipe_package import RecipePackage  # noqa: E402,F401
from .remote_command import RemoteCommand  # noqa: E402,F401
from .command_batch import CommandBatch  # noqa: E402,F401
from .alarm import Alarm  # noqa: E402,F401
from .operation_log import OperationLog  # noqa: E402,F401
from .task_job import TaskJob  # noqa: E402,F401