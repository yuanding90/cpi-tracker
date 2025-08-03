import json
import time
import os
from database import init_db, add_product_if_not_exists, save_price, export_to_csv, check_if_scraped_today
from scraper import get_price

def load_products():
    """Loads the list of products to track from the JSON file."""
    print("[DEBUG] Attempting to load products from products.json...")
    try:
        with open('products.json', 'r') as f:
            products = json.load(f)
            print(f"[SUCCESS] Loaded {len(products)} product(s) from file.")
            return products
    except FileNotFoundError:
        print("[ERROR] `products.json` not found. Please ensure the file exists.")
        return []
    except json.JSONDecodeError:
        print("[ERROR] Could not decode `products.json`. Please check for formatting errors (like extra commas).")
        return []

def main():
    """Main function to run the CPI tracker."""
    print("[DEBUG] main() function started.")
    
    # Ensure database exists
    if not os.path.exists('cpi_data.db'):
        print("[INFO] Database file 'cpi_data.db' not found. Creating it now.")
        init_db()
    else:
        print("[INFO] Database file 'cpi_data.db' already exists.")

    products_to_track = load_products()
    
    # CRITICAL CHECK: Stop if no products were loaded
    if not products_to_track:
        print("[CRITICAL] No products to track. Exiting script.")
        return

    print("\n--- Starting Price Collection ---")

    for product in products_to_track:
        name = product.get('name')
        category = product.get('category')
        url = product.get('url')
        selector = product.get('price_selector')

        if not all([name, category, url, selector]):
            print(f"[WARNING] Skipping invalid product entry in JSON: {product}")
            continue

        print(f"\nProcessing '{name}'...")
        print(f"  -  URL: {url}")

        # Add product to DB if it's not there and get its ID
        product_id = add_product_if_not_exists(name, category, url)

        # Check if this product has already been scraped today
        if check_if_scraped_today(product_id):
            print(f"  -  [INFO] Already scraped this product today. Skipping.")
            continue

        # If not scraped today, proceed with scraping
        print(f"  -  [INFO] No data for today. Scraping price...")
        price = get_price(url, selector)

        if price is not None:
            print(f"  -  [SUCCESS] Found price ${price:.2f}")
            # Save the found price to the database
            save_price(product_id, price)
        else:
            print(f"  -  [FAILURE] Could not retrieve price for '{name}'.")
        
        # Be a good internet citizen - wait a bit between requests
        time.sleep(2) 

    print("\n--- Price Collection Finished ---")

    # After collecting prices, export the latest data to a CSV file
    export_to_csv()


# This is the entry point of the script
if __name__ == '__main__':
    print("--- Data Collection Script Started ---")
    main()
    print("--- Data Collection Script Finished ---")