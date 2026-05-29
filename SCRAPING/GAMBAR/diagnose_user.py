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
            
            # Use the new get_gallery_images logic to extract 5 high-res URLs
            import re
            
            def get_gallery_images_test(driver, limit=5):
                image_urls = []
                # 1. Background image styles
                elements_with_style = driver.find_elements(By.XPATH, "//*[@style]")
                print(f"Inspecting {len(elements_with_style)} styled elements for background-image...")
                for el in elements_with_style:
                    try:
                        style = el.get_attribute("style")
                        if style and "googleusercontent.com" in style:
                            if "/a/" in style or "=s36" in style or "=s40" in style or "=s44" in style or "=s48" in style or "=s64" in style:
                                continue
                            match = re.search(r'url\("?([^"\)]+)"?\)', style)
                            if match:
                                src = match.group(1)
                                if src.startswith("//"): src = "https:" + src
                                if '=' in src:
                                    base_url = src.split('=')[0]
                                    high_res = base_url + "=w1080"
                                else:
                                    high_res = src + "=w1080"
                                if high_res not in image_urls:
                                    image_urls.append(high_res)
                                    if len(image_urls) >= limit: return image_urls
                    except:
                        pass
                
                # 2. Standard img tags as fallback
                imgs = driver.find_elements(By.TAG_NAME, "img")
                print(f"Inspecting {len(imgs)} img tags...")
                for img in imgs:
                    try:
                        src = img.get_attribute("src")
                        if src and ("googleusercontent.com" in src or "streetviewpixels" in src):
                            if "/a/" in src or "=s36" in src or "=s40" in src or "=s44" in src or "=s48" in src or "=s64" in src:
                                continue
                            if '=' in src:
                                base_url = src.split('=')[0]
                                high_res = base_url + "=w1080"
                            else:
                                high_res = src + "=w1080"
                            if high_res not in image_urls:
                                image_urls.append(high_res)
                                if len(image_urls) >= limit: return image_urls
                    except:
                        pass
                return image_urls

            extracted_urls = get_gallery_images_test(driver, 5)
            print(f"\n--- SUCCESS! EXTRACTED {len(extracted_urls)} HIGH-RES IMAGE URLS ---")
            for idx, url in enumerate(extracted_urls):
                print(f"[{idx+1}] {url[:100]}...")
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
