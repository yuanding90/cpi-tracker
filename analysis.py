import sqlite3

def calculate_cpi():
    """
    Calculates the CPI by comparing the latest basket cost to the base period cost.
    """
    try:
        conn = sqlite3.connect('cpi_data.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # --- 1. Find the Base Period (the earliest date with a full set of prices) ---
        cursor.execute("SELECT MIN(DATE(date_collected)) FROM prices")
        base_date_result = cursor.fetchone()
        if not base_date_result or not base_date_result[0]:
            print("\nNot enough data to calculate CPI. Run the scraper first.")
            return

        base_date = base_date_result[0]

        # --- 2. Find the Current Period (the latest date with a full set of prices) ---
        cursor.execute("SELECT MAX(DATE(date_collected)) FROM prices")
        current_date = cursor.fetchone()[0]

        print(f"\n--- CPI Analysis ---")
        print(f"Base Period Date:    {base_date}")
        print(f"Current Period Date: {current_date}")

        # --- 3. Calculate Base Cost ---
        # Get the first price recorded on the base date for each product
        cursor.execute("""
            SELECT p.name, pr.price
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE DATE(pr.date_collected) = ?
            GROUP BY pr.product_id
        """, (base_date,))
        base_prices = cursor.fetchall()
        
        if not base_prices:
            print("Could not retrieve base prices. CPI calculation aborted.")
            return
            
        base_cost = sum(item['price'] for item in base_prices)
        
        print(f"\nBase Period Basket ({len(base_prices)} items):")
        for item in base_prices:
            print(f"  - {item['name']}: ${item['price']:.2f}")
        print(f"Total Base Cost: ${base_cost:.2f}")


        # --- 4. Calculate Current Cost ---
        cursor.execute("""
            SELECT p.name, pr.price
            FROM prices pr
            JOIN products p ON pr.product_id = p.id
            WHERE DATE(pr.date_collected) = ?
            GROUP BY pr.product_id
        """, (current_date,))
        current_prices = cursor.fetchall()

        if not current_prices:
            print("Could not retrieve current prices. CPI calculation aborted.")
            return

        current_cost = sum(item['price'] for item in current_prices)
        
        print(f"\nCurrent Period Basket ({len(current_prices)} items):")
        for item in current_prices:
            print(f"  - {item['name']}: ${item['price']:.2f}")
        print(f"Total Current Cost: ${current_cost:.2f}")


        # --- 5. Calculate and Display CPI ---
        if base_cost == 0:
            print("\nBase cost is zero, cannot calculate CPI.")
            return
        
        # The core CPI calculation
        cpi = (current_cost / base_cost) * 100
        
        print("\n--------------------------")
        print(f"Men's Shoe CPI: {cpi:.2f}")
        print("--------------------------")
        
        if cpi > 100:
            print(f"Interpretation: Prices have increased by {cpi - 100:.2f}% since the base period.")
        elif cpi < 100:
            print(f"Interpretation: Prices have decreased by {100 - cpi:.2f}% since the base period.")
        else:
            print("Interpretation: Prices have remained stable since the base period.")

    except sqlite3.Error as e:
        print(f"Database error during analysis: {e}")
    finally:
        if conn:
            conn.close()
