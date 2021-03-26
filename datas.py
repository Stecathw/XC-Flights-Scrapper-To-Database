from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import os.path
import sys
import time
import pandas as pd
import csv
import gender_guesser.detector as gender



def create_driver():    
    # Locate the chromedriver executable and create driver
    exepath = sys.argv[0]
    #print(exepath)
    # get the path from the .py file
    dir_path = os.path.dirname(os.path.abspath(exepath))
    # get the path of "datasets" directory
    download_dir = dir_path+"\\datasets\\"
    preferences = {"download.default_directory": download_dir,
                   "download.prompt_for_download": False,
                   "directory_upgrade": True,
                   "safebrowsing.enabled": True }
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("prefs", preferences)
    return webdriver.Chrome(executable_path='./scrap/chromedriver/chromedriver.exe', chrome_options=chrome_options)

def get_web_page(driver):
    # Launch automatic test page to this url
    try:
        driver.get("https://parapente.ffvl.fr/node/1650")
    except Exception:
        print("Page not found")
        
def get_take_off():
    return input("Please choose a take off: ")

def fill_web_page_form(driver, launch):
    select = Select(driver.find_element_by_id("edit-1650-1-0"))
    select.select_by_value("null")
    take_off = driver.find_element_by_id("edit-1650-1-9")
    take_off.send_keys(launch)

def submit_search(driver):
    try:
        driver.find_element_by_id("edit-submit").click()
    except Exception:
        print("Take off not found")

def get_flights_number(driver):
    return driver.find_element_by_xpath("//div[2]/div/div/b").text

def get_table_as_dataframe(driver):
    return pd.read_html(driver.find_element_by_xpath("//div[2]/div/div/a[2]").get_attribute('href'))[0]

def dataframe_to_csv(df, launch):
    return df.to_csv("./scrap/datasets/{}.csv".format(launch))   

def filter_dataframe(df, launch):
    #Drop columns empty or not of our interest
    df.drop(['Unnamed: 0', 'Unnamed: 1', 'vol de groupe', 'Unnamed: 19', 'duree s',
             'B1','lat B1','lon B1','time B1','B2','lat B2','lon B2',
             'time B2','B3','lat B3','lon B3','time B3'], axis=1, inplace=True)
    # Rename headers
    df.rename(columns={"saison":"year", "type de vol":"flight type", "nom":"pilot name",
                       "km":"kms","decollage":"take off", "atterissage":"landing",
                       "parcours":"route","aile":"wing", "vitesse":"speed", 
                       "duree h":"duration", "altitude max":"max alt"}, inplace=True) 
    # Drop row for irelevant speed (lacking of gps trace most of the time)
    df.drop(df[df['speed'] > 500].index, inplace=True, axis=0)
    # fill cells NaN with 0
    df.fillna(0, inplace=True) #-> GIVES 0.0
    # Add launch name
    df.insert(0, "launch", launch)
    # Add pilot genre
    add_gender(df)
    # Sort by date
    df = df.sort_values("date")
    # Reset index 
    df.reset_index()
    return df

def add_gender(dataframe):
    # Add a new column for sex according to pilot name
    d = gender.Detector(case_sensitive=False)
    names = dataframe['pilot name']
    genre = []
    for name in names:
        try:
            name = str(name.split()[0])        
            if '-' in name:
                name = str(name.split('-')[0])
            genre.append(d.get_gender(name))  
        except:
            genre.append('error') 
            pass      
    dic = {'unknown':'male','mostly_male':'male', 'andy':'male'}
    genre = [dic.get(n, n) for n in genre]
    dataframe['sex'] = genre
    return dataframe

def initial_calculations(df):
    df['kms'] = df['kms'].apply(lambda x: x/100)
    df['points'] = df['points'].apply(lambda x: x/100)
    df['dist1'] = df['dist1'].apply(lambda x: x/100)
    df['dist2'] = df['dist2'].apply(lambda x: x/100)
    df['dist3'] = df['dist3'].apply(lambda x: x/100)
    df['dist4'] = df['dist4'].apply(lambda x: x/100)
    df['speed'] = df['speed'].apply(lambda x: x/10)
    df['duration'] = df['duration'].apply(lambda x: x/10)
    return df
   
def create_csv_file():
    launch = get_take_off()
    driver = create_driver()
    get_web_page(driver)
    fill_web_page_form(driver, launch)
    submit_search(driver)
    WebDriverWait(driver, 10)
    print(get_flights_number(driver))    
    df = get_table_as_dataframe(driver)
    filter_dataframe(df, launch)
    initial_calculations(df)
    #print(df)
    dataframe_to_csv(df, launch)    
    driver.close()
    driver.quit()


if __name__ == "__main__":
    create_csv_file()