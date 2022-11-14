from aws_lambda_powertools.utilities.typing import LambdaContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import boto3
import smart_open
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import os

access_key = os.environ['access_key']
secret_key = os.environ['secret_key']

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
    url = 'https://www.scottishmedicines.org.uk/medicines-advice/'
    driver = getDriver()
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,'''//*[@id="ccc-module"]''')))
    cookie = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH,  '//*[@id="ccc-recommended-settings"]')))
    cookie.click()

    if event['type'] == "daily":
        driver.find_element(by=By.CSS_SELECTOR, value='#medicine-advice-form > div.list-filters > div.list-filters__toggle > span.button--primary-open').click()
        editDateFrom = driver.find_element(by=By.CSS_SELECTOR, value='#from')
        editDateTo = driver.find_element(by=By.CSS_SELECTOR, value='#to')
        yesterday = (datetime.now() - timedelta(1)).strftime('%d/%m/%Y')
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateFrom)
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateTo)
        driver.find_element(by=By.CSS_SELECTOR, value='#medicine-advice-form > div.list-filters > div.list-filters__submit.open > input').click()

    # Rozklikavanie stranky, aby sa nam zobrazili vsetky hodnotenia. Kod funguje rovnako ako u EMA.
    numberOfElements = len(driver.find_elements(by=By.XPATH, value='//*[@id="tabContentPublished"]/div[1]/table/tbody/tr'))
    while True:
        try:
            driver.find_element(by=By.XPATH, value='//*[@id="btn-more-0"]').click()
        except:
            break
        WebDriverWait(driver, 20).until(lambda x:  len(driver.find_elements(by=By.XPATH, value='//*[@id="tabContentPublished"]/div[1]/table/tbody/tr'))  > numberOfElements)
        numberOfElements = len(driver.find_elements(by=By.XPATH, value='//*[@id="tabContentPublished"]/div[1]/table/tbody/tr')) 
        
    aTags = driver.find_elements(by=By.XPATH, value='''//*[@id="tabContentPublished"]/div[1]/table/tbody/tr[' ']/td[3]/a''')

    notLoaded = []
    numberOfUploaded = 0

    if len(aTags) != 0:
        urls = {a.get_attribute("href") for a in aTags}
        driver.close()
        
        client = boto3.client('s3', aws_access_key_id = access_key, aws_secret_access_key = secret_key)
        bucket = 'smcpdf'
        
        for url in urls: 
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")

            pdf = soup.select_one('.advice-document__link') 

            if pdf is not None:
                fileHref = pdf['href']
                fileName = fileHref.rsplit('/', 1)[-1]
                fileKey = f'pdf/{fileName}'

                with smart_open.open(f'https://www.scottishmedicines.org.uk/{fileHref}', 'rb',buffering=0) as f:
                    client.put_object(Bucket=bucket, Key=fileKey, Body=f.read())
                    numberOfUploaded += 1
            else:
                notLoaded.append(url)


    return {
        'statusCode': 200,
        'body': {'status': 'Success',
        'numberOfUpdatedDocuments': numberOfUploaded,
        'errors': notLoaded
        } 
    }
