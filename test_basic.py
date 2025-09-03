#!/usr/bin/env python3
"""
Simple test to verify the Flask application can be created and basic routes work.
This test runs without external dependencies to validate the application structure.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_app_creation():
    """Test that the Flask application can be created."""
    try:
        from app import create_app
        app = create_app('testing')
        assert app is not None
        assert app.config['TESTING'] == True
        print("✓ Flask application creation successful")
        return True
    except Exception as e:
        print(f"✗ Flask application creation failed: {e}")
        return False

def test_models_import():
    """Test that all models can be imported."""
    try:
        from app.models.merchant import Merchant
        from app.models.location import Location
        from app.models.user import User
        from app.models.device import Device
        from app.models.device_bin import DeviceBin
        from app.models.material_dictionary import MaterialDictionary
        from app.models.order import Order
        from app.models.order_item import OrderItem
        from app.models.recipe import Recipe
        from app.models.recipe_package import RecipePackage
        from app.models.remote_command import RemoteCommand
        from app.models.command_batch import CommandBatch
        from app.models.alarm import Alarm
        from app.models.task_job import TaskJob
        from app.models.operation_log import OperationLog
        print("✓ All models imported successfully")
        return True
    except Exception as e:
        print(f"✗ Model import failed: {e}")
        return False

def test_blueprints():
    """Test that all blueprints are registered."""
    try:
        from app import create_app
        app = create_app('testing')
        
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        expected_blueprints = ['main', 'auth', 'api', 'admin']
        
        for bp_name in expected_blueprints:
            if bp_name not in blueprint_names:
                raise Exception(f"Blueprint {bp_name} not registered")
        
        print(f"✓ All blueprints registered: {blueprint_names}")
        return True
    except Exception as e:
        print(f"✗ Blueprint registration failed: {e}")
        return False

def test_basic_routes():
    """Test basic route accessibility."""
    try:
        from app import create_app
        app = create_app('testing')
        
        with app.test_client() as client:
            # Test health endpoints
            response = client.get('/health')
            assert response.status_code == 200
            
            response = client.get('/api/v1/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data.get('ok') == True
            
            print("✓ Basic routes working")
            return True
    except Exception as e:
        print(f"✗ Route testing failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints return proper JSON format."""
    try:
        from app import create_app
        app = create_app('testing')
        
        with app.test_client() as client:
            # Test dashboard summary
            response = client.get('/api/v1/dashboard/summary')
            assert response.status_code == 200
            data = response.get_json()
            assert 'ok' in data
            assert 'data' in data
            
            # Test devices list
            response = client.get('/api/v1/devices')
            assert response.status_code == 200
            data = response.get_json()
            assert data.get('ok') == True
            assert 'devices' in data.get('data', {})
            
            # Test materials list
            response = client.get('/api/v1/materials')
            assert response.status_code == 200
            data = response.get_json()
            assert data.get('ok') == True
            assert 'materials' in data.get('data', {})
            
            print("✓ API endpoints returning proper JSON format")
            return True
    except Exception as e:
        print(f"✗ API endpoint testing failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Coffee Management System")
    print("=" * 50)
    
    tests = [
        test_app_creation,
        test_models_import,
        test_blueprints,
        test_basic_routes,
        test_api_endpoints
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        if test():
            passed += 1
        else:
            failed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! The application structure is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)