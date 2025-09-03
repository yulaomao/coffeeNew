#!/usr/bin/env python3
"""
Management commands for the coffee application.
"""
import click
import os
from flask import Flask
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from app import create_app, db
from config import config


@click.group()
def cli():
    """Coffee management commands."""
    pass


@cli.command()
@click.option('--drop', is_flag=True, help='Drop existing tables first')
@with_appcontext
def init_db(drop):
    """Initialize the database."""
    # Ensure all models are imported so SQLAlchemy can create tables
    import app.models  # noqa: F401
    if drop:
        click.echo('Dropping existing tables...')
        db.drop_all()
    
    click.echo('Creating database tables...')
    db.create_all()
    click.echo('Database initialized successfully!')


@cli.command()
@with_appcontext  
def migrate():
    """Run database migrations (placeholder for Alembic)."""
    click.echo('Migration functionality will be implemented with Alembic.')
    click.echo('For now, use init-db to create tables.')


@cli.command()
@click.option('--email', required=True, help='User email')
@click.option('--password', required=True, help='User password')
@click.option('--name', required=True, help='User name')
@click.option('--role', default='admin', help='User role (admin, ops, viewer)')
@with_appcontext
def create_user(email, password, name, role):
    """Create a new user."""
    from app.models.user import User, UserRole
    
    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        click.echo(f'Invalid role: {role}. Must be one of: admin, ops, viewer')
        return
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        click.echo(f'User with email {email} already exists!')
        return
    
    # Create new user
    user = User(
        email=email,
        name=name,
        role=role,
        active=True
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f'User {email} created successfully with role {role}!')


@cli.command(name='seed-demo')
@with_appcontext
def seed_demo():
    """Create demo/seed data."""
    from datetime import datetime, timedelta
    import uuid
    from app.models.merchant import Merchant, MerchantStatus
    from app.models.location import Location
    from app.models.device import Device, DeviceStatus
    from app.models.device_bin import DeviceBin
    from app.models.material_dictionary import MaterialDictionary
    from app.models.order import Order, PaymentMethod, PaymentStatus
    from app.models.order_item import OrderItem
    from app.models.recipe import Recipe
    from app.models.user import User, UserRole
    
    click.echo('Creating seed data...')
    
    # Create merchants
    merchant1 = Merchant(name='StarBucks Coffee', contact='contact@starbucks.com', status=MerchantStatus.ACTIVE.value)
    merchant2 = Merchant(name='Local Coffee Shop', contact='info@localcoffee.com', status=MerchantStatus.ACTIVE.value)
    db.session.add_all([merchant1, merchant2])
    db.session.flush()
    
    # Create locations
    location1 = Location(merchant_id=merchant1.id, name='Downtown Store', address='123 Main St', lat=39.9042, lng=116.4074)
    location2 = Location(merchant_id=merchant1.id, name='Mall Store', address='456 Mall Ave', lat=39.9100, lng=116.4200)
    location3 = Location(merchant_id=merchant2.id, name='Local Store', address='789 Local St', lat=39.8950, lng=116.4100)
    db.session.add_all([location1, location2, location3])
    db.session.flush()
    
    # Create devices
    device1 = Device(
        device_id='CM001',
        alias='Downtown Coffee Machine',
        model='CM-2000',
        fw_version='1.2.3',
        status=DeviceStatus.ONLINE.value,
        last_seen=datetime.utcnow(),
        merchant_id=merchant1.id,
        location_id=location1.id,
        tags={'location': 'indoor', 'priority': 'high'},
        extra={}
    )
    
    device2 = Device(
        device_id='CM002',
        alias='Mall Coffee Machine',
        model='CM-2000',
        fw_version='1.2.2',
        status=DeviceStatus.OFFLINE.value,
        last_seen=datetime.utcnow() - timedelta(hours=2),
        merchant_id=merchant1.id,
        location_id=location2.id,
        tags={'location': 'mall'},
        extra={}
    )
    
    device3 = Device(
        device_id='CM003',
        alias='Local Coffee Machine',
        model='CM-1000',
        fw_version='1.1.5',
        status=DeviceStatus.ONLINE.value,
        last_seen=datetime.utcnow() - timedelta(minutes=10),
        merchant_id=merchant2.id,
        location_id=location3.id,
        tags={'location': 'street'},
        extra={}
    )
    
    db.session.add_all([device1, device2, device3])
    db.session.flush()
    
    # Create material dictionary
    materials = [
        MaterialDictionary(code='COFFEE_BEAN_A', name='Arabica Coffee Beans', type='bean', unit='g', density=0.6, enabled=True),
        MaterialDictionary(code='COFFEE_BEAN_R', name='Robusta Coffee Beans', type='bean', unit='g', density=0.65, enabled=True),
        MaterialDictionary(code='MILK_POWDER', name='Milk Powder', type='powder', unit='g', density=0.5, enabled=True),
        MaterialDictionary(code='SUGAR', name='Sugar', type='powder', unit='g', density=0.8, enabled=True),
        MaterialDictionary(code='CREAM', name='Cream Powder', type='powder', unit='g', density=0.4, enabled=True),
        MaterialDictionary(code='COCOA', name='Cocoa Powder', type='powder', unit='g', density=0.45, enabled=True),
        MaterialDictionary(code='VANILLA', name='Vanilla Syrup', type='liquid', unit='ml', density=1.1, enabled=True),
        MaterialDictionary(code='CARAMEL', name='Caramel Syrup', type='liquid', unit='ml', density=1.3, enabled=True),
        MaterialDictionary(code='WATER', name='Filtered Water', type='liquid', unit='ml', density=1.0, enabled=True),
        MaterialDictionary(code='CUP_SMALL', name='Small Paper Cup', type='container', unit='pcs', density=0.1, enabled=True),
    ]
    db.session.add_all(materials)
    db.session.flush()
    
    # Create device bins
    bins_data = [
        # Device 1 bins
        (device1.device_id, 1, 'COFFEE_BEAN_A', 800, 1000, 'g', 15),
        (device1.device_id, 2, 'MILK_POWDER', 300, 500, 'g', 20),  # Low
        (device1.device_id, 3, 'SUGAR', 400, 800, 'g', 25),
        (device1.device_id, 4, 'WATER', 2000, 3000, 'ml', 10),
        
        # Device 2 bins
        (device2.device_id, 1, 'COFFEE_BEAN_R', 600, 1000, 'g', 15),
        (device2.device_id, 2, 'CREAM', 150, 500, 'g', 20),
        (device2.device_id, 3, 'COCOA', 80, 400, 'g', 20),  # Low
        
        # Device 3 bins
        (device3.device_id, 1, 'COFFEE_BEAN_A', 750, 800, 'g', 15),
        (device3.device_id, 2, 'MILK_POWDER', 400, 400, 'g', 20),
        (device3.device_id, 3, 'SUGAR', 300, 600, 'g', 25),
    ]
    
    for device_id, bin_idx, material_code, remaining, capacity, unit, threshold in bins_data:
        bin_obj = DeviceBin(
            device_id=device_id,
            bin_index=bin_idx,
            material_code=material_code,
            remaining=remaining,
            capacity=capacity,
            unit=unit,
            threshold_low_pct=threshold,
            last_sync=datetime.utcnow() - timedelta(minutes=30)
        )
        db.session.add(bin_obj)
    
    db.session.flush()
    
    # Create some orders (recent 7 days)
    base_time = datetime.utcnow() - timedelta(days=7)
    orders_data = [
        # Normal orders
        ('ORDER_001', device1.device_id, base_time + timedelta(days=1, hours=9), 2, 25.5, PaymentMethod.WECHAT.value, PaymentStatus.PAID.value, False),
        ('ORDER_002', device1.device_id, base_time + timedelta(days=1, hours=10), 1, 18.0, PaymentMethod.ALIPAY.value, PaymentStatus.PAID.value, False),
        ('ORDER_003', device3.device_id, base_time + timedelta(days=2, hours=14), 3, 42.0, PaymentMethod.CARD.value, PaymentStatus.PAID.value, False),
        ('ORDER_004', device1.device_id, base_time + timedelta(days=3, hours=8), 1, 15.5, PaymentMethod.WECHAT.value, PaymentStatus.PAID.value, False),
        ('ORDER_005', device3.device_id, base_time + timedelta(days=4, hours=16), 2, 28.0, PaymentMethod.ALIPAY.value, PaymentStatus.PAID.value, False),
        
        # Exception orders
        ('ORDER_006', device2.device_id, base_time + timedelta(days=5, hours=11), 1, 20.0, PaymentMethod.WECHAT.value, PaymentStatus.REFUNDED.value, True),
        ('ORDER_007', device1.device_id, base_time + timedelta(days=6, hours=13), 2, 35.0, PaymentMethod.CARD.value, PaymentStatus.REFUND_FAILED.value, True),
    ]
    
    for order_id, device_id, device_ts, items_count, total_price, payment_method, payment_status, is_exception in orders_data:
        order = Order(
            order_id=order_id,
            device_id=device_id,
            device_ts=device_ts,
            server_ts=device_ts + timedelta(seconds=1),
            items_count=items_count,
            total_price=total_price,
            currency='CNY',
            payment_method=payment_method,
            payment_status=payment_status,
            is_exception=is_exception,
            address=f'Generated from {device_id}'
        )
        db.session.add(order)
        
        # Add order items
        for i in range(items_count):
            item = OrderItem(
                order_id=order_id,
                product_id=f'PRODUCT_{i+1}',
                name=f'Coffee Item {i+1}',
                qty=1,
                unit_price=total_price / items_count,
                options={'size': 'medium', 'temperature': 'hot'}
            )
            db.session.add(item)
    
    db.session.flush()
    
    # Create some recipes
    recipe1 = Recipe(
        name='Classic Latte',
        version='1.0',
        schema={
            'steps': [
                {'action': 'grind', 'material': 'COFFEE_BEAN_A', 'amount': 20, 'unit': 'g'},
                {'action': 'brew', 'temperature': 85, 'time': 25},
                {'action': 'steam', 'material': 'MILK_POWDER', 'amount': 10, 'unit': 'g'},
                {'action': 'combine', 'ratio': '1:3'}
            ],
            'output': {'volume': 250, 'unit': 'ml'}
        },
        enabled=True
    )
    
    recipe2 = Recipe(
        name='Cappuccino',
        version='1.1',
        schema={
            'steps': [
                {'action': 'grind', 'material': 'COFFEE_BEAN_A', 'amount': 18, 'unit': 'g'},
                {'action': 'brew', 'temperature': 88, 'time': 30},
                {'action': 'foam', 'material': 'MILK_POWDER', 'amount': 8, 'unit': 'g'},
                {'action': 'combine', 'ratio': '1:1:1'}
            ],
            'output': {'volume': 180, 'unit': 'ml'}
        },
        enabled=True
    )
    
    db.session.add_all([recipe1, recipe2])
    
    # Check if admin user exists, if not create it
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        admin_user = User(
            email='admin@example.com',
            name='Admin User',
            role=UserRole.ADMIN.value,
            active=True
        )
        admin_user.set_password('Admin123!')
        db.session.add(admin_user)
    
    db.session.commit()
    click.echo('Seed data created successfully!')
    click.echo('Admin user: admin@example.com / Admin123!')

# Also register underscore alias for convenience
cli.add_command(seed_demo, name='seed_demo')


if __name__ == '__main__':
    # Create Flask app for CLI context
    app = create_app()
    with app.app_context():
        cli()
    