import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
from ..storage.db import db
from ..storage.models import Recipe, RecipePackage
from ..config import config
from ..utils.time import utc_now
from ..utils.crypto import verify_file_hash, md5_hash
from ..utils.sse import event_bus, EVENT_RECIPE_UPDATED
from ..backend.client import backend_client

class RecipeManager:
    """Manages recipe packages, downloads, and local indexing"""
    
    def __init__(self):
        self.recipes: List[Recipe] = []
        self.current_package_version = None
        self._load_recipes()
    
    def _load_recipes(self):
        """Load recipes from database"""
        try:
            self.recipes = db.get_active_recipes()
            logger.info(f"Loaded {len(self.recipes)} recipes from database")
            
            if not self.recipes:
                # Load default recipes if none exist
                self._create_default_recipes()
        
        except Exception as e:
            logger.error(f"Failed to load recipes: {e}")
            self._create_default_recipes()
    
    def _create_default_recipes(self):
        """Create default recipes for demo"""
        default_recipes = [
            Recipe(
                id=201,
                name="美式咖啡",
                price=12.0,
                category="hot",
                description="经典美式咖啡，香醇浓郁",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A", 
                        "amount": 15,
                        "unit": "g",
                        "duration_ms": 4000
                    },
                    {
                        "action": "brew",
                        "water_ml": 200,
                        "duration_ms": 30000
                    }
                ],
                materials={"BEAN_A": 15.0, "WATER": 200.0},
                temperature="hot"
            ),
            Recipe(
                id=202,
                name="拿铁",
                price=18.0,
                category="hot",
                description="香浓拿铁，奶香浓郁",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A",
                        "amount": 12,
                        "unit": "g", 
                        "duration_ms": 3500
                    },
                    {
                        "action": "brew",
                        "water_ml": 60,
                        "duration_ms": 25000
                    },
                    {
                        "action": "add_powder",
                        "bin": "MILK_POWDER",
                        "amount": 8,
                        "unit": "g",
                        "duration_ms": 2000
                    },
                    {
                        "action": "mix",
                        "duration_ms": 5000
                    }
                ],
                materials={"BEAN_A": 12.0, "MILK_POWDER": 8.0, "WATER": 60.0},
                temperature="hot"
            ),
            Recipe(
                id=203,
                name="卡布奇诺",
                price=16.0,
                category="hot",
                description="经典卡布奇诺，泡沫丰富",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A",
                        "amount": 10,
                        "unit": "g",
                        "duration_ms": 3000
                    },
                    {
                        "action": "brew", 
                        "water_ml": 40,
                        "duration_ms": 20000
                    },
                    {
                        "action": "add_powder",
                        "bin": "MILK_POWDER",
                        "amount": 6,
                        "unit": "g",
                        "duration_ms": 2000
                    },
                    {
                        "action": "mix",
                        "duration_ms": 8000
                    }
                ],
                materials={"BEAN_A": 10.0, "MILK_POWDER": 6.0, "WATER": 40.0},
                temperature="hot"
            ),
            Recipe(
                id=204,
                name="浓缩咖啡",
                price=10.0,
                category="hot",
                description="浓缩咖啡，浓郁醇厚",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A",
                        "amount": 8,
                        "unit": "g",
                        "duration_ms": 2500
                    },
                    {
                        "action": "brew",
                        "water_ml": 30,
                        "duration_ms": 18000
                    }
                ],
                materials={"BEAN_A": 8.0, "WATER": 30.0},
                temperature="hot"
            ),
            Recipe(
                id=205,
                name="摩卡",
                price=20.0,
                category="hot", 
                description="巧克力摩卡，甜美香浓",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A",
                        "amount": 12,
                        "unit": "g",
                        "duration_ms": 3500
                    },
                    {
                        "action": "brew",
                        "water_ml": 50,
                        "duration_ms": 22000
                    },
                    {
                        "action": "add_powder",
                        "bin": "MILK_POWDER",
                        "amount": 8,
                        "unit": "g",
                        "duration_ms": 2000
                    },
                    {
                        "action": "add_powder",
                        "bin": "SUGAR",
                        "amount": 5,
                        "unit": "g",
                        "duration_ms": 1500
                    },
                    {
                        "action": "mix",
                        "duration_ms": 6000
                    }
                ],
                materials={"BEAN_A": 12.0, "MILK_POWDER": 8.0, "SUGAR": 5.0, "WATER": 50.0},
                temperature="hot"
            ),
            Recipe(
                id=206,
                name="冰美式",
                price=14.0,
                category="cold",
                description="冰爽美式，夏日必选",
                steps=[
                    {
                        "action": "grind",
                        "bin": "BEAN_A",
                        "amount": 16,
                        "unit": "g",
                        "duration_ms": 4000
                    },
                    {
                        "action": "brew",
                        "water_ml": 100,
                        "duration_ms": 25000
                    },
                    {
                        "action": "pour",
                        "water_ml": 100,
                        "duration_ms": 3000
                    }
                ],
                materials={"BEAN_A": 16.0, "WATER": 200.0},
                temperature="cold"
            )
        ]
        
        # Save to database
        db.save_recipes(default_recipes, "default_1.0.0")
        self.recipes = default_recipes
        self.current_package_version = "default_1.0.0"
        
        logger.info(f"Created {len(default_recipes)} default recipes")
    
    def get_recipes(self) -> List[Recipe]:
        """Get all active recipes"""
        return self.recipes.copy()
    
    def get_recipe_by_id(self, recipe_id: int) -> Optional[Recipe]:
        """Get recipe by ID"""
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe
        return None
    
    def get_recipes_by_category(self, category: str) -> List[Recipe]:
        """Get recipes by category"""
        return [recipe for recipe in self.recipes if recipe.category == category]
    
    def get_available_recipes(self, material_availability: Dict[str, bool] = None) -> List[Recipe]:
        """Get recipes that are available based on material levels"""
        if material_availability is None:
            from .materials import material_manager
            available_recipes = []
            
            for recipe in self.recipes:
                if recipe.is_available:
                    availability = material_manager.check_recipe_availability(recipe.materials)
                    if all(availability.values()):
                        available_recipes.append(recipe)
            
            return available_recipes
        else:
            available_recipes = []
            for recipe in self.recipes:
                if recipe.is_available:
                    recipe_available = True
                    for material_code in recipe.materials:
                        if not material_availability.get(material_code, False):
                            recipe_available = False
                            break
                    if recipe_available:
                        available_recipes.append(recipe)
            return available_recipes
    
    async def download_recipe_package(self, package_url: str, expected_hash: str, 
                                    package_id: str, version: str) -> bool:
        """Download and install recipe package"""
        try:
            logger.info(f"Downloading recipe package {package_id} v{version} from {package_url}")
            
            # Download package
            package_data = await backend_client.download_file(package_url)
            
            # Verify hash
            actual_hash = md5_hash(package_data)
            if actual_hash.lower() != expected_hash.lower():
                logger.error(f"Package hash mismatch: expected {expected_hash}, got {actual_hash}")
                return False
            
            # Save package file
            package_dir = config.ASSETS_DIR / "recipes" / package_id
            package_dir.mkdir(parents=True, exist_ok=True)
            package_file = package_dir / f"{version}.json"
            
            with open(package_file, 'wb') as f:
                f.write(package_data)
            
            logger.info(f"Saved package to {package_file}")
            
            # Parse and install
            success = await self._install_package(package_file, package_id, version)
            
            if success:
                # Store package info
                package_info = RecipePackage(
                    package_id=package_id,
                    version=version,
                    download_url=package_url,
                    md5_hash=expected_hash,
                    downloaded_at=utc_now(),
                    installed_at=utc_now(),
                    is_active=True
                )
                
                # Save to database (would need to add this table)
                logger.info(f"Successfully installed recipe package {package_id} v{version}")
                
                # Emit update event
                event_bus.emit(EVENT_RECIPE_UPDATED, {
                    "package_id": package_id,
                    "version": version,
                    "recipe_count": len(self.recipes)
                })
            
            return success
        
        except Exception as e:
            logger.error(f"Failed to download recipe package: {e}")
            return False
    
    async def _install_package(self, package_file: Path, package_id: str, version: str) -> bool:
        """Install recipe package from file"""
        try:
            with open(package_file, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Validate package structure
            if "recipes" not in package_data:
                logger.error("Invalid package: missing 'recipes' field")
                return False
            
            # Parse recipes
            new_recipes = []
            for recipe_data in package_data["recipes"]:
                try:
                    recipe = Recipe(**recipe_data)
                    new_recipes.append(recipe)
                except Exception as e:
                    logger.error(f"Invalid recipe in package: {e}")
                    return False
            
            # Install recipes
            db.save_recipes(new_recipes, version)
            self.recipes = new_recipes
            self.current_package_version = version
            
            logger.info(f"Installed {len(new_recipes)} recipes from package {package_id}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to install package: {e}")
            return False
    
    def validate_recipe(self, recipe: Recipe) -> List[str]:
        """Validate recipe structure and requirements"""
        errors = []
        
        if not recipe.name:
            errors.append("Recipe name is required")
        
        if recipe.price <= 0:
            errors.append("Recipe price must be positive")
        
        if not recipe.steps:
            errors.append("Recipe must have at least one step")
        
        if not recipe.materials:
            errors.append("Recipe must specify required materials")
        
        # Validate steps
        for i, step in enumerate(recipe.steps):
            if "action" not in step:
                errors.append(f"Step {i+1}: action is required")
            
            if step.get("action") in ["grind", "add_powder"] and "bin" not in step:
                errors.append(f"Step {i+1}: bin is required for {step.get('action')}")
            
            if step.get("duration_ms", 0) <= 0:
                errors.append(f"Step {i+1}: duration_ms must be positive")
        
        # Validate materials match steps
        step_materials = {}
        for step in recipe.steps:
            if "bin" in step and "amount" in step:
                bin_material = step["bin"]
                amount = step["amount"]
                step_materials[bin_material] = step_materials.get(bin_material, 0) + amount
        
        for material, required in recipe.materials.items():
            if material not in step_materials:
                errors.append(f"Material {material} specified but not used in steps")
            elif abs(step_materials[material] - required) > 0.1:
                errors.append(f"Material {material}: step total {step_materials[material]} != required {required}")
        
        return errors
    
    def get_recipe_categories(self) -> List[str]:
        """Get all available recipe categories"""
        categories = set()
        for recipe in self.recipes:
            if recipe.category:
                categories.add(recipe.category)
        return sorted(list(categories))
    
    def search_recipes(self, query: str) -> List[Recipe]:
        """Search recipes by name or description"""
        query = query.lower()
        results = []
        
        for recipe in self.recipes:
            if (query in recipe.name.lower() or 
                (recipe.description and query in recipe.description.lower())):
                results.append(recipe)
        
        return results
    
    def get_recipe_summary(self) -> Dict[str, Any]:
        """Get recipe summary for UI"""
        total_recipes = len(self.recipes)
        available_recipes = len(self.get_available_recipes())
        categories = self.get_recipe_categories()
        
        return {
            "total_recipes": total_recipes,
            "available_recipes": available_recipes,
            "unavailable_recipes": total_recipes - available_recipes,
            "categories": categories,
            "current_version": self.current_package_version
        }

# Global recipe manager
recipe_manager = RecipeManager()