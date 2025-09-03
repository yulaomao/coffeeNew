from sqlalchemy import Column, String, Integer, ForeignKey, JSON, BigInteger
from sqlalchemy.orm import relationship
from app.models import BaseModel


class RecipePackage(BaseModel):
    __tablename__ = 'recipe_packages'
    
    package_id = Column(String(255), primary_key=True)  # Override id with package_id as PK
    version = Column(String(50), nullable=False)
    package_url = Column(String(500), nullable=False)
    md5 = Column(String(32), nullable=False)
    size = Column(BigInteger, nullable=False)
    manifest = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=True)
    
    # Relationships
    creator = relationship('User', back_populates='created_packages')
    recipe = relationship('Recipe', back_populates='packages')
    
    def __repr__(self):
        return f'<RecipePackage {self.package_id} v{self.version}>'