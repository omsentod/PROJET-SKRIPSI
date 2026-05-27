import pandas as pd
import time
import os
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--lang=id")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--start-maximized")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(45)
    return driver

def bypass_consent(driver):
    try:
        consent_buttons = driver.find_elements(By.XPATH, "//button[span[contains(text(), 'Tolak semua') or contains(text(), 'Reject all') or contains(text(), 'Saya setuju') or contains(text(), 'Agree')]]")
        for btn in consent_buttons:
            if btn.is_displayed():
                btn.click()
                print("✓ Bypassed Google Consent Popup.")
                time.sleep(2)
                break
    except Exception as e:
        print(f"Error bypassing consent: {e}")

def main():
    print("Loading wisataV2_updated.xlsx...")
    df = pd.read_excel("wisataV2_updated.xlsx")
    row = df.iloc[0]
    nama = row['Nama_Tempat']
    link = row['Link']
    print(f"Testing place: {nama}")
    print(f"Link: {link}")
    
    driver = init_driver()
    wait = WebDriverWait(driver, 15)
    
    try:
        driver.get(link)
        print("Waiting 5s for page to load...")
        time.sleep(5)
        bypass_consent(driver)
        
        # Take screenshot of main page
        driver.save_screenshot("main_page.png")
        print("Saved main_page.png")
        
        # Print all visible images on the main page
        imgs_main = driver.find_elements(By.TAG_NAME, "img")
        print(f"\n--- IMAGES ON MAIN PAGE (Total: {len(imgs_main)}) ---")
        for idx, img in enumerate(imgs_main[:15]):
            try:
                src = img.get_attribute("src")
                alt = img.get_attribute("alt")
                print(f"[{idx}] src: {src[:90]}... | alt: '{alt}'")
            except:
                pass
                
        # Try to find and click the "Foto" or "Photos" tab button
        print("\nSearching for 'Foto'/'Photos' tab...")
        tabs = driver.find_elements(By.XPATH, "//button[@role='tab' or contains(@class, 'tab') or contains(@class, 'chip')]")
        print(f"Found {len(tabs)} potential tab buttons:")
        for t in tabs:
            try:
                text = t.text
                aria = t.get_attribute("aria-label")
                print(f" - Text: '{text}' | Aria-label: '{aria}'")
            except:
                pass
                
        # Specifically try to find a button with text "Foto" or "Photos"
        tab_btn = None
        try:
            tab_btn = driver.find_element(By.XPATH, "//button[contains(., 'Foto') or contains(., 'Photos') or contains(@aria-label, 'Foto') or contains(@aria-label, 'Photos')]")
            print(f"Found specific tab button with text/aria-label: '{tab_btn.text}'")
        except Exception as e:
            print(f"Could not find specific tab button using xpath: {e}")
            
        # Try clicking it
        if tab_btn:
            print("Clicking the 'Foto'/'Photos' tab button...")
            try:
                tab_btn.click()
            except Exception as e:
                print(f"Normal click failed: {e}. Trying JS click...")
                driver.execute_script("arguments[0].click();", tab_btn)
                
            print("Clicked tab. Waiting 5s for gallery...")
            time.sleep(5)
            
            driver.save_screenshot("after_tab_click.png")
            print("Saved after_tab_click.png")
            
            # Print all visible images in gallery
            imgs_gallery = driver.find_elements(By.TAG_NAME, "img")
            print(f"\n--- IMAGES AFTER CLICKING TAB (Total: {len(imgs_gallery)}) ---")
            for idx, img in enumerate(imgs_gallery):
                try:
                    src = img.get_attribute("src")
                    alt = img.get_attribute("alt")
                    print(f"[{idx}] src: {src[:90]}... | alt: '{alt}'")
                except:
                    pass
        else:
            print("No tab button found. Trying cover photo click...")
            # Try to click the cover photo button
            try:
                cover_btn = driver.find_element(By.CSS_SELECTOR, "button[aria-label^='Foto']")
                driver.execute_script("arguments[0].click();", cover_btn)
                print("Clicked cover photo button.")
                time.sleep(5)
                driver.save_screenshot("after_cover_click.png")
                print("Saved after_cover_click.png")
                
                imgs_cover = driver.find_elements(By.TAG_NAME, "img")
                print(f"\n--- IMAGES AFTER CLICKING COVER PHOTO (Total: {len(imgs_cover)}) ---")
                for idx, img in enumerate(imgs_cover):
                    try:
                        src = img.get_attribute("src")
                        alt = img.get_attribute("alt")
                        print(f"[{idx}] src: {src[:90]}... | alt: '{alt}'")
                    except:
                        pass
            except Exception as e:
                print(f"Failed cover photo click: {e}")

    except Exception as e:
        print(f"Error in execution: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
