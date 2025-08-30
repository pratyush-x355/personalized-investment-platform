import unittest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from datetime import datetime, timedelta
import json

# Import your Kite_Api class
# from kite_connect import Kite_Api
from core.kite_connect import Kite_Api
from typing import List, Dict, Optional


class TestKiteApi(unittest.TestCase):
    """Comprehensive test suite for Kite_Api class"""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.api_key = "test_api_key"
        self.access_token = "test_access_token"
        
        # Mock KiteConnect to avoid actual API calls during testing
        with patch('kiteconnect.KiteConnect') as mock_kite_connect:
            self.mock_kite = Mock()
            mock_kite_connect.return_value = self.mock_kite
            
            # Initialize the Kite_Api instance
            self.kite_api = Kite_Api(self.api_key, self.access_token)
    
    # ==================== INITIALIZATION TESTS ====================
    
    def test_initialization(self):
        """Test proper initialization of Kite_Api instance."""
        self.assertEqual(self.kite_api.api_key, self.api_key)
        self.assertEqual(self.kite_api.access_token, self.access_token)
        self.assertIsNotNone(self.kite_api.kite)
        
        # Check if mapping dictionaries are properly initialized
        self.assertIn("BUY", self.kite_api.t_type_dict)
        self.assertIn("NSE", self.kite_api.ex_seg_dict)
        self.assertIn("CNC", self.kite_api.p_type_dict)
    
    def test_mapping_variables(self):
        """Test that all mapping dictionaries are properly set up."""
        # Test transaction types
        self.assertEqual(len(self.kite_api.t_type_dict), 2)
        self.assertIn("BUY", self.kite_api.t_type_dict)
        self.assertIn("SELL", self.kite_api.t_type_dict)
        
        # Test exchanges
        expected_exchanges = ["NSE", "BSE", "NFO", "BFO", "CDS", "MCX"]
        for exchange in expected_exchanges:
            self.assertIn(exchange, self.kite_api.ex_seg_dict)
        
        # Test product types
        expected_products = ["CNC", "MIS", "NRML"]
        for product in expected_products:
            self.assertIn(product, self.kite_api.p_type_dict)
    
    # ==================== ORDER PLACEMENT TESTS ====================
    
    def test_place_market_order_success(self):
        """Test successful market order placement."""
        # Mock successful response
        mock_response = {"order_id": "123456", "status": "success"}
        self.mock_kite.place_order.return_value = mock_response
        
        result = self.kite_api.place_market_order(
            tradingsymbol="RELIANCE",
            exchange="NSE",
            t_type="BUY",
            quantity=10,
            p_type="CNC"
        )
        
        self.assertEqual(result, mock_response)
        self.mock_kite.place_order.assert_called_once()
    
    def test_place_market_order_error(self):
        """Test market order placement with error."""
        # Mock exception
        self.mock_kite.place_order.side_effect = Exception("API Error")
        
        result = self.kite_api.place_market_order(
            tradingsymbol="RELIANCE",
            exchange="NSE",
            t_type="BUY",
            quantity=10,
            p_type="CNC"
        )
        
        self.assertEqual(result["status"], "error")
        self.assertIn("API Error", result["message"])
    
    def test_place_limit_order(self):
        """Test limit order placement."""
        mock_response = {"order_id": "789012", "status": "success"}
        self.mock_kite.place_order.return_value = mock_response
        
        result = self.kite_api.place_limit_order(
            tradingsymbol="TCS",
            exchange="NSE",
            t_type="BUY",
            quantity=5,
            p_type="CNC",
            price=3500.0
        )
        
        self.assertEqual(result, mock_response)
        
        # Verify correct parameters were passed
        call_args = self.mock_kite.place_order.call_args
        self.assertEqual(call_args[1]["price"], 3500.0)
        self.assertEqual(call_args[1]["quantity"], 5)
    
    def test_place_stoploss_orders(self):
        """Test stop-loss order placement."""
        mock_response = {"order_id": "345678", "status": "success"}
        self.mock_kite.place_order.return_value = mock_response
        
        # Test SL Limit order
        result = self.kite_api.place_stoploss_limit_order(
            tradingsymbol="INFY",
            exchange="NSE",
            t_type="SELL",
            quantity=10,
            p_type="CNC",
            price=1500.0,
            trigger_price=1520.0
        )
        
        self.assertEqual(result, mock_response)
        
        # Test SL Market order
        result = self.kite_api.place_stoploss_market_order(
            tradingsymbol="INFY",
            exchange="NSE",
            t_type="SELL",
            quantity=10,
            p_type="CNC",
            trigger_price=1520.0
        )
        
        self.assertEqual(result, mock_response)
    
    # ==================== ORDER MANAGEMENT TESTS ====================
    
    def test_modify_order(self):
        """Test order modification."""
        mock_response = {"order_id": "123456", "status": "modified"}
        self.mock_kite.modify_order.return_value = mock_response
        
        result = self.kite_api.modify_order(
            order_id="123456",
            quantity=20,
            price=3600.0
        )
        
        self.assertEqual(result, mock_response)
        self.mock_kite.modify_order.assert_called_once()
    
    def test_cancel_order(self):
        """Test order cancellation."""
        mock_response = {"order_id": "123456", "status": "cancelled"}
        self.mock_kite.cancel_order.return_value = mock_response
        
        result = self.kite_api.cancel_order(order_id="123456")
        
        self.assertEqual(result, mock_response)
        self.mock_kite.cancel_order.assert_called_once()
    
    # ==================== DATA RETRIEVAL TESTS ====================
    
    def test_get_orders(self):
        """Test getting orders."""
        mock_orders = [
            {"order_id": "123", "tradingsymbol": "RELIANCE", "status": "COMPLETE"},
            {"order_id": "456", "tradingsymbol": "TCS", "status": "OPEN"}
        ]
        self.mock_kite.orders.return_value = mock_orders
        
        result = self.kite_api.get_orders()
        
        self.assertEqual(result, mock_orders)
        self.assertEqual(len(result), 2)
    
    def test_get_positions(self):
        """Test getting positions."""
        mock_positions = {
            "net": [{"tradingsymbol": "RELIANCE", "quantity": 10, "pnl": 500}],
            "day": []
        }
        self.mock_kite.positions.return_value = mock_positions
        
        result = self.kite_api.get_positions()
        
        self.assertEqual(result, mock_positions)
        self.assertIn("net", result)
        self.assertIn("day", result)
    
    def test_get_holdings(self):
        """Test getting holdings."""
        mock_holdings = [
            {"tradingsymbol": "RELIANCE", "quantity": 100, "average_price": 2500}
        ]
        self.mock_kite.holdings.return_value = mock_holdings
        
        result = self.kite_api.get_holdings()
        
        self.assertEqual(result, mock_holdings)
    
    def test_get_profile(self):
        """Test getting user profile."""
        mock_profile = {
            "user_id": "test_user",
            "user_name": "Test User",
            "email": "test@example.com"
        }
        self.mock_kite.profile.return_value = mock_profile
        
        result = self.kite_api.get_profile()
        
        self.assertEqual(result, mock_profile)
    
    # ==================== MARKET DATA TESTS ====================
    
    def test_get_quote(self):
        """Test getting market quotes."""
        mock_quote = {
            "NSE:RELIANCE": {
                "last_price": 2500.0,
                "volume": 1000000,
                "ohlc": {"open": 2480, "high": 2520, "low": 2470, "close": 2490}
            }
        }
        self.mock_kite.quote.return_value = mock_quote
        
        # Test single instrument
        result = self.kite_api.get_quote("NSE:RELIANCE")
        self.assertEqual(result, mock_quote)
        
        # Test multiple instruments
        result = self.kite_api.get_quote(["NSE:RELIANCE", "NSE:TCS"])
        self.assertEqual(result, mock_quote)
    
    def test_get_ltp(self):
        """Test getting Last Traded Price."""
        mock_ltp = {
            "NSE:RELIANCE": {"last_price": 2500.0}
        }
        self.mock_kite.ltp.return_value = mock_ltp
        
        result = self.kite_api.get_ltp("NSE:RELIANCE")
        
        self.assertEqual(result, mock_ltp)
    
    def test_get_historical_data(self):
        """Test getting historical data."""
        mock_historical = [
            {
                "date": "2024-01-01T00:00:00+0530",
                "open": 2480,
                "high": 2520,
                "low": 2470,
                "close": 2500,
                "volume": 1000000
            }
        ]
        self.mock_kite.historical_data.return_value = mock_historical
        
        result = self.kite_api.get_historical_data(
            instrument_token="738561",
            from_date="2024-01-01",
            to_date="2024-01-31",
            interval="day"
        )
        
        self.assertEqual(result, mock_historical)
    
    # ==================== UTILITY METHOD TESTS ====================
    
    def test_convert_position(self):
        """Test position conversion."""
        mock_response = {"status": "success"}
        self.mock_kite.convert_position.return_value = mock_response
        
        result = self.kite_api.convert_position(
            exchange="NSE",
            tradingsymbol="RELIANCE",
            t_type="BUY",
            quantity=10,
            old_p_type="MIS",
            new_p_type="CNC"
        )
        
        self.assertEqual(result, mock_response)
    
    def test_get_pnl_summary(self):
        """Test P&L summary calculation."""
        mock_positions = {
            "net": [
                {"pnl": 500, "realised": 300, "unrealised": 200},
                {"pnl": -100, "realised": 0, "unrealised": -100}
            ],
            "day": []
        }
        self.mock_kite.positions.return_value = mock_positions
        
        result = self.kite_api.get_pnl_summary()
        
        self.assertEqual(result["total_pnl"], 400)
        self.assertEqual(result["realized_pnl"], 300)
        self.assertEqual(result["unrealized_pnl"], 100)
        self.assertEqual(result["position_count"], 2)
    
    def test_search_instruments(self):
        """Test instrument search functionality."""
        mock_instruments = [
            {"tradingsymbol": "RELIANCE", "name": "Reliance Industries", "exchange": "NSE"},
            {"tradingsymbol": "TCS", "name": "Tata Consultancy Services", "exchange": "NSE"},
            {"tradingsymbol": "RELIANCEBANK", "name": "Reliance Bank", "exchange": "BSE"}
        ]
        self.mock_kite.instruments.return_value = mock_instruments
        
        result = self.kite_api.search_instruments("RELIANCE")
        
        # Should find instruments with "RELIANCE" in symbol or name
        self.assertEqual(len(result), 2)
        symbols = [inst["tradingsymbol"] for inst in result]
        self.assertIn("RELIANCE", symbols)
        self.assertIn("RELIANCEBANK", symbols)
    
    def test_validate_order_params(self):
        """Test order parameter validation."""
        # Test valid parameters
        result = self.kite_api.validate_order_params(
            exchange="NSE",
            p_type="CNC",
            order_type="MARKET"
        )
        self.assertTrue(result["valid"])
        self.assertEqual(len(result["errors"]), 0)
        
        # Test invalid parameters
        result = self.kite_api.validate_order_params(
            exchange="INVALID",
            p_type="INVALID",
            order_type="INVALID"
        )
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["errors"]), 3)
    
    # ==================== ERROR HANDLING TESTS ====================
    
    def test_error_handling_orders(self):
        """Test error handling in order methods."""
        self.mock_kite.orders.side_effect = Exception("Network error")
        
        result = self.kite_api.get_orders()
        
        self.assertEqual(result, [])
    
    def test_error_handling_positions(self):
        """Test error handling in position methods."""
        self.mock_kite.positions.side_effect = Exception("API error")
        
        result = self.kite_api.get_positions()
        
        self.assertEqual(result, {"net": [], "day": []})
    
    # ==================== INTEGRATION TESTS ====================
    
    def test_order_flow_integration(self):
        """Test complete order flow from placement to cancellation."""
        # Mock order placement
        place_response = {"order_id": "123456", "status": "success"}
        self.mock_kite.place_order.return_value = place_response
        
        # Mock order modification
        modify_response = {"order_id": "123456", "status": "modified"}
        self.mock_kite.modify_order.return_value = modify_response
        
        # Mock order cancellation
        cancel_response = {"order_id": "123456", "status": "cancelled"}
        self.mock_kite.cancel_order.return_value = cancel_response
        
        # Test flow
        place_result = self.kite_api.place_limit_order(
            tradingsymbol="RELIANCE",
            exchange="NSE",
            t_type="BUY",
            quantity=10,
            p_type="CNC",
            price=2500.0
        )
        
        modify_result = self.kite_api.modify_order(
            order_id="123456",
            price=2600.0
        )
        
        cancel_result = self.kite_api.cancel_order(order_id="123456")
        
        self.assertEqual(place_result["order_id"], "123456")
        self.assertEqual(modify_result["status"], "modified")
        self.assertEqual(cancel_result["status"], "cancelled")


class KiteApiLiveTests:
    """
    Live testing class for actual API testing (use with caution).
    Only run these tests in a sandbox environment with valid credentials.
    """
    
    def __init__(self, api_key: str, access_token: str):
        """Initialize with real credentials for live testing."""
        self.kite_api = Kite_Api(api_key, access_token)
        self.test_results = []
    
    def test_basic_connectivity(self):
        """Test basic API connectivity."""
        try:
            profile = self.kite_api.get_profile()
            if profile and "user_id" in profile:
                self.log_result("✅ Basic connectivity", "PASS", f"Connected as {profile.get('user_name', 'Unknown')}")
                return True
            else:
                self.log_result("❌ Basic connectivity", "FAIL", "No profile data received")
                return False
        except Exception as e:
            self.log_result("❌ Basic connectivity", "FAIL", str(e))
            return False
    
    def test_market_data_retrieval(self):
        """Test market data retrieval functions."""
        test_instruments = ["NSE:RELIANCE", "NSE:TCS"]
        
        try:
            # Test quotes
            quotes = self.kite_api.get_quote(test_instruments)
            if quotes:
                self.log_result("✅ Quote retrieval", "PASS", f"Retrieved quotes for {len(quotes)} instruments")
            else:
                self.log_result("❌ Quote retrieval", "FAIL", "No quote data received")
            
            # Test LTP
            ltp = self.kite_api.get_ltp(test_instruments)
            if ltp:
                self.log_result("✅ LTP retrieval", "PASS", f"Retrieved LTP for {len(ltp)} instruments")
            else:
                self.log_result("❌ LTP retrieval", "FAIL", "No LTP data received")
            
            # Test OHLC
            ohlc = self.kite_api.get_ohlc(test_instruments)
            if ohlc:
                self.log_result("✅ OHLC retrieval", "PASS", f"Retrieved OHLC for {len(ohlc)} instruments")
            else:
                self.log_result("❌ OHLC retrieval", "FAIL", "No OHLC data received")
                
        except Exception as e:
            self.log_result("❌ Market data retrieval", "FAIL", str(e))
    
    def test_account_data_retrieval(self):
        """Test account-related data retrieval."""
        try:
            # Test orders
            orders = self.kite_api.get_orders()
            self.log_result("✅ Orders retrieval", "PASS", f"Retrieved {len(orders)} orders")
            
            # Test positions
            positions = self.kite_api.get_positions()
            net_positions = len(positions.get("net", []))
            day_positions = len(positions.get("day", []))
            self.log_result("✅ Positions retrieval", "PASS", 
                          f"Net: {net_positions}, Day: {day_positions}")
            
            # Test holdings
            holdings = self.kite_api.get_holdings()
            self.log_result("✅ Holdings retrieval", "PASS", f"Retrieved {len(holdings)} holdings")
            
            # Test margins
            margins = self.kite_api.get_margins()
            self.log_result("✅ Margins retrieval", "PASS", "Margin data retrieved")
            
        except Exception as e:
            self.log_result("❌ Account data retrieval", "FAIL", str(e))
    
    def test_instrument_search(self):
        """Test instrument search functionality."""
        try:
            # Search for a common stock
            results = self.kite_api.search_instruments("RELIANCE", "NSE")
            if results:
                self.log_result("✅ Instrument search", "PASS", 
                              f"Found {len(results)} instruments matching 'RELIANCE'")
            else:
                self.log_result("❌ Instrument search", "FAIL", "No instruments found")
                
        except Exception as e:
            self.log_result("❌ Instrument search", "FAIL", str(e))
    
    def test_validation_methods(self):
        """Test validation utility methods."""
        try:
            # Test parameter validation
            valid_result = self.kite_api.validate_order_params("NSE", "CNC", "MARKET")
            invalid_result = self.kite_api.validate_order_params("INVALID", "INVALID", "INVALID")
            
            if valid_result["valid"] and not invalid_result["valid"]:
                self.log_result("✅ Parameter validation", "PASS", "Validation working correctly")
            else:
                self.log_result("❌ Parameter validation", "FAIL", "Validation not working properly")
                
            # Test utility methods
            product_types = self.kite_api.get_supported_product_types()
            order_types = self.kite_api.get_supported_order_types()
            exchanges = self.kite_api.get_supported_exchanges()
            
            if product_types and order_types and exchanges:
                self.log_result("✅ Utility methods", "PASS", 
                              f"Products: {len(product_types)}, Orders: {len(order_types)}, Exchanges: {len(exchanges)}")
            else:
                self.log_result("❌ Utility methods", "FAIL", "Some utility methods returned empty results")
                
        except Exception as e:
            self.log_result("❌ Validation methods", "FAIL", str(e))
    
    def log_result(self, test_name: str, status: str, details: str):
        """Log test results."""
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{test_name}: {status} - {details}")
    
    def run_all_tests(self):
        """Run all live tests."""
        print("🚀 Starting Kite API Live Tests...")
        print("=" * 50)
        
        # Run tests in sequence
        if self.test_basic_connectivity():
            self.test_market_data_retrieval()
            self.test_account_data_retrieval()
            self.test_instrument_search()
            self.test_validation_methods()
        else:
            print("❌ Basic connectivity failed. Skipping other tests.")
        
        print("\n" + "=" * 50)
        print("📊 Test Summary:")
        
        passed = sum(1 for r in self.test_results if "PASS" in r["status"])
        failed = sum(1 for r in self.test_results if "FAIL" in r["status"])
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed / (passed + failed) * 100):.1f}%" if (passed + failed) > 0 else "No tests run")
        
        return self.test_results


# ==================== MOCK DATA FIXTURES ====================

class MockDataGenerator:
    """Generate realistic mock data for testing."""
    
    @staticmethod
    def generate_mock_orders(count: int = 5) -> List[Dict]:
        """Generate mock order data."""
        orders = []
        for i in range(count):
            orders.append({
                "order_id": f"12345{i:02d}",
                "tradingsymbol": f"STOCK{i}",
                "exchange": "NSE",
                "transaction_type": "BUY" if i % 2 == 0 else "SELL",
                "quantity": (i + 1) * 10,
                "price": 2500 + (i * 100),
                "status": "COMPLETE" if i % 3 == 0 else "OPEN",
                "order_timestamp": datetime.now().isoformat()
            })
        return orders
    
    @staticmethod
    def generate_mock_positions(count: int = 3) -> Dict:
        """Generate mock position data."""
        positions = []
        for i in range(count):
            positions.append({
                "tradingsymbol": f"STOCK{i}",
                "exchange": "NSE",
                "quantity": (i + 1) * 10,
                "product": "CNC",
                "pnl": (i - 1) * 100,  # Mix of profit/loss
                "realised": i * 50,
                "unrealised": (i - 1) * 50
            })
        
        return {"net": positions, "day": []}


# ==================== PERFORMANCE TESTING ====================

class PerformanceTest:
    """Performance testing for Kite API operations."""
    
    def __init__(self, kite_api):
        self.kite_api = kite_api
        self.performance_results = []
    
    def time_operation(self, operation_name: str, operation_func):
        """Time an operation and log results."""
        start_time = datetime.now()
        try:
            result = operation_func()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.performance_results.append({
                "operation": operation_name,
                "duration": duration,
                "status": "success",
                "timestamp": start_time.isoformat()
            })
            
            print(f"{operation_name}: {duration:.3f}s ✅")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            self.performance_results.append({
                "operation": operation_name,
                "duration": duration,
                "status": "error",
                "error": str(e),
                "timestamp": start_time.isoformat()
            })
            
            print(f"{operation_name}: {duration:.3f}s ❌ - {str(e)}")
            return None
    
    def run_performance_tests(self):
        """Run performance tests on various operations."""
        print("🏃 Running Performance Tests...")
        print("=" * 40)
        
        # Test data retrieval performance
        self.time_operation("Get Profile", lambda: self.kite_api.get_profile())
        self.time_operation("Get Orders", lambda: self.kite_api.get_orders())
        self.time_operation("Get Positions", lambda: self.kite_api.get_positions())
        self.time_operation("Get Holdings", lambda: self.kite_api.get_holdings())
        
        # Test market data performance
        self.time_operation("Get Quote", lambda: self.kite_api.get_quote("NSE:RELIANCE"))
        self.time_operation("Get LTP", lambda: self.kite_api.get_ltp(["NSE:RELIANCE", "NSE:TCS"]))
        
        # Performance summary
        print("\n📊 Performance Summary:")
        successful_ops = [r for r in self.performance_results if r["status"] == "success"]
        if successful_ops:
            avg_duration = sum(r["duration"] for r in successful_ops) / len(successful_ops)
            print(f"Average operation time: {avg_duration:.3f}s")
            
            fastest = min(successful_ops, key=lambda x: x["duration"])
            slowest = max(successful_ops, key=lambda x: x["duration"])
            
            print(f"Fastest: {fastest['operation']} ({fastest['duration']:.3f}s)")
            print(f"Slowest: {slowest['operation']} ({slowest['duration']:.3f}s)")


# ==================== USAGE EXAMPLES ====================

def run_unit_tests():
    """Run all unit tests."""
    print("🧪 Running Unit Tests...")
    print("=" * 40)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestKiteApi)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\n📊 Unit Test Results:")
    print(f"✅ Tests passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests failed: {len(result.failures)}")
    print(f"💥 Errors: {len(result.errors)}")
    
    return result.wasSuccessful()

def run_live_tests(api_key: str, access_token: str):
    """Run live tests with actual API."""
    print("🔴 CAUTION: Running live tests with actual API!")
    print("Make sure you're using a sandbox environment.")
    
    confirmation = input("Continue? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("Live tests cancelled.")
        return
    
    live_tester = KiteApiLiveTests(api_key, access_token)
    return live_tester.run_all_tests()

def run_performance_tests(api_key: str, access_token: str):
    """Run performance tests."""
    try:
        from kite_connect import Kite_Api
        kite_api = Kite_Api(api_key, access_token)
        
        perf_tester = PerformanceTest(kite_api)
        perf_tester.run_performance_tests()
        
        return perf_tester.performance_results
    except Exception as e:
        print(f"Performance test setup failed: {e}")
        return []

# ==================== MAIN EXECUTION ====================

if __name__ == "__main__":
    """
    Main execution block for running tests.
    
    Choose which type of tests to run:
    1. Unit tests (recommended - safe, no real API calls)
    2. Live tests (requires valid credentials, use with caution)
    3. Performance tests (requires valid credentials)
    """
    
    print("🎯 Kite API Testing Suite")
    print("=" * 50)
    print("1. Unit Tests (Recommended)")
    print("2. Live Tests (Requires valid credentials)")
    print("3. Performance Tests (Requires valid credentials)")
    print("4. All Unit Tests Only")
    
    choice = input("\nSelect test type (1-4): ")
    
    if choice == "1" or choice == "4":
        # Run unit tests
        success = run_unit_tests()
        if success:
            print("\n🎉 All unit tests passed!")
        else:
            print("\n⚠️ Some unit tests failed. Check the output above.")
    
    elif choice == "2":
        # Live tests
        api_key = input("Enter API Key: ")
        access_token = input("Enter Access Token: ")
        
        print("\n🔴 WARNING: This will make actual API calls!")
        print("Ensure you're using a sandbox environment.")
        
        live_results = run_live_tests(api_key, access_token)
        
        if live_results:
            print("\n📈 Live test results saved for analysis.")
    
    elif choice == "3":
        # Performance tests
        api_key = input("Enter API Key: ")
        access_token = input("Enter Access Token: ")
        
        print("\n⚡ Running Performance Tests...")
        perf_results = run_performance_tests(api_key, access_token)
        
        if perf_results:
            print(f"\n📊 Performance data collected for {len(perf_results)} operations.")
    
    else:
        print("Invalid choice. Running unit tests by default.")
        run_unit_tests()


# ==================== ADDITIONAL TESTING UTILITIES ====================

class TestDataValidator:
    """Validate data returned by Kite API methods."""
    
    @staticmethod
    def validate_order_response(response: Dict) -> bool:
        """Validate order placement response."""
        required_fields = ["order_id"]
        return all(field in response for field in required_fields)
    
    @staticmethod
    def validate_quote_data(quote_data: Dict) -> bool:
        """Validate quote data structure."""
        if not quote_data:
            return False
        
        for instrument, data in quote_data.items():
            required_fields = ["last_price"]
            if not all(field in data for field in required_fields):
                return False
        return True
    
    @staticmethod
    def validate_position_data(positions: Dict) -> bool:
        """Validate positions data structure."""
        required_keys = ["net", "day"]
        return all(key in positions for key in required_keys)


class TestScenarios:
    """Common testing scenarios for different trading strategies."""
    
    def __init__(self, kite_api):
        self.kite_api = kite_api
    
    def test_intraday_trading_scenario(self):
        """Test a complete intraday trading scenario."""
        print("🔄 Testing Intraday Trading Scenario...")
        
        # This is a safe test that doesn't place actual orders
        # Just validates the API methods work
        
        try:
            # 1. Check available margin
            margins = self.kite_api.get_margins("equity")
            print(f"Available margin: {margins.get('available', {}).get('cash', 'N/A')}")
            
            # 2. Get current market price
            quote = self.kite_api.get_quote("NSE:RELIANCE")
            if quote and "NSE:RELIANCE" in quote:
                current_price = quote["NSE:RELIANCE"].get("last_price", 0)
                print(f"Current RELIANCE price: ₹{current_price}")
            
            # 3. Validate order parameters
            validation = self.kite_api.validate_order_params("NSE", "MIS", "LIMIT")
            print(f"Order validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Intraday scenario test failed: {e}")
            return False
    
    def test_delivery_trading_scenario(self):
        """Test a delivery trading scenario."""
        print("📦 Testing Delivery Trading Scenario...")
        
        try:
            # 1. Check holdings
            holdings = self.kite_api.get_holdings()
            print(f"Current holdings: {len(holdings)} stocks")
            
            # 2. Check available cash for delivery
            margins = self.kite_api.get_margins("equity")
            if margins:
                available_cash = margins.get('available', {}).get('cash', 0)
                print(f"Available cash for delivery: ₹{available_cash}")
            
            # 3. Validate CNC order parameters
            validation = self.kite_api.validate_order_params("NSE", "CNC", "LIMIT")
            print(f"CNC order validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            
            return True
            
        except Exception as e:
            print(f"❌ Delivery scenario test failed: {e}")
            return False
    
    def test_options_trading_scenario(self):
        """Test options trading scenario."""
        print("📈 Testing Options Trading Scenario...")
        
        try:
            # 1. Search for NIFTY options
            nifty_options = self.kite_api.search_instruments("NIFTY", "NFO")
            options_count = len([opt for opt in nifty_options if "CE" in opt.get("tradingsymbol", "") or "PE" in opt.get("tradingsymbol", "")])
            print(f"Found {options_count} NIFTY options")
            
            # 2. Validate F&O order parameters
            validation = self.kite_api.validate_order_params("NFO", "NRML", "MARKET")
            print(f"F&O order validation: {'✅ Valid' if validation['valid'] else '❌ Invalid'}")
            
            # 3. Check F&O margins
            margins = self.kite_api.get_margins("commodity")  # or equity for F&O
            print("F&O margin check completed")
            
            return True
            
        except Exception as e:
            print(f"❌ Options scenario test failed: {e}")
            return False


# ==================== AUTOMATED TEST RUNNER ====================

class AutomatedTestRunner:
    """Automated test runner with comprehensive reporting."""
    
    def __init__(self, config: Dict):
        """
        Initialize with test configuration.
        
        Args:
            config: Test configuration dictionary
        """
        self.config = config
        self.results = {
            "start_time": datetime.now(),
            "unit_tests": {},
            "live_tests": {},
            "performance_tests": {},
            "scenarios": {}
        }
    
    def run_comprehensive_tests(self):
        """Run all types of tests based on configuration."""
        print("🚀 Starting Comprehensive Kite API Tests")
        print("=" * 60)
        
        # Run unit tests
        if self.config.get("run_unit_tests", True):
            print("\n1️⃣ Running Unit Tests...")
            self.results["unit_tests"]["success"] = run_unit_tests()
        
        # Run live tests if credentials provided
        if self.config.get("api_key") and self.config.get("access_token"):
            if self.config.get("run_live_tests", False):
                print("\n2️⃣ Running Live Tests...")
                live_tester = KiteApiLiveTests(
                    self.config["api_key"], 
                    self.config["access_token"]
                )
                self.results["live_tests"]["results"] = live_tester.run_all_tests()
            
            if self.config.get("run_performance_tests", False):
                print("\n3️⃣ Running Performance Tests...")
                self.results["performance_tests"]["results"] = run_performance_tests(
                    self.config["api_key"], 
                    self.config["access_token"]
                )
            
            if self.config.get("run_scenarios", False):
                print("\n4️⃣ Running Trading Scenarios...")
                from kite_connect import Kite_Api
                kite_api = Kite_Api(self.config["api_key"], self.config["access_token"])
                scenarios = TestScenarios(kite_api)
                
                self.results["scenarios"]["intraday"] = scenarios.test_intraday_trading_scenario()
                self.results["scenarios"]["delivery"] = scenarios.test_delivery_trading_scenario()
                self.results["scenarios"]["options"] = scenarios.test_options_trading_scenario()
        
        self.results["end_time"] = datetime.now()
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        start_time = self.results["start_time"]
        end_time = self.results["end_time"]
        duration = end_time - start_time
        
        print(f"Test Duration: {duration.total_seconds():.2f} seconds")
        print(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Unit test results
        if self.results["unit_tests"]:
            unit_success = self.results["unit_tests"].get("success", False)
            print(f"\n📝 Unit Tests: {'✅ PASSED' if unit_success else '❌ FAILED'}")
        
        # Live test results
        if self.results["live_tests"]:
            live_results = self.results["live_tests"]["results"]
            if live_results:
                passed = sum(1 for r in live_results if "PASS" in r.get("status", ""))
                total = len(live_results)
                print(f"🔴 Live Tests: {passed}/{total} passed ({(passed/total*100):.1f}%)")
        
        # Performance test results
        if self.results["performance_tests"]:
            perf_results = self.results["performance_tests"]["results"]
            if perf_results:
                successful = [r for r in perf_results if r["status"] == "success"]
                if successful:
                    avg_time = sum(r["duration"] for r in successful) / len(successful)
                    print(f"⚡ Performance: Avg {avg_time:.3f}s per operation")
        
        # Scenario test results
        if self.results["scenarios"]:
            scenarios = self.results["scenarios"]
            passed_scenarios = sum(1 for success in scenarios.values() if success)
            total_scenarios = len(scenarios)
            print(f"🎭 Scenarios: {passed_scenarios}/{total_scenarios} passed")
        
        print("\n" + "=" * 60)


# ==================== QUICK TEST FUNCTIONS ====================

def quick_unit_test():
    """Quick unit test for basic functionality."""
    print("⚡ Quick Unit Test")
    
    # Test initialization without actual API
    with patch('kiteconnect.KiteConnect'):
        try:
            kite_api = Kite_Api("test_key", "test_token")
            
            # Test mapping dictionaries
            assert "BUY" in kite_api.t_type_dict
            assert "NSE" in kite_api.ex_seg_dict
            assert "CNC" in kite_api.p_type_dict
            
            # Test validation
            validation = kite_api.validate_order_params("NSE", "CNC", "MARKET")
            assert validation["valid"] == True
            
            print("✅ Quick test passed!")
            return True
            
        except Exception as e:
            print(f"❌ Quick test failed: {e}")
            return False

def demo_usage():
    """Demonstrate how to use the testing framework."""
    print("📚 Demo: How to Test Kite_Api Class")
    print("=" * 50)
    
    print("""
    # Example 1: Run unit tests only (Safe)
    python test_kite_api.py
    # Then select option 1
    
    # Example 2: Quick validation test
    quick_unit_test()
    
    # Example 3: Live testing (Use sandbox credentials)
    config = {
        "api_key": "your_api_key",
        "access_token": "your_access_token",
        "run_unit_tests": True,
        "run_live_tests": True,
        "run_performance_tests": False,
        "run_scenarios": True
    }
    
    runner = AutomatedTestRunner(config)
    runner.run_comprehensive_tests()
    
    # Example 4: Test specific functionality
    with patch('kiteconnect.KiteConnect') as mock_kite:
        kite_api = Kite_Api("test_key", "test_token")
        
        # Mock responses for testing
        mock_kite.return_value.orders.return_value = [
            {"order_id": "123", "status": "COMPLETE"}
        ]
        
        orders = kite_api.get_orders()
        assert len(orders) == 1
        assert orders[0]["order_id"] == "123"
    """)

# Run demo if script is executed directly
if __name__ == "__main__":
    # Quick validation
    if quick_unit_test():
        # Show menu for full testing
        demo_usage()
    else:
        print("❌ Basic validation failed. Please check your setup.")