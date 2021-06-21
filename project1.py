from selenium import webdriver
from  time import sleep

import os
from selenium.common.exceptions import NoSuchElementException
import re
import gspread
from google.oauth2.credentials import Credentials

import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import sys
from utils import flatten_data

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/drive']

def extract_data(body):
    '''
    gets all the useful information from the html data
    '''
    items_list = []
    for element in body:
        try:
            name = element.find_element_by_css_selector(".fn").get_attribute("innerHTML")
            rating = element.find_element_by_css_selector("b").get_attribute("innerHTML")
            discount = element.find_element_by_css_selector(".multi-tag").get_attribute("innerHTML")
            url = element.find_element_by_css_selector("a").get_attribute("href")
            ratings_detail = element.find_element_by_css_selector(".ratings-component").get_attribute("innerHTML")
            num_reviews = re.search(r"(?<=<span> \()[a-zA-Z0-9+]+(?=\))", ratings_detail).group()
            price = 0
            description = ""
            detail_list = element.find_elements_by_css_selector(".categories.summary span")

            for ele in detail_list:
                text = ele.get_attribute("innerHTML")
                if text == "৳":
                    price += 1
                else:
                    description += f"{text} "  
            items_list.append((name, url, description, discount, price, rating, num_reviews))
        except NoSuchElementException as e:
            continue

    return items_list

def get_html(url):
    '''
    scrolls through the whole page to get all the html data
    '''
    SCROLL_PAUSE_TIME = 1

    viewport = "document.documentElement.scrollHeight"

    # useful driver options to run it on linux. not needed for windows.
    # chrome_options = webdriver.ChromeOptions() 
    # chrome_options.add_argument("--no-sandbox") 
    # chrome_options.add_argument("--disable-setuid-sandbox") 
    # chrome_options.add_argument("--remote-debugging-port=9222")
    # chrome_options.add_argument("--disable-dev-shm-using") 
    # chrome_options.add_argument("--disable-extensions") 
    # chrome_options.add_argument("--disable-gpu") 
    # chrome_options.add_argument("start-maximized") 
    # chrome_options.add_argument("disable-infobars")
    # chrome_options.add_argument(r"user-data-dir=.\cookies\\test")

    print(f"scraping {url}...")
    #disable logging
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("excludeSwitches", ['enable-logging'])
    
    driver = webdriver.Chrome('C:\chromedriver\chromedriver.exe', options=chrome_options)
    driver.maximize_window()
    driver.get(url)
    # driver.get('https://www.foodpanda.com.bd/restaurants/new?lat=23.7511965&lng=90.373567&expedition=pickup&vertical=restaurants')

    start_height = 0
    scrolled_height = 0
    total_height = driver.execute_script(f"return {viewport}")

    screen_height = driver.execute_script("return window.innerHeight")

    while True:

        sleep(SCROLL_PAUSE_TIME)

        if scrolled_height >= total_height:
            break
        elif scrolled_height < total_height:
            driver.execute_script(f"window.scrollTo({start_height}, {int(start_height)+int(screen_height)});")
            
            scrolled_height = driver.execute_script("return window.pageYOffset") + driver.execute_script("return window.innerHeight")
            total_height = driver.execute_script(f"return {viewport}")
            
            start_height = scrolled_height
        else:
            break
    
    results = driver.find_elements_by_css_selector("li")
    
    return results, driver

def main(html_body):
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

    sheet = file.open("Food Panda").get_worksheet(0)

    print('Updating spreadsheet...')
    
    items_list = extract_data(html_body)

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
    html_body, driver = get_html(url)
    main(html_body)
    driver.quit()
    print('done')
