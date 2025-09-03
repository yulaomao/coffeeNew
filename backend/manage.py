#!/usr/bin/env python3
"""
Coffee Admin Management CLI

This script provides command-line interface for managing the coffee admin application.
"""

import os
import sys
import click
from datetime import datetime, timezone
from flask import current_app
from flask.cli import with_appcontext, AppGroup

# Add the backend directory to Python path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

from app import create_app
from app.extensions import db
from app.models import User, Merchant, Location, Device, DeviceBin, MaterialDictionary, Order, OrderItem, Recipe, RecipePackage


app = create_app()

# Create CLI groups
init_cli = AppGroup('init')
user_cli = AppGroup('user')
data_cli = AppGroup('data')

app.cli.add_command(init_cli, name='init')
app.cli.add_command(user_cli, name='user')
app.cli.add_command(data_cli, name='data')


@init_cli.command('db')
@with_appcontext
def init_db():
    """Initialize database tables"""
    click.echo('Creating database tables...')
    db.create_all()
    click.echo('Database initialized successfully.')


@click.command()
@with_appcontext
def migrate():
    """Run database migrations"""
    from flask_migrate import upgrade
    click.echo('Running database migrations...')
    upgrade()
    click.echo('Migrations completed successfully.')


@user_cli.command('create')
@click.option('--email', required=True, help='User email address')
@click.option('--password', required=True, help='User password')
@click.option('--name', required=True, help='User full name')
@click.option('--role', type=click.Choice(['admin', 'ops', 'viewer']), default='admin', help='User role')
@with_appcontext
def create_user(email, password, name, role):
    """Create a new user"""
    try:
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            click.echo(f'User with email {email} already exists.')
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
        
        click.echo(f'User {email} created successfully with role {role}.')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating user: {str(e)}', err=True)


@data_cli.command('seed-demo')
@with_appcontext
def seed_demo_data():
    """Seed database with demo data"""
    try:
        click.echo('Seeding demo data...')
        
        # Create merchants
        merchant1 = Merchant(name='Coffee Chain A', contact='contact@coffeechaina.com', status='active')
        merchant2 = Merchant(name='Coffee Chain B', contact='contact@coffeechainb.com', status='active')
        
        db.session.add(merchant1)
        db.session.add(merchant2)
        db.session.flush()  # Get IDs
        
        # Create locations
        location1 = Location(
            merchant_id=merchant1.id,
            name='Downtown Store',
            address='123 Main St, Downtown',
            lat=40.7128,
            lng=-74.0060
        )
        
        location2 = Location(
            merchant_id=merchant1.id,
            name='Mall Store',
            address='456 Mall Ave, Shopping Center',
            lat=40.7589,
            lng=-73.9851
        )
        
        location3 = Location(
            merchant_id=merchant2.id,
            name='Airport Store',
            address='789 Airport Rd, Terminal 1',
            lat=40.6413,
            lng=-73.7781
        )
        
        db.session.add_all([location1, location2, location3])
        db.session.flush()
        
        # Create material dictionary
        materials = [
            MaterialDictionary(code='COFFEE_BEANS', name='Coffee Beans', type='beans', unit='g', density=0.7, enabled=True),
            MaterialDictionary(code='MILK_POWDER', name='Milk Powder', type='powder', unit='g', density=0.5, enabled=True),
            MaterialDictionary(code='SUGAR', name='Sugar', type='powder', unit='g', density=0.8, enabled=True),
            MaterialDictionary(code='COCOA', name='Cocoa Powder', type='powder', unit='g', density=0.4, enabled=True),
            MaterialDictionary(code='VANILLA', name='Vanilla Syrup', type='liquid', unit='ml', density=1.0, enabled=True),
            MaterialDictionary(code='WATER', name='Water', type='liquid', unit='ml', density=1.0, enabled=True),
            MaterialDictionary(code='CUPS', name='Paper Cups', type='supplies', unit='pcs', density=0.1, enabled=True),
            MaterialDictionary(code='LIDS', name='Cup Lids', type='supplies', unit='pcs', density=0.05, enabled=True),
            MaterialDictionary(code='STIRRERS', name='Stirrers', type='supplies', unit='pcs', density=0.02, enabled=True),
            MaterialDictionary(code='NAPKINS', name='Napkins', type='supplies', unit='pcs', density=0.01, enabled=True),
        ]
        
        db.session.add_all(materials)
        
        # Create devices
        device1 = Device(
            device_id='D001',
            alias='Downtown Machine 1',
            model='CoffeePro-A',
            fw_version='2.1.0',
            status='online',
            last_seen=datetime.now(timezone.utc),
            ip='192.168.1.100',
            wifi_ssid='CoffeeNet',
            temperature=22.5,
            merchant_id=merchant1.id,
            location_id=location1.id,
            tags=['premium', 'high-traffic'],
            extra={'installation_date': '2023-06-01'}
        )
        
        device2 = Device(
            device_id='D002',
            alias='Mall Machine 1',
            model='CoffeePro-A',
            fw_version='2.0.5',
            status='offline',
            last_seen=datetime.now(timezone.utc),
            merchant_id=merchant1.id,
            location_id=location2.id,
            tags=['standard'],
            extra={'installation_date': '2023-07-15'}
        )
        
        device3 = Device(
            device_id='D003',
            alias='Airport Machine 1',
            model='CoffeePro-B',
            fw_version='1.8.2',
            status='online',
            last_seen=datetime.now(timezone.utc),
            ip='192.168.1.103',
            wifi_ssid='AirportWiFi',
            temperature=24.1,
            merchant_id=merchant2.id,
            location_id=location3.id,
            tags=['compact', 'airport'],
            extra={'installation_date': '2023-05-20'}
        )
        
        db.session.add_all([device1, device2, device3])
        
        # Create device bins with materials
        bins_data = [
            # Device 1 bins
            {'device_id': 'D001', 'bin_index': 0, 'material_code': 'COFFEE_BEANS', 'remaining': 1200, 'capacity': 2000, 'threshold_low_pct': 20},
            {'device_id': 'D001', 'bin_index': 1, 'material_code': 'MILK_POWDER', 'remaining': 800, 'capacity': 1000, 'threshold_low_pct': 15},
            {'device_id': 'D001', 'bin_index': 2, 'material_code': 'SUGAR', 'remaining': 150, 'capacity': 500, 'threshold_low_pct': 20},  # Low material
            {'device_id': 'D001', 'bin_index': 3, 'material_code': 'WATER', 'remaining': 8000, 'capacity': 10000, 'threshold_low_pct': 10},
            {'device_id': 'D001', 'bin_index': 4, 'material_code': 'CUPS', 'remaining': 45, 'capacity': 100, 'threshold_low_pct': 30},
            
            # Device 2 bins
            {'device_id': 'D002', 'bin_index': 0, 'material_code': 'COFFEE_BEANS', 'remaining': 1800, 'capacity': 2000, 'threshold_low_pct': 20},
            {'device_id': 'D002', 'bin_index': 1, 'material_code': 'MILK_POWDER', 'remaining': 100, 'capacity': 1000, 'threshold_low_pct': 15},  # Low material
            {'device_id': 'D002', 'bin_index': 2, 'material_code': 'SUGAR', 'remaining': 400, 'capacity': 500, 'threshold_low_pct': 20},
            {'device_id': 'D002', 'bin_index': 3, 'material_code': 'WATER', 'remaining': 5000, 'capacity': 10000, 'threshold_low_pct': 10},
            
            # Device 3 bins
            {'device_id': 'D003', 'bin_index': 0, 'material_code': 'COFFEE_BEANS', 'remaining': 900, 'capacity': 1500, 'threshold_low_pct': 25},
            {'device_id': 'D003', 'bin_index': 1, 'material_code': 'COCOA', 'remaining': 200, 'capacity': 400, 'threshold_low_pct': 20},
            {'device_id': 'D003', 'bin_index': 2, 'material_code': 'WATER', 'remaining': 7500, 'capacity': 8000, 'threshold_low_pct': 15},
        ]
        
        for bin_data in bins_data:
            bin_obj = DeviceBin(**bin_data, unit='g', last_sync=datetime.now(timezone.utc))
            db.session.add(bin_obj)
        
        # Create some demo recipes
        recipe1 = Recipe(
            name='Classic Espresso',
            version='1.0',
            enabled=True,
            schema={
                "version": "1.0",
                "name": "Classic Espresso",
                "description": "Traditional espresso shot",
                "category": "espresso",
                "prep_time": 30,
                "steps": [
                    {"step_id": "grind", "name": "Grind Beans", "type": "dispense", "params": {"material": "COFFEE_BEANS", "amount": 18}, "duration": 5},
                    {"step_id": "extract", "name": "Extract", "type": "extract", "params": {"pressure": 9, "temperature": 92}, "duration": 25}
                ],
                "materials": [
                    {"material_code": "COFFEE_BEANS", "bin_index": 0, "amount": 18, "unit": "g"}
                ]
            }
        )
        
        recipe2 = Recipe(
            name='Cappuccino',
            version='1.1',
            enabled=True,
            schema={
                "version": "1.1",
                "name": "Cappuccino",
                "description": "Espresso with steamed milk foam",
                "category": "milk-based",
                "prep_time": 60,
                "steps": [
                    {"step_id": "grind", "name": "Grind Beans", "type": "dispense", "params": {"material": "COFFEE_BEANS", "amount": 18}, "duration": 5},
                    {"step_id": "extract", "name": "Extract", "type": "extract", "params": {"pressure": 9, "temperature": 92}, "duration": 25},
                    {"step_id": "milk", "name": "Steam Milk", "type": "dispense", "params": {"material": "MILK_POWDER", "amount": 8}, "duration": 15},
                    {"step_id": "foam", "name": "Create Foam", "type": "foam", "params": {"temperature": 65}, "duration": 15}
                ],
                "materials": [
                    {"material_code": "COFFEE_BEANS", "bin_index": 0, "amount": 18, "unit": "g"},
                    {"material_code": "MILK_POWDER", "bin_index": 1, "amount": 8, "unit": "g"}
                ]
            }
        )
        
        db.session.add_all([recipe1, recipe2])
        
        # Create some demo orders (for the past week)
        from decimal import Decimal
        import random
        from datetime import timedelta
        
        order_items_templates = [
            {'product_id': 'ESP001', 'name': 'Classic Espresso', 'qty': 1, 'unit_price': Decimal('3.50')},
            {'product_id': 'CAP001', 'name': 'Cappuccino', 'qty': 1, 'unit_price': Decimal('4.20')},
            {'product_id': 'LAT001', 'name': 'Latte', 'qty': 1, 'unit_price': Decimal('4.50')},
            {'product_id': 'AME001', 'name': 'Americano', 'qty': 1, 'unit_price': Decimal('3.80')},
        ]
        
        devices = ['D001', 'D002', 'D003']
        payment_methods = ['wechat', 'alipay', 'card', 'corp']
        
        order_counter = 1
        for days_ago in range(7):
            date = datetime.now(timezone.utc) - timedelta(days=days_ago)
            
            # Create 5-15 orders per day
            for i in range(random.randint(5, 15)):
                device_id = random.choice(devices)
                template = random.choice(order_items_templates)
                
                order = Order(
                    order_id=f'ORD{date.strftime("%Y%m%d")}{order_counter:03d}',
                    device_id=device_id,
                    device_ts=date.replace(hour=random.randint(7, 20), minute=random.randint(0, 59)),
                    server_ts=date.replace(hour=random.randint(7, 20), minute=random.randint(0, 59)),
                    items_count=1,
                    total_price=template['unit_price'],
                    currency='CNY',
                    payment_method=random.choice(payment_methods),
                    payment_status='paid' if random.random() > 0.05 else 'unpaid',
                    is_exception=random.random() < 0.02,
                    address=f'Order from {device_id}',
                    meta={'app_version': '2.1.0'}
                )
                
                db.session.add(order)
                db.session.flush()
                
                # Add order item
                order_item = OrderItem(
                    order_id=order.order_id,
                    product_id=template['product_id'],
                    name=template['name'],
                    qty=template['qty'],
                    unit_price=template['unit_price'],
                    options={'size': 'regular', 'temperature': 'hot'}
                )
                
                db.session.add(order_item)
                order_counter += 1
        
        db.session.commit()
        
        click.echo('Demo data seeded successfully!')
        click.echo('Created:')
        click.echo(f'  - {Merchant.query.count()} merchants')
        click.echo(f'  - {Location.query.count()} locations')
        click.echo(f'  - {Device.query.count()} devices')
        click.echo(f'  - {MaterialDictionary.query.count()} materials')
        click.echo(f'  - {DeviceBin.query.count()} device bins')
        click.echo(f'  - {Recipe.query.count()} recipes')
        click.echo(f'  - {Order.query.count()} orders')
        
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error seeding data: {str(e)}', err=True)


@click.command()
@click.option('--host', default='127.0.0.1', help='Host to run on')
@click.option('--port', default=5000, type=int, help='Port to run on')
@click.option('--debug', is_flag=True, help='Enable debug mode')
def run_web(host, port, debug):
    """Run web server"""
    click.echo(f'Starting web server on {host}:{port}...')
    app.run(host=host, port=port, debug=debug)


@click.command()
def run_worker():
    """Run Celery worker"""
    from app.workers.celery_app import celery
    click.echo('Starting Celery worker...')
    celery.start(['worker', '--loglevel=info'])


@click.command()
def run_beat():
    """Run Celery beat scheduler"""
    from app.workers.celery_app import celery
    click.echo('Starting Celery beat scheduler...')
    celery.start(['beat', '--loglevel=info'])


# Register standalone commands
app.cli.add_command(migrate)
app.cli.add_command(run_web)
app.cli.add_command(run_worker)
app.cli.add_command(run_beat)


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) == 1:
        # No arguments provided, show help
        click.echo("Coffee Admin Management CLI")
        click.echo("Usage: python manage.py <command>")
        click.echo()
        click.echo("Commands:")
        click.echo("  init-db       Initialize database")
        click.echo("  migrate       Run migrations")
        click.echo("  seed-demo     Seed demo data")
        click.echo("  create-user   Create user")
        click.echo("  run-web       Start web server")
        click.echo("  run-worker    Start Celery worker")
        click.echo("  run-beat      Start Celery beat")
        sys.exit(0)
    
    # Handle command parsing
    cmd = sys.argv[1]
    
    if cmd == 'init-db':
        with app.app_context():
            init_db()
    elif cmd == 'migrate':
        with app.app_context():
            migrate()
    elif cmd == 'seed-demo':
        with app.app_context():
            seed_demo_data()
    elif cmd == 'create-user':
        if len(sys.argv) < 8:
            click.echo("Usage: python manage.py create-user --email <email> --password <password> --name <name> [--role <role>]")
            sys.exit(1)
        
        # Parse create-user arguments
        email = None
        password = None
        name = None
        role = 'admin'
        
        i = 2
        while i < len(sys.argv):
            if sys.argv[i] == '--email' and i + 1 < len(sys.argv):
                email = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--password' and i + 1 < len(sys.argv):
                password = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--name' and i + 1 < len(sys.argv):
                name = sys.argv[i + 1]
                i += 2
            elif sys.argv[i] == '--role' and i + 1 < len(sys.argv):
                role = sys.argv[i + 1]
                i += 2
            else:
                i += 1
        
        if not all([email, password, name]):
            click.echo("Error: --email, --password, and --name are required")
            sys.exit(1)
        
        with app.app_context():
            create_user(email, password, name, role)
    
    elif cmd == 'run-web':
        run_web()
    elif cmd == 'run-worker':
        run_worker()
    elif cmd == 'run-beat':
        run_beat()
    else:
        click.echo(f"Unknown command: {cmd}")
        sys.exit(1)