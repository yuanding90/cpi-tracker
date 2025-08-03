import requests
from bs4 import BeautifulSoup
import re

def get_price(url, selector):
    """
    Scrapes a single product page to get the price.

    Args:
        url (str): The URL of the product page.
        selector (str): The CSS selector for the price element.

    Returns:
        float: The price as a float, or None if not found.
    """
    try:
        # Set a User-Agent header to mimic a browser and avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Fetch the content from the URL
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the HTML content
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the price element using the provided CSS selector
        price_element = soup.select_one(selector)

        if not price_element:
            print(f"  -  Selector '{selector}' not found on page.")
            return None

        price_text = price_element.get_text()

        # Use regex to find the first number (integer or float) in the string
        # This is robust against extra text like "$", "USD", "Sale", etc.
        price_match = re.search(r'[\d,]+\.?\d*', price_text)
        if price_match:
            # Remove commas and convert to float
            cleaned_price = price_match.group(0).replace(',', '')
            return float(cleaned_price)
        else:
            print(f"  -  Could not parse price from text: '{price_text}'")
            return None

    except requests.exceptions.RequestException as e:
        print(f"  -  Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"  -  An unexpected error occurred during scraping: {e}")
        return None