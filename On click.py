# pip install selenium webdriver-manager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
import re

# ---------------- CONFIG ----------------
CONFIG = {
    "do_login": True,   # set to False if login is not needed
    "login_url": "https://example.com/login",
    "login_user_selector": "input[name='username']",
    "login_pass_selector": "input[name='password']",
    "login_button_selector": "button[type='submit']",
    "username": "YOUR_USER",
    "password": "YOUR_PASS",

    # Target page
    "section_url": "https://example.com/index.php?/suits/amex",

    # Popup selectors
    "modal_root_xpath": "//*[@role='dialog' or contains(@class,'ui-dialog') or contains(@class,'modal')]",
    "save_button_xpath": ".//button[normalize-space()='Save' or normalize-space()='OK' or contains(@class,'btn-primary')]",
    "success_toast_selector": ".toast-success, .alert-success",
}

# ---------- Setup ----------
def build_driver(headless=False):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--start-maximized")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(60)
    return driver

wait_for = lambda drv, timeout=30: WebDriverWait(drv, timeout)

# ---------- Helpers ----------
def safe_click(driver, by, sel):
    el = wait_for(driver).until(EC.element_to_be_clickable((by, sel)))
    driver.execute_script("arguments[0].click();", el)
    return el

def wait_visible(driver, by, sel):
    return wait_for(driver).until(EC.visibility_of_element_located((by, sel)))

def do_login(driver, cfg):
    driver.get(cfg["login_url"])
    wait_visible(driver, By.CSS_SELECTOR, cfg["login_user_selector"]).send_keys(cfg["username"])
    wait_visible(driver, By.CSS_SELECTOR, cfg["login_pass_selector"]).send_keys(cfg["password"])
    safe_click(driver, By.CSS_SELECTOR, cfg["login_button_selector"])
    # Wait for login to complete (optional): change selector to something post-login
    # wait_visible(driver, By.CSS_SELECTOR, "div.dashboard")

def open_section(driver, cfg):
    driver.get(cfg["section_url"])
    # Wait for page to load
    wait_for(driver).until(lambda d: "suits" in d.current_url)

# ---------- Click Change Selection ----------
def click_change_selection(driver):
    # Wait for anchor <a> with onclick="app.runs.selectCases(...);"
    anchor = wait_for(driver).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@onclick,'app.runs.selectCases')]"))
    )

    # Extract the case ID if possible
    onclick = anchor.get_attribute("onclick")
    m = re.search(r"selectCases\((\d+)\)", onclick)
    if m:
        run_id = m.group(1)
        print(f"[INFO] Calling app.runs.selectCases({run_id}) via JS")
        driver.execute_script("app.runs.selectCases(arguments[0]);", int(run_id))
    else:
        print("[INFO] Could not parse ID, clicking the anchor directly...")
        driver.execute_script("arguments[0].click();", anchor)

# ---------- Handle Modal Popup ----------
def handle_modal_popup(driver, cfg):
    # Wait for modal to appear
    modal = wait_for(driver, 20).until(
        EC.visibility_of_element_located((By.XPATH, cfg["modal_root_xpath"]))
    )

    # Example: interact with dropdown if exists
    try:
        dropdown = modal.find_element(By.XPATH, ".//select")
        Select(dropdown).select_by_index(0)  # Adjust as needed
    except:
        pass

    # Example: click checkbox if exists
    try:
        checkbox = modal.find_element(By.XPATH, ".//input[@type='checkbox']")
        if not checkbox.is_selected():
            checkbox.click()
    except:
        pass

    # Click Save button
    save_btn = modal.find_element(By.XPATH, cfg["save_button_xpath"])
    driver.execute_script("arguments[0].click();", save_btn)

    # Wait for modal to disappear or success toast to appear
    try:
        wait_for(driver, 15).until(EC.invisibility_of_element(modal))
        print("[SUCCESS] Modal closed — Save likely successful ✅")
        return True
    except:
        try:
            wait_visible(driver, By.CSS_SELECTOR, cfg["success_toast_selector"])
            print("[SUCCESS] Success toast detected ✅")
            return True
        except:
            print("[WARN] No success confirmation detected ❓")
            return False

# ---------- Main ----------
def main():
    cfg = CONFIG
    driver = build_driver(headless=False)

    try:
        if cfg["do_login"]:
            do_login(driver, cfg)

        open_section(driver, cfg)
        click_change_selection(driver)
        ok = handle_modal_popup(driver, cfg)

        print("\n=== RESULT ===")
        print("✅ SAVE SUCCESS" if ok else "❌ SAVE NOT CONFIRMED")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
