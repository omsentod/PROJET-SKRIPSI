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
        time.sleep(5)
        
        # Click the cover photo button to open gallery
        cover_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label^='Foto']")
        driver.execute_script("arguments[0].click();", cover_btn)
        print("Clicked cover photo button. Waiting 5s...")
        time.sleep(5)
        
        # Now search the entire DOM for elements referencing googleusercontent
        print("\n--- SEARCHING FOR GOOGLEUSERCONTENT REFERENCES ---")
        
        # 1. Search all elements with a style attribute
        elements_with_style = driver.find_elements(By.XPATH, "//*[@style]")
        print(f"Found {len(elements_with_style)} elements with a style attribute.")
        style_matches = 0
        for idx, el in enumerate(elements_with_style):
            try:
                style = el.get_attribute("style")
                if "googleusercontent" in style:
                    style_matches += 1
                    print(f"Style Match [{style_matches}]: tag={el.tag_name} | class='{el.get_attribute('class')}' | style='{style[:150]}...'")
            except:
                pass
                
        # 2. Search all img elements
        imgs = driver.find_elements(By.TAG_NAME, "img")
        print(f"\nFound {len(imgs)} img elements.")
        img_matches = 0
        for idx, img in enumerate(imgs):
            try:
                src = img.get_attribute("src")
                if src and "googleusercontent" in src:
                    img_matches += 1
                    print(f"Img Match [{img_matches}]: tag={img.tag_name} | class='{img.get_attribute('class')}' | src='{src[:150]}...'")
            except:
                pass
                
        # 3. Search all div/a elements that might have data-urls or custom attributes
        all_els = driver.find_elements(By.XPATH, "//*[contains(@class, 'photo') or contains(@class, 'image') or @role='img']")
        print(f"\nFound {len(all_els)} potential photo-class/role=img elements.")
        for idx, el in enumerate(all_els[:20]):
            try:
                print(f"El [{idx}]: tag={el.tag_name} | class='{el.get_attribute('class')}' | role='{el.get_attribute('role')}' | text='{el.text[:30]}'")
            except:
                pass

    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
