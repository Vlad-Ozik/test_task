import unittest
import sys
import os
from datetime import datetime

# Add src to path to import the module
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fetch_exchange_rates import calculate_percentage_change

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

if __name__ == '__main__':
    unittest.main()
