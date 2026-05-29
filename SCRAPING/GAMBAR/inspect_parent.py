import pandas as pd
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def main():
    driver = init_driver()
    url = "https://www.google.com/maps/place/Air+Terjun+Grojogan+Sewu+Pujon/data=!4m7!3m6!1s0x2e7887a1073e1ce7:0x4fdbae6fe33510b0!8m2!3d-7.8664128!4d112.4233498!16s%2Fg%2F11b6_nvy3v!19sChIJ5xw-B6GHeC4RsBA142-u208?authuser=0&hl=id&rclk=1"
    
    try:
        driver.get(url)
        time.sleep(6)
        
        # Find the image with googleusercontent
        imgs = driver.find_elements(By.TAG_NAME, "img")
        for idx, img in enumerate(imgs):
            src = img.get_attribute("src")
            if src and "googleusercontent" in src:
                print(f"\n--- FOUND IMAGE {idx} ---")
                print(f"src: {src[:90]}...")
                print(f"alt: {img.get_attribute('alt')}")
                
                # Print outerHTML of parent elements
                parent = img
                for i in range(1, 4):
                    try:
                        parent = parent.find_element(By.XPATH, "..")
                        print(f"Parent level {i}: tag={parent.tag_name} | class='{parent.get_attribute('class')}' | jsaction='{parent.get_attribute('jsaction')}' | aria-label='{parent.get_attribute('aria-label')}'")
                    except Exception as e:
                        print(f"Parent level {i} error: {e}")
                        break
                        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
