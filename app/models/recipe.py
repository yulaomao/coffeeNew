from sqlalchemy import Column, String, Integer, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models import BaseModel


class Recipe(BaseModel):
    __tablename__ = 'recipes'
    
    name = Column(String(255), nullable=False)
    version = Column(String(50), nullable=False)
    schema = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    packages = relationship('RecipePackage', back_populates='recipe', lazy='dynamic')
    
    def __repr__(self):
        return f'<Recipe {self.name} v{self.version}>'