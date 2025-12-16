import requests
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)



def get_last_business_day(reference_date: datetime = None) -> str:
    """
    Get the last business day (skips weekends).
    
    Args:
        reference_date: Reference date to calculate from (default: today)
        
    Returns:
        str: Last business day in YYYY-MM-DD format
    """
    if reference_date is None:
        reference_date = datetime.now()
    
    current = reference_date - timedelta(days=1)
    

    while current.weekday() in [5, 6]:
        current -= timedelta(days=1)
    
    return current.strftime('%Y-%m-%d')


def get_yesterday_date() -> str:
    """
    Calculate yesterday's date (T-1), skipping weekends.
    
    Returns:
        str: Last business day in YYYY-MM-DD format
    """
    return get_last_business_day()


def fetch_exchange_rates(date: str, base_currency: str = 'EUR') -> Dict[str, Any]:
    """
    Fetch exchange rates from Frankfurter API.
    
    Args:
        date: Date in YYYY-MM-DD format
        base_currency: Base currency code (default: EUR)
    
    Returns:
        dict: Exchange rate data
    
    Raises:
        requests.exceptions.RequestException: If API request fails
        ValueError: If response data is invalid
    """
    url = f"https://api.frankfurter.app/{date}"
    params = {'from': base_currency}
    
    logger.info(f"Fetching exchange rates for {base_currency} on {date}")
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'rates' not in data:
            raise ValueError("Invalid response: 'rates' field missing")
        
        if 'date' not in data:
            raise ValueError("Invalid response: 'date' field missing")
        
        logger.info(f"Successfully fetched {len(data['rates'])} exchange rates")
        return data
        
    except requests.exceptions.Timeout:
        logger.error(f"Request timeout while fetching data from {url}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error occurred: {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching exchange rates: {e}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise ValueError(f"Invalid JSON response: {e}")


def save_to_file(data: Dict[str, Any], output_dir: str = '/app/data') -> str:
    """
    Save exchange rate data to JSON file.
    
    Args:
        data: Exchange rate data
        output_dir: Directory to save file (default: /app/data)
    
    Returns:
        str: Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"exchange_rates_{data['date']}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Exchange rates saved to {filepath}")
    return str(filepath)



def get_previous_date(date_str: str) -> str:
    """
    Calculate date before the given date (T-1 relative to date_str), skipping weekends.
    
    Args:
        date_str: Date in YYYY-MM-DD format
        
    Returns:
        str: Previous business day in YYYY-MM-DD format
    """
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    return get_last_business_day(date_obj)


def calculate_percentage_change(current_rates: Dict[str, float], previous_rates: Dict[str, float]) -> Dict[str, Any]:
    """
    Calculate percentage change between current and previous rates.
    Formula: ((Current - Previous) / Previous) * 100
    
    Args:
        current_rates: Dictionary of current exchange rates
        previous_rates: Dictionary of previous exchange rates
        
    Returns:
        dict: Dictionary containing rate changes and metadata
    """
    changes = {}
    
    for currency, current_rate in current_rates.items():
        if currency in previous_rates:
            prev_rate = previous_rates[currency]
            if prev_rate != 0:
                pct_change = ((current_rate - prev_rate) / prev_rate) * 100
                changes[currency] = {
                    'rate_t1': current_rate,
                    'rate_t2': prev_rate,
                    'pct_change': round(pct_change, 4)
                }
    
    return changes


def save_processed_data(data: Dict[str, Any], date_str: str, output_dir: str = '/app/data') -> str:
    """
    Save processed percentage change data to JSON file.
    
    Args:
        data: Processed data including percentage changes
        date_str: Reference date (T-1)
        output_dir: Directory to save file
        
    Returns:
        str: Path to saved file
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"processed_rate_changes_{date_str}_{timestamp}.json"
    filepath = output_path / filename
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Processed rate changes saved to {filepath}")
    return str(filepath)


def main():
    """
    Main function to fetch rates, calculate changes, and save results.
    """
    try:
        date_t1 = get_yesterday_date()
        logger.info(f"Processing exchange rates for T-1: {date_t1}")
        data_t1 = fetch_exchange_rates(date_t1, base_currency='EUR')
        
        filepath_t1 = save_to_file(data_t1)
        logger.info(f"T-1 Data saved to {filepath_t1}")
        
        date_t2 = get_previous_date(date_t1)
        logger.info(f"Fetching exchange rates for T-2: {date_t2}")
        data_t2 = fetch_exchange_rates(date_t2, base_currency='EUR')
        
        logger.info("Calculating percentage changes (T-1 vs T-2)")
        changes = calculate_percentage_change(data_t1['rates'], data_t2['rates'])
        
        processed_data = {
            'base_currency': 'EUR',
            'date_t1': date_t1,
            'date_t2': date_t2,
            'analysis_timestamp': datetime.now().isoformat(),
            'rates': changes
        }
        
        filepath_processed = save_processed_data(processed_data, date_t1)
        logger.info(f"Processed data successfully saved to {filepath_processed}")
        
        logger.info("Significant changes (> 0.5%):")
        for currency, details in changes.items():
            if abs(details['pct_change']) > 0.5:
                logger.info(f"  {currency}: {details['pct_change']}%")
        
        return str(filepath_processed)
        
    except Exception as e:
        logger.error(f"Failed to process exchange rates: {e}")
        raise


if __name__ == "__main__":
    main()
