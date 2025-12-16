import unittest
import sys
import os
from datetime import datetime

# Add src to path to import the module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fetch_exchange_rates import calculate_percentage_change, get_last_business_day

class TestCalculations(unittest.TestCase):

    def test_calculate_percentage_change_basic(self):
        """Test basic percentage change calculation"""
        current_rates = {'USD': 1.10}
        previous_rates = {'USD': 1.00}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertIn('USD', changes)
        self.assertEqual(changes['USD']['pct_change'], 10.0)
        self.assertEqual(changes['USD']['rate_t1'], 1.10)
        self.assertEqual(changes['USD']['rate_t2'], 1.00)

    def test_calculate_percentage_change_negative(self):
        """Test negative percentage change"""
        current_rates = {'USD': 0.90}
        previous_rates = {'USD': 1.00}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertEqual(changes['USD']['pct_change'], -10.0)

    def test_calculate_percentage_change_zero_change(self):
        """Test zero percentage change"""
        current_rates = {'USD': 1.00}
        previous_rates = {'USD': 1.00}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertEqual(changes['USD']['pct_change'], 0.0)

    def test_calculate_percentage_change_missing_currency(self):
        """Test when a currency exists in current but not previous rates"""
        current_rates = {'USD': 1.10, 'GBP': 0.85}
        previous_rates = {'USD': 1.00}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertIn('USD', changes)
        self.assertNotIn('GBP', changes)

    def test_calculate_percentage_change_zero_previous_rate(self):
        """Test division by zero protection (though unlikely in real fx rates)"""
        current_rates = {'USD': 1.10}
        previous_rates = {'USD': 0.0}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertNotIn('USD', changes)

    def test_calculate_percentage_change_rounding(self):
        """Test rounding to 4 decimal places"""
        current_rates = {'USD': 1.123456}
        previous_rates = {'USD': 1.00}
        
        changes = calculate_percentage_change(current_rates, previous_rates)
        
        self.assertEqual(changes['USD']['pct_change'], 12.3456)

    def test_get_last_business_day_simple(self):
        """Test that it returns a string date"""
        date_str = get_last_business_day()
        # Should match YYYY-MM-DD format
        self.assertRegex(date_str, r'^\d{4}-\d{2}-\d{2}$')

    def test_get_last_business_day_weekend_skip(self):
        """Test that it specifically skips weekends"""
        # Monday -> Sunday (skip) -> Saturday (skip) -> Friday
        monday = datetime(2023, 10, 23) # Oct 23 2023 is a Monday
        result = get_last_business_day(monday)
        self.assertEqual(result, '2023-10-20') # Should be Friday Oct 20

if __name__ == '__main__':
    unittest.main()
