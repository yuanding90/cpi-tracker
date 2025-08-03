import sqlite3
import csv
import uuid
from datetime import datetime

DB_NAME = 'cpi_data.db'

def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    print("[DEBUG] Attempting to initialize database...")
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create products table, using the URL as the unique identifier
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uuid TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            source_url TEXT NOT NULL UNIQUE
        )
    ''')
    print("[DEBUG] 'products' table checked/created.")

    # Create prices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            price REAL NOT NULL,
            date_collected TEXT NOT NULL,
            FOREIGN KEY (product_id) REFERENCES products (id)
        )
    ''')
    print("[DEBUG] 'prices' table checked/created.")

    conn.commit()
    conn.close()
    print("[SUCCESS] Database initialized successfully.")

def add_product_if_not_exists(name, category, url):
    """
    Adds a product to the database if it doesn't already exist based on its URL.
    Returns the product's ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if a product with this URL already exists
    cursor.execute("SELECT id FROM products WHERE source_url = ?", (url,))
    product = cursor.fetchone()
    
    if product:
        product_id = product['id']
    else:
        # If not, generate a uuid and insert it
        new_uuid = str(uuid.uuid4())
        cursor.execute(
            "INSERT INTO products (uuid, name, category, source_url) VALUES (?, ?, ?, ?)",
            (new_uuid, name, category, url)
        )
        conn.commit()
        product_id = cursor.lastrowid
        print(f"  -  [DEBUG] Added new product to database: {name} (UUID: {new_uuid})")
        
    conn.close()
    return product_id

def check_if_scraped_today(product_id):
    """
    Checks if a given product_id has already been scraped today.
    Returns True if scraped today, False otherwise.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    cursor.execute(
        "SELECT id FROM prices WHERE product_id = ? AND DATE(date_collected) = ?",
        (product_id, today_str)
    )
    result = cursor.fetchone()
    conn.close()
    
    # If a record is found, result is not None, so return True
    return result is not None

def save_price(product_id, price):
    """Saves a new price record to the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute(
        "INSERT INTO prices (product_id, price, date_collected) VALUES (?, ?, ?)",
        (product_id, price, date_str)
    )
    
    conn.commit()
    conn.close()

def export_to_csv():
    """Exports the most recent 1000 price entries to a CSV file."""
    print("\n[INFO] Exporting recent data to CSV...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # SQL query to join tables and get the latest 1000 records
        cursor.execute("""
            SELECT
                p.uuid,
                p.name,
                p.category,
                pr.price,
                pr.date_collected,
                p.source_url
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            ORDER BY pr.date_collected DESC
            LIMIT 1000
        """)
        
        rows = cursor.fetchall()
        
        if not rows:
            print("[INFO] No data to export.")
            return

        # Define the CSV file name
        csv_file_name = 'price_data_export.csv'
        
        with open(csv_file_name, 'w', newline='', encoding='utf-8') as csvfile:
            # Create a writer object
            csv_writer = csv.writer(csvfile)
            
            # Write the header row
            header = ['product_uuid', 'product_name', 'category', 'price', 'date_collected', 'source_url']
            csv_writer.writerow(header)
            
            # Write the data rows
            csv_writer.writerows(rows)
            
        print(f"[SUCCESS] Successfully exported {len(rows)} rows to {csv_file_name}")

    except sqlite3.Error as e:
        print(f"[ERROR] Database error during CSV export: {e}")
    finally:
        if conn:
            conn.close()