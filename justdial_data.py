from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from webdriver_manager.chrome import ChromeDriverManager

# Get user inputs
search_query = input("🔍 What are you searching for (e.g., 'Wedding Planning'): ").strip().replace(" ", "-")
location = input("📍 Enter location (e.g., 'Tirupati'): ").strip().replace(" ", "-").capitalize()

# Construct URL
url = f"https://www.justdial.com/{location}/{search_query}"
print(f"🌐 Opening: {url}")

# Construct filename
filename = f"{search_query}s-at-{location.lower()}.csv"
print(f"📄 Output will be saved as: {filename}")

# Set up Selenium WebDriver
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_experimental_option("excludeSwitches", ["enable-automation"])

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get(url)

# Debugging: Check page load
print("⏳ Waiting for page to load...")
try:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("✅ Page body loaded.")
    
    # Manual delay for JavaScript
    print("⏳ Waiting 15s for JavaScript to load listings...")
    time.sleep(15)
    
    # Wait for listings container
    WebDriverWait(driver, 50).until(
        EC.presence_of_all_elements_located((By.XPATH, "//div[contains(@class,'store')] | //div[contains(@class,'result')] | //section"))
    )
    print("✅ Listings container found.")
except Exception as e:
    print(f"⚠️ Error loading page or listings: {e}")
    with open("page_source.html", "w", encoding="utf-8") as f:
        f.write(driver.page_source)
    print("📝 Saved page source to 'page_source.html'. Please check it for correct XPath.")
    driver.quit()
    exit()

# Scroll to load all listings
print("⏳ Scrolling to load all listings...")
last_height = driver.execute_script("return document.body.scrollHeight")
while True:
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(5)
    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Collect data
print("🕵️ Collecting all visible listings...")
data = []
seen_names = set()  # To avoid duplicates

try:
    listings = driver.find_elements(By.XPATH, "//div[contains(@class,'store')] | //div[contains(@class,'result')] | //section")
    print(f"📊 Found {len(listings)} listings.")
except Exception as e:
    print(f"⚠️ Error finding listings: {e}")
    listings = []

for i, listing in enumerate(listings, 1):
    try:
        # Name
        name_elem = listing.find_element(By.XPATH, ".//h2 | .//a[@title] | .//span[contains(@class,'name')]")
        name = name_elem.text.strip()
        if len(name.split()) < 2 or name.lower() in ["user", "average ratings"]:
            continue
        if name in seen_names:
            continue
        seen_names.add(name)
    except:
        continue

    try:
        # Click "Show Number" button and extract phone
        show_number_btn = listing.find_element(By.XPATH, ".//a[contains(text(), 'Show Number')] | .//button[contains(text(), 'Show Number')]")
        show_number_btn.click() 
        time.sleep(2)  # Wait for number to appear
        phone_elem = listing.find_element(By.XPATH, ".//a[contains(@href,'tel:')] | .//span[contains(@class,'callcontent')]")
        phone = phone_elem.get_attribute("href").replace("tel:", "").strip() if "tel:" in phone_elem.get_attribute("href") else phone_elem.text.strip()
        if not phone or len(phone) != 11 or not phone.startswith("0"):
            phone = "Not Available"
    except:
        phone = "Not Available"

    try:
        # Address
        address_elem = listing.find_element(By.XPATH, ".//div[contains(@class,'locatcity')] | .//p[contains(@class,'address')] | .//span[contains(@class,'addr')]")
        address = address_elem.text.strip()
    except:
        address = "N/A"

    try:
        # Rating
        rating_elem = listing.find_element(By.XPATH, ".//div[contains(@class,'resultbox_totalrate')] | .//span[contains(@class,'rating')]")
        rating = rating_elem.text.strip().split()[0]  # Extract the number (e.g., "5.0" from "5.0<span>")
    except:
        rating = "N/A"

    print(f"{i}. {name} | 📞 {phone} | ⭐ {rating} | 📍 {address}")
    data.append([name, phone, rating, address])

# Save to CSV
if data:
    df = pd.DataFrame(data, columns=["Name", "Phone", "Rating", "Address"])
    df = df.replace("", "N/A")
    df.to_csv(filename, index=False, encoding="utf-8")
    print(f"✅ Data saved to {filename}")
    print("\nSample Output (first 5 rows):")
    print(df.head().to_string(index=False))
else:
    print("⚠️ No valid listings found. Check 'page_source.html' for correct XPath.")

driver.quit()
print("🔚 Browser closed.")