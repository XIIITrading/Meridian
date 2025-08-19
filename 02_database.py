# 02_database.py

import webbrowser
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def run():
    """
    Opens Rowzero database in Chrome browser.
    Uses Selenium for better control and reliability.
    """
    url = "https://www.rowzero.io"
    
    # Method 1: Simple approach with webbrowser (uncomment to use)
    # webbrowser.open(url)
    
    # Method 2: Selenium approach (recommended for automation)
    try:
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")
        
        # Optional: Run in headless mode (uncomment if you don't need to see the browser)
        # chrome_options.add_argument("--headless")
        
        # Create driver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        # Navigate to Rowzero
        print(f"Opening Rowzero database...")
        driver.get(url)
        
        # Keep browser open (remove/modify based on your needs)
        print("Browser opened successfully. Press Enter to close...")
        input()
        driver.quit()
        
    except Exception as e:
        print(f"Error opening browser: {e}")
        # Fallback to simple webbrowser method
        print("Attempting fallback method...")
        webbrowser.open(url)

def run_simple():
    """
    Simple alternative using just webbrowser module.
    Less control but no additional dependencies needed.
    """
    url = "https://www.rowzero.io"
    print(f"Opening Rowzero database in default browser...")
    webbrowser.open(url)
    print("Browser opened successfully.")

if __name__ == "__main__":
    # Run the main function when script is executed directly
    run()