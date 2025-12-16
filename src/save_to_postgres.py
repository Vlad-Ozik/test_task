import json
import logging
import os
import psycopg2
from psycopg2 import sql
from typing import Dict, Any


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Establish connection to PostgreSQL using environment variables or defaults."""
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        database=os.getenv('CURRENCY_DB_NAME'),
        user=os.getenv('CURRENCY_DB_USER'),
        password=os.getenv('CURRENCY_DB_PASSWORD'),
        port=os.getenv('CURRENCY_DB_PORT', '5432')
    )

def create_table_if_not_exists(cursor):
    """Create the processed_rate_changes table if it doesn't exist."""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS processed_rate_changes (
        id SERIAL PRIMARY KEY,
        calculation_date DATE NOT NULL,
        current_rate_date DATE NOT NULL,
        previous_rate_date DATE NOT NULL,
        base_currency CHAR(3) NOT NULL,
        target_currency CHAR(3) NOT NULL,
        current_rate NUMERIC(18, 6) NOT NULL,
        previous_rate NUMERIC(18, 6) NOT NULL,
        pct_change NUMERIC(10, 4) NOT NULL,
        CONSTRAINT uq_processed_date_pair UNIQUE (calculation_date, current_rate_date, previous_rate_date, base_currency, target_currency)
    );
    
    CREATE INDEX IF NOT EXISTS idx_processed_date ON processed_rate_changes(calculation_date);
    CREATE INDEX IF NOT EXISTS idx_processed_pair ON processed_rate_changes(base_currency, target_currency);
    """
    cursor.execute(create_table_query)

def save_processed_data_to_db(json_filepath: str) -> None:
    """
    Read processed data from JSON file and save to PostgreSQL.
    
    Args:
        json_filepath: Path to the JSON file containing processed rates.
    """
    logger.info(f"Starting database import from {json_filepath}")
    
    if not os.path.exists(json_filepath):
        raise FileNotFoundError(f"File not found: {json_filepath}")
        
    try:
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            create_table_if_not_exists(cur)
            
            base_currency = data['base_currency']
            current_rate_date = data['date_t1']
            previous_rate_date = data['date_t2']
            calculation_date = data['analysis_timestamp'].split('T')[0]
            
            records_inserted = 0
            
            insert_query = """
            INSERT INTO processed_rate_changes (
                calculation_date, current_rate_date, previous_rate_date, 
                base_currency, target_currency, 
                current_rate, previous_rate, pct_change
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT ON CONSTRAINT uq_processed_date_pair 
            DO UPDATE SET
                current_rate = EXCLUDED.current_rate,
                previous_rate = EXCLUDED.previous_rate,
                pct_change = EXCLUDED.pct_change;
            """
            
            for target_currency, details in data['rates'].items():
                cur.execute(insert_query, (
                    calculation_date,
                    current_rate_date,
                    previous_rate_date,
                    base_currency,
                    target_currency,
                    details['rate_t1'],
                    details['rate_t2'],
                    details['pct_change']
                ))
                records_inserted += 1
                
            conn.commit()
            logger.info(f"Successfully inserted/updated {records_inserted} records in database.")
            
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            cur.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Failed to save data to database: {e}")
        raise

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        save_processed_data_to_db(sys.argv[1])
    else:
        logger.error("Usage: python save_to_postgres.py <json_filepath>")
