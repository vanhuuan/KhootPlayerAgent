import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def test_kahoot_access():
    """Test if we can access Kahoot without getting blocked"""
    
    # Setup Chrome with stealth options
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Hide webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Override user agent
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        print("Navigating to Kahoot...")
        driver.get("https://kahoot.it/")
        time.sleep(5)
        
        current_url = driver.current_url
        print(f"Current URL: {current_url}")
        print(f"Page title: {driver.title}")
        
        if "gameblock" in current_url:
            print("❌ BLOCKED: Kahoot detected automation")
            print("Page content preview:")
            print(driver.page_source[:500])
        else:
            print("✅ SUCCESS: Accessed Kahoot without being blocked")
            
            # Try to find the PIN input
            try:
                pin_inputs = driver.find_elements("css selector", "input[type='text']")
                if pin_inputs:
                    print(f"Found {len(pin_inputs)} input fields")
                    for i, inp in enumerate(pin_inputs):
                        placeholder = inp.get_attribute("placeholder")
                        print(f"  Input {i}: placeholder='{placeholder}'")
                else:
                    print("No input fields found")
            except Exception as e:
                print(f"Error finding inputs: {e}")
        
        input("Press Enter to close browser...")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    test_kahoot_access() 