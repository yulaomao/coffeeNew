from datetime import datetime, timezone
from app.workers.celery_app import celery
from app.models import TaskJob, Order, OrderItem, MaterialDictionary, DeviceBin
from app.extensions import db
from app import create_app
import csv
import io
import os


@celery.task
def process_export_task(task_id):
    """Process export task"""
    app = create_app()
    with app.app_context():
        try:
            task = TaskJob.query.get(task_id)
            if not task:
                return {"error": "Task not found"}
            
            task.status = 'running'
            task.progress = 0
            db.session.commit()
            
            params = task.params
            export_type = params.get('export_type')
            
            if export_type == 'orders':
                result = _export_orders(task)
            elif export_type == 'materials':
                result = _export_materials(task)
            else:
                raise ValueError(f"Unsupported export type: {export_type}")
            
            task.status = 'success'
            task.progress = 100
            task.result_url = result.get('url')
            db.session.commit()
            
            return result
            
        except Exception as e:
            task.status = 'fail'
            task.error_message = str(e)
            db.session.commit()
            return {"error": str(e)}


@celery.task
def export_runner():
    """Periodic task to process pending export tasks"""
    app = create_app()
    with app.app_context():
        try:
            # Find pending export tasks
            pending_tasks = TaskJob.query.filter(
                TaskJob.type == 'export',
                TaskJob.status == 'pending'
            ).limit(5).all()
            
            processed = 0
            for task in pending_tasks:
                process_export_task.delay(task.task_id)
                processed += 1
            
            return {"processed": processed}
            
        except Exception as e:
            return {"error": str(e)}


def _export_orders(task):
    """Export orders to CSV"""
    params = task.params
    
    # Build query
    query = db.session.query(Order)
    
    if params.get('from_date'):
        from_dt = datetime.fromisoformat(params['from_date'].replace('Z', '+00:00'))
        query = query.filter(Order.server_ts >= from_dt)
    
    if params.get('to_date'):
        to_dt = datetime.fromisoformat(params['to_date'].replace('Z', '+00:00'))
        query = query.filter(Order.server_ts <= to_dt)
    
    if params.get('device_id'):
        query = query.filter(Order.device_id == params['device_id'])
    
    if params.get('payment_method'):
        query = query.filter(Order.payment_method == params['payment_method'])
    
    if params.get('payment_status'):
        query = query.filter(Order.payment_status == params['payment_status'])
    
    if params.get('exception_only'):
        query = query.filter(Order.is_exception == True)
    
    orders = query.all()
    
    # Update progress
    task.progress = 25
    db.session.commit()
    
    # Generate CSV
    output = io.StringIO()
    headers = [
        'order_id', 'device_id', 'device_ts', 'server_ts', 'items_count',
        'total_price', 'currency', 'payment_method', 'payment_status',
        'is_exception', 'address'
    ]
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    for i, order in enumerate(orders):
        writer.writerow({
            'order_id': order.order_id,
            'device_id': order.device_id,
            'device_ts': order.device_ts.isoformat() if order.device_ts else '',
            'server_ts': order.server_ts.isoformat() if order.server_ts else '',
            'items_count': order.items_count,
            'total_price': float(order.total_price) if order.total_price else 0,
            'currency': order.currency,
            'payment_method': order.payment_method.value if order.payment_method else '',
            'payment_status': order.payment_status.value if order.payment_status else '',
            'is_exception': order.is_exception,
            'address': order.address or ''
        })
        
        # Update progress periodically
        if i % 100 == 0:
            task.progress = 25 + int(70 * i / len(orders))
            db.session.commit()
    
    csv_content = output.getvalue()
    output.close()
    
    # Save file (in a real implementation, save to cloud storage)
    filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    # For demo, just return the content
    return {
        "filename": filename,
        "size": len(csv_content.encode('utf-8')),
        "url": f"/exports/{filename}",
        "content": csv_content
    }


def _export_materials(task):
    """Export materials to CSV"""
    params = task.params
    
    query = db.session.query(MaterialDictionary)
    
    if params.get('enabled_only'):
        query = query.filter(MaterialDictionary.enabled == True)
    
    materials = query.all()
    
    # Update progress
    task.progress = 25
    db.session.commit()
    
    # Generate CSV
    output = io.StringIO()
    headers = ['code', 'name', 'type', 'unit', 'density', 'enabled']
    
    if params.get('include_usage_stats'):
        headers.extend(['total_bins', 'total_capacity', 'total_remaining'])
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    for i, material in enumerate(materials):
        row = {
            'code': material.code,
            'name': material.name,
            'type': material.type or '',
            'unit': material.unit or '',
            'density': float(material.density) if material.density else '',
            'enabled': material.enabled
        }
        
        if params.get('include_usage_stats'):
            bins = DeviceBin.query.filter_by(material_code=material.code).all()
            row['total_bins'] = len(bins)
            row['total_capacity'] = sum(float(bin.capacity or 0) for bin in bins)
            row['total_remaining'] = sum(float(bin.remaining or 0) for bin in bins)
        
        writer.writerow(row)
        
        # Update progress
        if i % 50 == 0:
            task.progress = 25 + int(70 * i / len(materials))
            db.session.commit()
    
    csv_content = output.getvalue()
    output.close()
    
    filename = f"materials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return {
        "filename": filename,
        "size": len(csv_content.encode('utf-8')),
        "url": f"/exports/{filename}",
        "content": csv_content
    }