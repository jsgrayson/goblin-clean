"""
Database Manager - SQLite/PostgreSQL integration for long-term storage
"""
import sqlite3
import pandas as pd
from loguru import logger
import os
import json

class DatabaseManager:
    """
    Manages database connections and schema.
    Defaults to SQLite for ease of use, but structure supports PostgreSQL.
    """
    
    def __init__(self, db_path: str = "goblin_ai.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Price History Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                price INTEGER,
                quantity INTEGER,
                timestamp INTEGER
            )
        ''')
        
        # Predictions Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                predicted_price INTEGER,
                confidence REAL,
                timestamp INTEGER,
                target_date INTEGER
            )
        ''')
        
        # Transactions Table (Accounting)
        c.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                type TEXT, -- BUY or SELL
                price INTEGER,
                quantity INTEGER,
                timestamp INTEGER,
                character TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Database initialized at {self.db_path}")

    def save_scan_data(self, df: pd.DataFrame):
        """Save scan data to DB."""
        conn = sqlite3.connect(self.db_path)
        try:
            # Ensure columns match
            df_to_save = df[['item_id', 'price', 'quantity', 'timestamp']].copy()
            df_to_save.to_sql('price_history', conn, if_exists='append', index=False)
            logger.info(f"Saved {len(df)} records to price_history.")
        except Exception as e:
            logger.error(f"Error saving scan data: {e}")
        finally:
            conn.close()

    def get_price_history(self, item_id: int, limit: int = 100) -> pd.DataFrame:
        """Fetch price history for an item."""
        conn = sqlite3.connect(self.db_path)
        query = f"SELECT * FROM price_history WHERE item_id = {item_id} ORDER BY timestamp DESC LIMIT {limit}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def save_prediction(self, predictions: List[Dict]):
        """Save predictions."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        try:
            for p in predictions:
                c.execute('''
                    INSERT INTO predictions (item_id, predicted_price, confidence, timestamp, target_date)
                    VALUES (?, ?, ?, ?, ?)
                ''', (p['item_id'], p['price'], p['confidence'], p['timestamp'], p['target_date']))
            conn.commit()
        finally:
            conn.close()

    def migrate_from_csv(self, csv_path: str):
        """One-time migration from CSV to DB."""
        if os.path.exists(csv_path):
            logger.info(f"Migrating {csv_path} to database...")
            df = pd.read_csv(csv_path)
            # Rename columns if needed to match schema
            # df = df.rename(columns={'marketValue': 'price'}) 
            self.save_scan_data(df)
            logger.success("Migration complete.")

if __name__ == "__main__":
    # Test
    db = DatabaseManager()
    # Mock data
    mock_df = pd.DataFrame({
        'item_id': [123, 456],
        'price': [1000, 5000],
        'quantity': [10, 5],
        'timestamp': [1700000000, 1700000000]
    })
    db.save_scan_data(mock_df)
    print(db.get_price_history(123))
