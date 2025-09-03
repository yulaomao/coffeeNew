from enum import Enum as PyEnum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from app.models import BaseModel


class UserRole(PyEnum):
    ADMIN = 'admin'
    OPS = 'ops' 
    VIEWER = 'viewer'


class User(UserMixin, BaseModel):
    __tablename__ = 'users'
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.VIEWER.value)
    active = Column(Boolean, default=True, nullable=False)
    
    # Add constraint for role enum
    __table_args__ = (
        CheckConstraint(
            role.in_([role.value for role in UserRole]),
            name='ck_user_role'
        ),
    )
    
    # Relationships
    created_packages = relationship('RecipePackage', back_populates='creator', lazy='dynamic')
    created_batches = relationship('CommandBatch', back_populates='creator', lazy='dynamic')
    operation_logs = relationship('OperationLog', back_populates='actor', lazy='dynamic')
    
    def set_password(self, password):
        """Set password hash."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash."""
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """Check if user is admin."""
        return self.role == UserRole.ADMIN.value
    
    def is_ops(self):
        """Check if user has ops role or higher."""
        return self.role in [UserRole.ADMIN.value, UserRole.OPS.value]
    
    def __repr__(self):
        return f'<User {self.email}>'