#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the Python path
backend_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_path)

try:
    print("Testing Coffee Admin application imports...")
    
    # Test basic imports
    from app import create_app
    from app.config import Config
    from app.extensions import db
    from app.models import User, Device, Order, MaterialDictionary
    from app.services.device_service import DeviceService
    from app.services.order_service import OrderService
    
    print("✓ All imports successful")
    
    # Test app creation
    app = create_app()
    print("✓ Flask app creation successful")
    
    # Test basic configuration
    with app.app_context():
        print(f"✓ App context works")
        print(f"✓ Database URI configured: {app.config['SQLALCHEMY_DATABASE_URI'][:50]}...")
        print(f"✓ Redis URL configured: {app.config['REDIS_URL']}")
        print(f"✓ SSE enabled: {app.config['ENABLE_SSE']}")
        print(f"✓ Device token enabled: {app.config['ENABLE_DEVICE_TOKEN']}")
    
    print("\n🎉 All basic tests passed! The Coffee Admin system is ready.")
    print("\nNext steps:")
    print("1. Set up PostgreSQL database")
    print("2. Set up Redis server")
    print("3. Copy .env.example to .env and configure")
    print("4. Run: python manage.py init-db")
    print("5. Run: python manage.py seed-demo")
    print("6. Run: python manage.py create-user --email admin@example.com --password Admin123! --name 'Admin' --role admin")
    print("7. Run: python manage.py run-web")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please install required packages: pip install -r requirements.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)