from datetime import datetime, timezone
from app.models import MaterialDictionary, DeviceBin, OperationLog, TaskJob
from app.extensions import db
from sqlalchemy import func
import uuid
import csv
import io


class MaterialService:
    @staticmethod
    def import_materials(materials_data, overwrite_existing=False, imported_by=None):
        """Import materials from list of material data"""
        total_rows = len(materials_data)
        successful_rows = 0
        failed_rows = 0
        errors = []
        
        for i, material_data in enumerate(materials_data):
            try:
                # Check if material exists
                existing = MaterialDictionary.query.filter_by(code=material_data.code).first()
                
                if existing and not overwrite_existing:
                    errors.append({
                        "row": i + 1,
                        "code": material_data.code,
                        "error": "Material already exists"
                    })
                    failed_rows += 1
                    continue
                
                if existing:
                    # Update existing
                    existing.name = material_data.name
                    existing.type = material_data.type
                    existing.unit = material_data.unit
                    existing.density = material_data.density
                    existing.enabled = material_data.enabled
                    existing.updated_at = datetime.now(timezone.utc)
                else:
                    # Create new
                    material = MaterialDictionary(
                        code=material_data.code,
                        name=material_data.name,
                        type=material_data.type,
                        unit=material_data.unit,
                        density=material_data.density,
                        enabled=material_data.enabled
                    )
                    db.session.add(material)
                
                successful_rows += 1
                
            except Exception as e:
                errors.append({
                    "row": i + 1,
                    "code": getattr(material_data, 'code', 'unknown'),
                    "error": str(e)
                })
                failed_rows += 1
        
        try:
            db.session.commit()
            
            # Log the import
            if imported_by:
                log = OperationLog(
                    action="material_import",
                    target_type="material",
                    summary=f"Imported {successful_rows} materials",
                    payload_snip={
                        "total_rows": total_rows,
                        "successful": successful_rows,
                        "failed": failed_rows,
                        "overwrite_existing": overwrite_existing
                    },
                    source='backend',
                    actor_id=imported_by
                )
                db.session.add(log)
                db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return {
                "total_rows": total_rows,
                "successful_rows": 0,
                "failed_rows": total_rows,
                "errors": [{"error": f"Database error: {str(e)}"}]
            }
        
        return {
            "total_rows": total_rows,
            "successful_rows": successful_rows,
            "failed_rows": failed_rows,
            "errors": errors
        }
    
    @staticmethod
    def export_materials(format_type='csv', enabled_only=False, include_usage_stats=False, exported_by=None):
        """Export materials to specified format"""
        try:
            query = db.session.query(MaterialDictionary)
            
            if enabled_only:
                query = query.filter(MaterialDictionary.enabled == True)
            
            materials = query.order_by(MaterialDictionary.code).all()
            
            if format_type == 'csv':
                return MaterialService._export_materials_csv(materials, include_usage_stats, exported_by)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
            
        except Exception as e:
            raise Exception(f"Export failed: {str(e)}")
    
    @staticmethod
    def _export_materials_csv(materials, include_usage_stats=False, exported_by=None):
        """Export materials to CSV format"""
        output = io.StringIO()
        
        # Define CSV headers
        headers = ['code', 'name', 'type', 'unit', 'density', 'enabled']
        if include_usage_stats:
            headers.extend(['total_bins', 'active_devices', 'total_capacity', 'total_remaining'])
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        for material in materials:
            row = {
                'code': material.code,
                'name': material.name,
                'type': material.type or '',
                'unit': material.unit or '',
                'density': float(material.density) if material.density else '',
                'enabled': material.enabled
            }
            
            if include_usage_stats:
                # Calculate usage statistics
                bins = DeviceBin.query.filter_by(material_code=material.code).all()
                row['total_bins'] = len(bins)
                row['active_devices'] = len(set(bin.device_id for bin in bins))
                row['total_capacity'] = sum(float(bin.capacity or 0) for bin in bins)
                row['total_remaining'] = sum(float(bin.remaining or 0) for bin in bins)
            
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Log the export
        if exported_by:
            log = OperationLog(
                action="material_export",
                target_type="material",
                summary=f"Exported {len(materials)} materials",
                payload_snip={
                    "format": "csv",
                    "count": len(materials),
                    "include_usage_stats": include_usage_stats
                },
                source='backend',
                actor_id=exported_by
            )
            db.session.add(log)
            db.session.commit()
        
        return {
            "format": "csv",
            "content": csv_content,
            "filename": f"materials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "size": len(csv_content.encode('utf-8'))
        }
    
    @staticmethod
    def get_material_usage_stats(material_code):
        """Get usage statistics for a material"""
        material = MaterialDictionary.query.filter_by(code=material_code).first()
        if not material:
            return None
        
        # Get all bins using this material
        bins = DeviceBin.query.filter_by(material_code=material_code).all()
        
        # Calculate statistics
        total_bins = len(bins)
        active_devices = len(set(bin.device_id for bin in bins))
        total_capacity = sum(float(bin.capacity or 0) for bin in bins)
        total_remaining = sum(float(bin.remaining or 0) for bin in bins)
        
        # Calculate low material bins
        low_bins = []
        for bin_obj in bins:
            if bin_obj.remaining and bin_obj.capacity and bin_obj.threshold_low_pct:
                threshold = bin_obj.capacity * bin_obj.threshold_low_pct / 100
                if bin_obj.remaining < threshold:
                    low_bins.append(bin_obj)
        
        return {
            "material": material.to_dict(),
            "usage_stats": {
                "total_bins": total_bins,
                "active_devices": active_devices,
                "total_capacity": total_capacity,
                "total_remaining": total_remaining,
                "utilization_rate": total_remaining / total_capacity if total_capacity > 0 else 0,
                "low_material_bins": len(low_bins),
                "low_bins_details": [bin_obj.to_dict() for bin_obj in low_bins]
            }
        }
    
    @staticmethod
    def get_materials_overview():
        """Get overview of all materials with usage statistics"""
        materials = MaterialDictionary.query.filter_by(enabled=True).all()
        
        overview = {
            "total_materials": len(materials),
            "materials_in_use": 0,
            "materials_low": 0,
            "total_devices": 0,
            "materials": []
        }
        
        device_ids = set()
        materials_with_low_stock = set()
        
        for material in materials:
            bins = DeviceBin.query.filter_by(material_code=material.code).all()
            
            if bins:
                overview["materials_in_use"] += 1
                
                # Track unique devices
                for bin_obj in bins:
                    device_ids.add(bin_obj.device_id)
                    
                    # Check for low stock
                    if bin_obj.remaining and bin_obj.capacity and bin_obj.threshold_low_pct:
                        threshold = bin_obj.capacity * bin_obj.threshold_low_pct / 100
                        if bin_obj.remaining < threshold:
                            materials_with_low_stock.add(material.code)
            
            total_capacity = sum(float(bin_obj.capacity or 0) for bin_obj in bins)
            total_remaining = sum(float(bin_obj.remaining or 0) for bin_obj in bins)
            
            overview["materials"].append({
                "code": material.code,
                "name": material.name,
                "bins_count": len(bins),
                "total_capacity": total_capacity,
                "total_remaining": total_remaining,
                "utilization_rate": total_remaining / total_capacity if total_capacity > 0 else 0
            })
        
        overview["total_devices"] = len(device_ids)
        overview["materials_low"] = len(materials_with_low_stock)
        
        return overview