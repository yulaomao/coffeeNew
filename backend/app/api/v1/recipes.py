from flask import request
from flask_login import login_required
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.models import Recipe, RecipePackage
from app.extensions import db


@bp.route('/recipes', methods=['GET'])
@login_required
def list_recipes():
    """List recipes"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        enabled_only = request.args.get('enabled_only', type=bool, default=False)
        
        query = db.session.query(Recipe)
        
        if enabled_only:
            query = query.filter(Recipe.enabled == True)
        
        total = query.count()
        recipes = query.order_by(Recipe.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        recipe_data = [recipe.to_dict() for recipe in recipes]
        
        return paginated_response(recipe_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list recipes: {str(e)}",
            status_code=500
        )


@bp.route('/recipes/packages', methods=['GET'])
@login_required
def list_recipe_packages():
    """List recipe packages"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        
        query = db.session.query(RecipePackage).order_by(RecipePackage.created_at.desc())
        
        total = query.count()
        packages = query.offset((page - 1) * page_size).limit(page_size).all()
        
        package_data = [package.to_dict() for package in packages]
        
        return paginated_response(package_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list packages: {str(e)}",
            status_code=500
        )