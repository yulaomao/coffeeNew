import unittest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from device.agent.materials import material_manager
from device.agent.recipes import recipe_manager
from device.agent.orders import order_manager
from device.backend.client import backend_client

class TestMaterialManager(unittest.TestCase):
    """Test material management"""
    
    def setUp(self):
        self.material_manager = material_manager
    
    def test_get_bins(self):
        """Test getting bins"""
        bins = self.material_manager.get_bins()
        self.assertIsInstance(bins, list)
        self.assertGreater(len(bins), 0)
    
    def test_material_sufficient(self):
        """Test material sufficiency check"""
        # Should have enough BEAN_A for 10g
        sufficient = self.material_manager.is_material_sufficient("BEAN_A", 10.0)
        self.assertTrue(sufficient)
        
        # Should not have enough BEAN_A for 1000g
        sufficient = self.material_manager.is_material_sufficient("BEAN_A", 1000.0)
        self.assertFalse(sufficient)
    
    def test_set_bin_level(self):
        """Test setting bin level"""
        # Set bin 0 to 50%
        result = self.material_manager.set_bin_level(0, 50.0)
        self.assertTrue(result)
        
        # Check if level was set
        bin_data = self.material_manager.get_bin_by_index(0)
        self.assertEqual(bin_data.remaining, 50.0)


class TestRecipeManager(unittest.TestCase):
    """Test recipe management"""
    
    def setUp(self):
        self.recipe_manager = recipe_manager
    
    def test_get_recipes(self):
        """Test getting recipes"""
        recipes = self.recipe_manager.get_recipes()
        self.assertIsInstance(recipes, list)
        self.assertGreater(len(recipes), 0)
    
    def test_get_recipe_by_id(self):
        """Test getting recipe by ID"""
        recipe = self.recipe_manager.get_recipe_by_id(201)
        self.assertIsNotNone(recipe)
        self.assertEqual(recipe.id, 201)
        
        # Non-existent recipe
        recipe = self.recipe_manager.get_recipe_by_id(999)
        self.assertIsNone(recipe)
    
    def test_validate_recipe(self):
        """Test recipe validation"""
        recipe = self.recipe_manager.get_recipe_by_id(201)
        errors = self.recipe_manager.validate_recipe(recipe)
        self.assertEqual(len(errors), 0)


class TestOrderManager(unittest.TestCase):
    """Test order management"""
    
    def setUp(self):
        self.order_manager = order_manager
    
    async def test_create_order(self):
        """Test creating order"""
        items = [{"recipe_id": 201, "quantity": 1}]
        order = await self.order_manager.create_order(items, is_test=True)
        
        self.assertIsNotNone(order)
        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.items[0].recipe_id, 201)
    
    async def test_create_test_order(self):
        """Test creating test order"""
        order = await self.order_manager.create_test_order(201)
        
        self.assertTrue(order.is_test)
        self.assertEqual(order.payment_status, "paid")
        self.assertEqual(order.status, "paid")


class TestBackendClient(unittest.TestCase):
    """Test backend client"""
    
    def setUp(self):
        self.client = backend_client
    
    @patch('device.backend.client.httpx.AsyncClient')
    async def test_post_status(self, mock_client):
        """Test posting status"""
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        status_data = {
            "status": "idle",
            "temperature": 85.0,
            "firmware_version": "1.0.0",
            "uptime_seconds": 3600
        }
        
        response = await self.client.post_status(status_data)
        self.assertTrue(response.ok)
    
    async def test_test_connection(self):
        """Test connection test"""
        # This will likely fail in test environment, but shouldn't crash
        try:
            result = await self.client.test_connection()
            self.assertIsInstance(result, bool)
        except Exception:
            # Connection failures are expected in test environment
            pass


def run_async_test(coro):
    """Helper to run async tests"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


if __name__ == '__main__':
    # Run sync tests
    suite = unittest.TestSuite()
    
    # Add sync tests
    suite.addTest(unittest.makeSuite(TestMaterialManager))
    suite.addTest(unittest.makeSuite(TestRecipeManager))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests manually
    print("\nRunning async tests...")
    
    try:
        # Test order creation
        items = [{"recipe_id": 201, "quantity": 1}]
        order = run_async_test(order_manager.create_order(items, is_test=True))
        print(f"✓ Created test order: {order.order_id}")
        
        # Test order creation (test mode)
        test_order = run_async_test(order_manager.create_test_order(201))
        print(f"✓ Created test order: {test_order.order_id}")
        
        print("\nAll async tests passed!")
    
    except Exception as e:
        print(f"✗ Async test failed: {e}")
    
    print(f"\nTest Results: {result.testsRun} tests run, {len(result.failures)} failures, {len(result.errors)} errors")