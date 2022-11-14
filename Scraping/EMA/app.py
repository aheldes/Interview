from aws_lambda_powertools.utilities.typing import LambdaContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from secrets import access_key, secret_key
import boto3
import smart_open
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup


def getDriver() -> webdriver:
    chromeOptions = Options()
    chromeOptions.binary_location = '/opt/headless-chromium'
    chromeOptions.add_argument("--window-size=1920,1080")
    chromeOptions.add_argument("--start-maximized")
    chromeOptions.add_argument('--headless')
    chromeOptions.add_argument('--no-sandbox')
    chromeOptions.add_argument('--single-process')
    chromeOptions.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome('/opt/chromedriver', options=chromeOptions)
    return driver

def lambda_handler(event: dict, context: LambdaContext) -> dict:
    url = 'https://www.ema.europa.eu/en/medicines/field_ema_web_categories%253Aname_field/Human/ema_group_types/ema_medicine/field_ema_med_status/authorised-36?search_api_views_fulltext=ATC%20AND%20L01*%20OR%20ATC%20AND%20L02*'
    driver = getDriver()
    driver.get(url)
    cookie = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,  '//*[@id="cookie-consent-banner"]/div/div/div[2]/a[1]')))
    cookie.click()
    cookie = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,  '''//*[@id="cookie-consent-banner"]/div/div/div[2]/a''')))
    cookie.click()
    
    if event['type'] == "daily":
        editDateFrom = driver.find_element_by_css_selector('#edit-date-from--3-datepicker-popup-0')
        editDateTo = driver.find_element_by_css_selector('#edit-date-to--3-datepicker-popup-0')
        yesterday = (datetime.now() - timedelta(1)).strftime('%d/%m/%Y')
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateFrom)
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateTo)
        driver.find_element_by_xpath('//*[@id="edit-submit--10"]').click()

    numberOfElements = len(driver.find_elements_by_xpath('/html/body/main/div/div[2]/section/div/div[5]/div[1]/ul/li/a'))
    while True:
        try:
            driver.find_element_by_xpath('//*[@id="block-current-search-ema-standard"]/div[5]/div[2]/ul/li/a').click()
        except NoSuchElementException:
            break
        WebDriverWait(driver, 20).until(lambda x: len(driver.find_elements_by_xpath('/html/body/main/div/div[2]/section/div/div[5]/div[1]/ul/li/a')) > numberOfElements)
        numberOfElements = len(driver.find_elements_by_xpath('/html/body/main/div/div[2]/section/div/div[5]/div[1]/ul/li/a'))
    
    aTags = driver.find_elements_by_xpath('//*[@id="block-current-search-ema-standard"]/div[5]/div[1]/ul/li/a')
    notLoaded = []
    numberOfUploaded = 0
    
    if len(aTags) != 0:
        urls = {a.get_attribute("href") for a in aTags}
        driver.close()
    
        client = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)
        bucket = 'emapdf'
        for url in urls: 
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            pdf = soup.select_one('#block-views-09027d5b69ce7c6479b2b6ca7b91e8c2 > div > div > div > div > ul > li.ecl-list-item.ema-list-item.ema-list-item--file.ecl-list-items--with-translations > a')
            
            fileHref = pdf['href']
            fileName = fileHref.rsplit('/', 1)[-1]
            file_key = f'pdf/{fileName}'
            try:
                with smart_open.open(fileHref, 'rb',buffering=0) as f:
                    client.put_object(Bucket=bucket, Key=file_key, Body=f.read())
                numberOfUploaded += 1
            except:
                notLoaded.append({'url':url, 'fileHref': fileHref})
    return {
        'statusCode': 200,
        'body': {'status': 'Success',
        'numberOfUpdatedDocuments': numberOfUploaded,
        'errors': notLoaded
        } 
    }
