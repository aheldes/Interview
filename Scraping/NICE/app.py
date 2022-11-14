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
import time
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
    url = 'https://www.nice.org.uk/guidance/published?ndt=Guidance&ndt=Quality%20standard&ngt=Clinical%20guidelines&ngt=NICE%20guidelines&ngt=Technology%20appraisal%20guidance&ps=9999'
    driver = getDriver()
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[2]')))
    cookie = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.XPATH, '/html/body/div[2]/div[2]/div/div/div[2]/button[1]/span')))
    cookie.click()
    
    if event['type'] == "daily":
        editDateFrom = driver.find_element(by=By.CSS_SELECTOR, value='#from')
        editDateTo = driver.find_element(by=By.CSS_SELECTOR, value='#to')
        yesterday = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateFrom)
        driver.execute_script(f"arguments[0].setAttribute('value', '{yesterday}')", editDateTo)
        driver.find_element(by=By.XPATH, value='//*[@id="group-last-updated-date"]/div/button').click()
        time.sleep(1)
        
    aTags = driver.find_elements(by=By.XPATH, value='''//*["@id=results"]/tbody/tr[' ']/td[1]/a''')
    notLoaded = []
    numberOfUploaded = 0
    
    if len(aTags) != 0:
        urls = {a.get_attribute("href") for a in aTags}
        driver.close()
        client = boto3.client('s3', aws_access_key_id = access_key, aws_secret_access_key = secret_key)
        bucket = 'nicepdf'
        
        for url in urls: 
            page = requests.get(url)
            soup = BeautifulSoup(page.content, "html.parser")
            
            try:
                pdf = soup.select_one('#nice-download')
            
                fileHref = pdf['href']
                fileName = fileHref.rsplit('/', 1)[-1] + ".pdf"
                fileName = fileName + ".pdf"
                fileKey = f'pdf/{fileName}'
                
                with smart_open.open("https://www.nice.org.uk" + fileHref, 'rb',buffering=0) as f:
                    client.put_object(Bucket=bucket, Key=fileKey, Body=f.read())
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
