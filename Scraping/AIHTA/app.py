from aws_lambda_powertools.utilities.typing import LambdaContext
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.ui import Select
import boto3
import smart_open
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
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
    url = 'https://eprints.aihta.at/view/subjects/QZ200-380.html'
    driver = getDriver()
    driver.get(url)
    driver.find_element(by=By.XPATH, value='//*[@id="export-format"]/option[6]').click()
    driver.find_element(by=By.XPATH, value='//*[@id="content"]/form/div/div[1]/div[1]/input[1]').click()

    aTags = driver.find_elements(by=By.XPATH, value='''/html/body/p[' ']/a''')
    notLoaded = []
    numberOfUploaded = 0
    
    if len(aTags) != 0:
        urls = {a.get_attribute("href") for a in aTags}
        driver.close()
        client = boto3.client('s3', aws_access_key_id = access_key, aws_secret_access_key = secret_key)
        bucket = 'aihtapdf'

        for url in urls: 
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            pdf = soup.select_one('.ep_document_link')
            if pdf is not None:
                fileHref = pdf['href']
                fileName = fileHref.rsplit('/', 1)[-1]
                file_key = f'pdf/{fileName}'
                if fileHref.startswith('/'):
                    fileHref = url + '/'.join(fileHref.split('/', 2)[2:])
                with smart_open.open(fileHref, 'rb', buffering=0) as f:
                    client.put_object(Bucket=bucket, Key=file_key, Body=f.read())
                    numberOfUploaded += 1
            else:
                notLoaded.append(url)

    return {
        'statusCode': 200,
        'body': {
        'status': 'Success',
        'numberOfUpdatedDocuments': numberOfUploaded,
        'errors': notLoaded
        } 
    }

