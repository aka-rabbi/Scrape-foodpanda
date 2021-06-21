from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time

from selenium.common.exceptions import NoSuchElementException, TimeoutException
# import re
import json
import gspread
from google.oauth2.credentials import Credentials

from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from utils import flatten_data
import sys

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def extract_data(url):
    '''
    gets all the useful information from the html data
    '''
    #useful driver options to run it on linux. not needed for windows.
    chrome_options = webdriver.ChromeOptions() 
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-setuid-sandbox") 
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_options.add_argument("--disable-dev-shm-using") 
    chrome_options.add_argument("--disable-extensions") 
    # chrome_options.add_argument("--disable-gpu") 
    # chrome_options.add_argument("start-maximized") 
    # chrome_options.add_argument("disable-infobars")
    # chrome_options.add_argument(r"user-data-dir=.\cookies\\test")
    
    print(f"scraping {url}...")

    driver = webdriver.Chrome('/home/nassagroup/Desktop/scraper__/chromedriver', options=chrome_options)
    # keep the window open otherwise it can't get all the data.
    driver.maximize_window()
    driver.get(url)
    # driver.get('https://www.foodpanda.com.bd/restaurant/new/zp2f/cafe-pizza-house')


    # get rid of any unwanted overlay
    ac = ActionChains(driver)

    ac.send_keys(Keys.ESCAPE).perform()
    resturant_info = driver.find_element_by_css_selector(".vendor-info-link")
    ac.move_to_element(resturant_info).click().perform()

    # Get restaurant address then put it as the user's location.
    wait = WebDriverWait(driver, 5)
    address = wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="about-panel"]/div[1]/div[2]/p'))).get_attribute("innerHTML")

    ac.send_keys(Keys.ESCAPE).perform()

    location = driver.find_element_by_css_selector(".location-search-button")
    ac.move_to_element(location).click().perform()
    driver.find_element_by_css_selector(".restaurants-search-form__input").send_keys(address)

    next_step = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '.location-search-go-icon')))
    next_step.click()
                                                    
    next_step = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, '.map-submit-button')))
    ac.move_to_element(next_step).click().perform()                                                                                

    data_rows = []

    wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".dish-list")))
    body_html = driver.find_elements_by_css_selector(".dish-category-section")
    for category in body_html:
        
        category_name = category.find_element_by_css_selector("h2").get_attribute("innerText")
        
        price = category.find_element_by_css_selector(".price-tags-container span").get_attribute("innerText")

        buttons = category.find_elements_by_css_selector(".product-button-overlay")

        for button in buttons:
            next_sibling = driver.execute_script("""
                    return arguments[0].nextElementSibling
                """, button)
        
            dish_name = next_sibling.find_element_by_css_selector(".dish-name span").get_attribute("innerHTML")
            dish_description = next_sibling.find_element_by_css_selector("p").get_attribute("innerHTML")

            button.click()
            time.sleep(0.5)

            try:
                option_name = driver.find_element_by_css_selector(".product-topping-list-title-text").get_attribute("innerHTML")
                for label in driver.find_elements_by_css_selector(".product-topping-item"):

                    option = label.find_elements_by_css_selector("label label.radio-box span")[-1].get_attribute("innerHTML")
                    option_price = label.find_elements_by_css_selector("span")[-1].get_attribute("innerHTML")
                    data_rows.append( (category_name, dish_name, dish_description, price, option_name, option, option_price) )

                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
            except NoSuchElementException:
                data_rows.append( (category_name, dish_name, dish_description, price, '', '', '') )
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    return data_rows, driver

            
def main(items_list):
    '''
    credential for google drive obtained through official docs
    see `https://github.com/googleworkspace/python-samples/blob/master/docs/quickstart/quickstart.py` for more details
    '''
    creds = None


    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'creds.json', SCOPES)
            creds = flow.run_local_server(port=51227)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())


    file = gspread.authorize(creds)

    sheet = file.open("Food Panda").get_worksheet(1)
    print('Updating spreadsheet...')
    
    flattened_data, cell_range = flatten_data(items_list)
    cells = sheet.range(cell_range)

    for x in range(len(flattened_data)):
        cells[x].value = flattened_data[x]

    sheet.update_cells(cells)



    
if __name__ == '__main__':
    try:
        url  = sys.argv[1]
    except IndexError:
        url = input('Please enter a valid URL: ')
    items_list, driver = extract_data(url)
    main(items_list)
    driver.quit()
    print('done')

    

