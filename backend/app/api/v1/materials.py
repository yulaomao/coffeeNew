from flask import request
from flask_login import login_required, current_user
from app.api.v1 import bp
from app.api.response import success_response, error_response, ErrorCode, paginated_response
from app.api.decorators import validate_json, require_role
from app.schemas.material import MaterialCreateRequest, MaterialUpdateRequest, MaterialImportRequest
from app.models import MaterialDictionary, DeviceBin
from app.extensions import db
from app.services.material_service import MaterialService


@bp.route('/materials', methods=['GET'])
@login_required
def list_materials():
    """List materials"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        enabled_only = request.args.get('enabled_only', type=bool, default=False)
        search = request.args.get('search', '').strip()
        
        query = db.session.query(MaterialDictionary)
        
        if enabled_only:
            query = query.filter(MaterialDictionary.enabled == True)
        
        if search:
            query = query.filter(
                MaterialDictionary.code.ilike(f'%{search}%') |
                MaterialDictionary.name.ilike(f'%{search}%')
            )
        
        total = query.count()
        materials = query.order_by(MaterialDictionary.code).offset((page - 1) * page_size).limit(page_size).all()
        
        material_data = [material.to_dict() for material in materials]
        
        return paginated_response(material_data, total, page, page_size)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to list materials: {str(e)}",
            status_code=500
        )


@bp.route('/materials', methods=['POST'])
@login_required
@validate_json(MaterialCreateRequest)
@require_role(['admin', 'ops'])
def create_material():
    """Create new material"""
    try:
        material_data = request.validated_json
        
        # Check if material code already exists
        existing = MaterialDictionary.query.filter_by(code=material_data.code).first()
        if existing:
            return error_response(
                ErrorCode.CONFLICT,
                "Material code already exists",
                status_code=409
            )
        
        material = MaterialDictionary(
            code=material_data.code,
            name=material_data.name,
            type=material_data.type,
            unit=material_data.unit,
            density=material_data.density,
            enabled=material_data.enabled
        )
        
        db.session.add(material)
        db.session.commit()
        
        return success_response(material.to_dict(), status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to create material: {str(e)}",
            status_code=500
        )


@bp.route('/materials/<int:material_id>', methods=['PUT'])
@login_required
@validate_json(MaterialUpdateRequest)
@require_role(['admin', 'ops'])
def update_material(material_id):
    """Update material"""
    try:
        material = MaterialDictionary.query.get(material_id)
        if not material:
            return error_response(
                ErrorCode.NOT_FOUND,
                "Material not found",
                status_code=404
            )
        
        update_data = request.validated_json
        
        if update_data.name is not None:
            material.name = update_data.name
        if update_data.type is not None:
            material.type = update_data.type
        if update_data.unit is not None:
            material.unit = update_data.unit
        if update_data.density is not None:
            material.density = update_data.density
        if update_data.enabled is not None:
            material.enabled = update_data.enabled
        
        db.session.commit()
        
        return success_response(material.to_dict())
        
    except Exception as e:
        db.session.rollback()
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to update material: {str(e)}",
            status_code=500
        )


@bp.route('/materials/import', methods=['POST'])
@login_required
@validate_json(MaterialImportRequest)
@require_role(['admin', 'ops'])
def import_materials():
    """Import materials from CSV data"""
    try:
        import_data = request.validated_json
        
        result = MaterialService.import_materials(
            materials_data=import_data.materials,
            overwrite_existing=import_data.overwrite_existing,
            imported_by=current_user.id
        )
        
        return success_response(result)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to import materials: {str(e)}",
            status_code=500
        )


@bp.route('/materials/export', methods=['GET'])
@login_required
@require_role(['admin', 'ops'])
def export_materials():
    """Export materials"""
    try:
        format_type = request.args.get('format', 'csv')
        enabled_only = request.args.get('enabled_only', type=bool, default=False)
        include_usage = request.args.get('include_usage_stats', type=bool, default=False)
        
        result = MaterialService.export_materials(
            format_type=format_type,
            enabled_only=enabled_only,
            include_usage_stats=include_usage,
            exported_by=current_user.id
        )
        
        return success_response(result)
        
    except Exception as e:
        return error_response(
            ErrorCode.INTERNAL_ERROR,
            f"Failed to export materials: {str(e)}",
            status_code=500
        )