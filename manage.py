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
@click.option('--reset', is_flag=True, help='Drop & recreate tables before seeding')
@with_appcontext
def seed_demo(reset):
    """Create demo/seed data (idempotent). Use --reset to recreate tables."""
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
    from app.models.alarm import Alarm, AlarmType, AlarmSeverity, AlarmStatus
    from app.models.remote_command import RemoteCommand, CommandType, CommandStatus
    
    # Optional reset (drop & create all tables)
    if reset:
        click.echo('Resetting database (drop & create tables)...')
        import app.models  # ensure models imported
        db.drop_all()
        db.create_all()

    click.echo('Creating seed data (idempotent)...')
    
    # Create merchants
    # Merchants (upsert by name)
    merchant1 = Merchant.query.filter_by(name='StarBucks Coffee').first()
    if not merchant1:
        merchant1 = Merchant(name='StarBucks Coffee', contact='contact@starbucks.com', status=MerchantStatus.ACTIVE.value)
        db.session.add(merchant1)
        db.session.flush()
    else:
        merchant1.contact = 'contact@starbucks.com'
        merchant1.status = MerchantStatus.ACTIVE.value

    merchant2 = Merchant.query.filter_by(name='Local Coffee Shop').first()
    if not merchant2:
        merchant2 = Merchant(name='Local Coffee Shop', contact='info@localcoffee.com', status=MerchantStatus.ACTIVE.value)
        db.session.add(merchant2)
        db.session.flush()
    else:
        merchant2.contact = 'info@localcoffee.com'
        merchant2.status = MerchantStatus.ACTIVE.value
    
    # Create locations
    # Locations (upsert by merchant + name)
    def get_or_create_location(merchant_id, name, address, lat, lng):
        loc = Location.query.filter_by(merchant_id=merchant_id, name=name).first()
        if not loc:
            loc = Location(merchant_id=merchant_id, name=name, address=address, lat=lat, lng=lng)
            db.session.add(loc)
            db.session.flush()
        else:
            loc.address = address
            loc.lat = lat
            loc.lng = lng
        return loc

    location1 = get_or_create_location(merchant1.id, 'Downtown Store', '123 Main St', 39.9042, 116.4074)
    location2 = get_or_create_location(merchant1.id, 'Mall Store', '456 Mall Ave', 39.9100, 116.4200)
    location3 = get_or_create_location(merchant2.id, 'Local Store', '789 Local St', 39.8950, 116.4100)
    
    # Create devices
    # Devices (upsert by device_id)
    def upsert_device(device_id, alias, model, fw_version, status, last_seen, merchant_id, location_id, tags, extra):
        d = Device.query.get(device_id)
        if not d:
            d = Device(device_id=device_id, merchant_id=merchant_id)
            db.session.add(d)
        d.alias = alias
        d.model = model
        d.fw_version = fw_version
        d.status = status
        d.last_seen = last_seen
        d.location_id = location_id
        d.tags = tags
        d.extra = extra
        db.session.flush()
        return d

    device1 = upsert_device(
        'CM001', 'Downtown Coffee Machine', 'CM-2000', '1.2.3',
        DeviceStatus.ONLINE.value, datetime.utcnow(), merchant1.id, location1.id,
        {'location': 'indoor', 'priority': 'high'}, {}
    )
    device2 = upsert_device(
        'CM002', 'Mall Coffee Machine', 'CM-2000', '1.2.2',
        DeviceStatus.OFFLINE.value, datetime.utcnow() - timedelta(hours=2), merchant1.id, location2.id,
        {'location': 'mall'}, {}
    )
    device3 = upsert_device(
        'CM003', 'Local Coffee Machine', 'CM-1000', '1.1.5',
        DeviceStatus.ONLINE.value, datetime.utcnow() - timedelta(minutes=10), merchant2.id, location3.id,
        {'location': 'street'}, {}
    )
    
    # Material dictionary (upsert by code)
    def upsert_material(code, name, type_, unit, density, enabled=True):
        m = MaterialDictionary.query.filter_by(code=code).first()
        if not m:
            m = MaterialDictionary(code=code, name=name)
            db.session.add(m)
        m.name = name
        m.type = type_
        m.unit = unit
        m.density = density
        m.enabled = enabled
        return m

    _ = [
        upsert_material('COFFEE_BEAN_A', 'Arabica Coffee Beans', 'bean', 'g', 0.6, True),
        upsert_material('COFFEE_BEAN_R', 'Robusta Coffee Beans', 'bean', 'g', 0.65, True),
        upsert_material('MILK_POWDER', 'Milk Powder', 'powder', 'g', 0.5, True),
        upsert_material('SUGAR', 'Sugar', 'powder', 'g', 0.8, True),
        upsert_material('CREAM', 'Cream Powder', 'powder', 'g', 0.4, True),
        upsert_material('COCOA', 'Cocoa Powder', 'powder', 'g', 0.45, True),
        upsert_material('VANILLA', 'Vanilla Syrup', 'liquid', 'ml', 1.1, True),
        upsert_material('CARAMEL', 'Caramel Syrup', 'liquid', 'ml', 1.3, True),
        upsert_material('WATER', 'Filtered Water', 'liquid', 'ml', 1.0, True),
        upsert_material('CUP_SMALL', 'Small Paper Cup', 'container', 'pcs', 0.1, True),
    ]
    db.session.flush()
    
    # Create device bins (include low & empty scenarios)
    bins_data = [
        # Device 1 bins
        (device1.device_id, 1, 'COFFEE_BEAN_A', 800, 1000, 'g', 15),
        (device1.device_id, 2, 'MILK_POWDER', 80, 500, 'g', 20),  # Low
        (device1.device_id, 3, 'SUGAR', 400, 800, 'g', 25),
        (device1.device_id, 4, 'WATER', 2000, 3000, 'ml', 10),
        
        # Device 2 bins
        (device2.device_id, 1, 'COFFEE_BEAN_R', 0, 1000, 'g', 15),  # Empty
        (device2.device_id, 2, 'CREAM', 150, 500, 'g', 20),
        (device2.device_id, 3, 'COCOA', 80, 400, 'g', 20),  # Low
        
        # Device 3 bins
        (device3.device_id, 1, 'COFFEE_BEAN_A', 750, 800, 'g', 15),
        (device3.device_id, 2, 'MILK_POWDER', 400, 400, 'g', 20),
        (device3.device_id, 3, 'SUGAR', 300, 600, 'g', 25),
    ]
    
    for device_id, bin_idx, material_code, remaining, capacity, unit, threshold in bins_data:
        bin_obj = DeviceBin.query.filter_by(device_id=device_id, bin_index=bin_idx).first()
        if not bin_obj:
            bin_obj = DeviceBin(device_id=device_id, bin_index=bin_idx)
            db.session.add(bin_obj)
        bin_obj.material_code = material_code
        bin_obj.remaining = remaining
        bin_obj.capacity = capacity
        bin_obj.unit = unit
        bin_obj.threshold_low_pct = threshold
        bin_obj.last_sync = datetime.utcnow() - timedelta(minutes=30)
    
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
        order = Order.query.get(order_id)
        if not order:
            order = Order(order_id=order_id, device_id=device_id)
            db.session.add(order)
        order.device_ts = device_ts
        order.server_ts = device_ts + timedelta(seconds=1)
        order.items_count = items_count
        order.total_price = total_price
        order.currency = 'CNY'
        order.payment_method = payment_method
        order.payment_status = payment_status
        order.is_exception = is_exception
        order.address = f'Generated from {device_id}'

        # Replace order items for idempotency
        for it in order.items.all():
            db.session.delete(it)
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
    
    # Create sample alarms
    # Alarms (avoid duplicates by device+type OPEN)
    def ensure_open_alarm(device_id, type_, severity, title, description, context):
        existing = Alarm.query.filter_by(device_id=device_id, type=type_, status=AlarmStatus.OPEN.value).first()
        if not existing:
            a = Alarm(
                device_id=device_id,
                type=type_,
                severity=severity,
                title=title,
                description=description,
                status=AlarmStatus.OPEN.value,
                context=context
            )
            db.session.add(a)

    ensure_open_alarm(device1.device_id, AlarmType.MATERIAL_LOW.value, AlarmSeverity.WARN.value,
                      '奶粉不足', '原料仓2奶粉低于阈值', {'bin_index': 2, 'threshold_pct': 20})
    ensure_open_alarm(device2.device_id, AlarmType.OFFLINE.value, AlarmSeverity.CRITICAL.value,
                      '设备离线', '设备超过2小时未上报', {'last_seen': str(device2.last_seen)})

    # Create some remote commands history
    # Remote commands (upsert by command_id)
    def upsert_command(command_id, device_id, type_, payload, status, attempts, max_attempts, last_error=None):
        c = RemoteCommand.query.get(command_id)
        if not c:
            c = RemoteCommand(command_id=command_id, device_id=device_id)
            db.session.add(c)
        c.type = type_
        c.payload = payload
        c.status = status
        c.attempts = attempts
        c.max_attempts = max_attempts
        c.last_error = last_error

    upsert_command('CMD_001', device1.device_id, CommandType.SYNC.value, {'action': 'sync_materials'}, CommandStatus.SUCCESS.value, 1, 3)
    upsert_command('CMD_002', device1.device_id, CommandType.SET_PARAMS.value, {'temperature_target': 85, 'brew_time': 30}, CommandStatus.SUCCESS.value, 1, 3)
    upsert_command('CMD_003', device1.device_id, CommandType.UPGRADE.value, {'version': '1.2.4'}, CommandStatus.FAIL.value, 2, 3, 'Download failed')
    upsert_command('CMD_004', device2.device_id, CommandType.SYNC.value, {'action': 'sync_status'}, CommandStatus.PENDING.value, 0, 3)

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
    
    # Ensure admin user exists
    admin_user = User.query.filter_by(email='admin@example.com').first()
    if not admin_user:
        admin_user = User(email='admin@example.com', name='Admin User', role=UserRole.ADMIN.value, active=True)
        admin_user.set_password('Admin123!')
        db.session.add(admin_user)
    else:
        # keep existing password; ensure role is admin
        admin_user.role = UserRole.ADMIN.value
    
    db.session.commit()
    click.echo('Seed data created/updated successfully!')
    click.echo('Admin user: admin@example.com / Admin123! (created if absent)')

# Also register underscore alias for convenience
cli.add_command(seed_demo, name='seed_demo')


if __name__ == '__main__':
    # Create Flask app for CLI context
    app = create_app()
    with app.app_context():
        cli()
    