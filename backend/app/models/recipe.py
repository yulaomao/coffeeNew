from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Numeric
from app.extensions import db


class Recipe(db.Model):
    __tablename__ = 'recipes'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    version = Column(String(50))
    schema = Column(JSON)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    def __repr__(self):
        return f'<Recipe {self.name} v{self.version}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'schema': self.schema,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class RecipePackage(db.Model):
    __tablename__ = 'recipe_packages'
    
    package_id = Column(String(100), primary_key=True)
    version = Column(String(50))
    package_url = Column(String(500))
    md5 = Column(String(32))
    size = Column(Numeric(15, 0))  # Size in bytes
    manifest = Column(JSON)
    created_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    creator = db.relationship('User', back_populates='created_packages')
    
    def __repr__(self):
        return f'<RecipePackage {self.package_id} v{self.version}>'
    
    def to_dict(self):
        return {
            'package_id': self.package_id,
            'version': self.version,
            'package_url': self.package_url,
            'md5': self.md5,
            'size': int(self.size) if self.size else None,
            'manifest': self.manifest,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }