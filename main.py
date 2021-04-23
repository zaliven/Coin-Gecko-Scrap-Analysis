from bs4 import BeautifulSoup as bs
import requests as rq
import pandas as pd
import numpy as np
import re
from time import sleep
from time import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import urllib
import random
from time import sleep


today_str = datetime.now().strftime("%Y-%m-%d")
three_months_ago_str = (datetime.now() - relativedelta(days=+90)).strftime("%Y-%m-%d")


# sleep 1-3 seconds to avoid getting blocked by captcha
def random_sleep():
    sleep(random.uniform(1, 3))


def scrape_coin_gecko():
    df = pd.DataFrame(columns=['date', 'coin_name', 'symbol', 'market_cap', 'volume', 'price', '24_hr_pct_change', '7_day_pct_change', 'v_marketcap'])
    start_time = time()
    for i in range(1, 11):
        url = f'https://www.coingecko.com/en?page={i}'
        main_html = rq.get(url).text
        main_html_soup = bs(main_html,'html.parser')
        hrefs = main_html_soup.find_all("a", {"class": "d-lg-none font-bold"}, href=True)
        for coin_url in hrefs:
            try:
                df = df.append(scrape_coin(coin_url['href']))
                random_sleep()
            except Exception as e:
                print(coin_url)
                print(e)
    end_time = time()
    print(f'Seconds passed: {end_time - start_time}')
    return df


def scrape_coin(coin_url):
    url = f'https://www.coingecko.com/{coin_url}/historical_data/usd?end_date={today_str}&start_date={three_months_ago_str}#panel'
    text = rq.get(url).text
    soup = bs(text,'html.parser')

    dates = [x.text.strip() for x in soup.find_all("th", {"class" : "font-semibold text-center"})]
    # Remove $ and commas from coin information (Market Cap, Volume, Price), to convert to int later
    info = [x.text.strip()[1:].replace(',', '') for x in soup.find_all("td", {"class" : "text-center"})]
    market_caps = info[0::4]
    volumes = info[1::4]
    open_price = info[2::4]
    # arr_length is calculated to fit coin symbol/name to dataframe. May differ from 60 if the coin is new.
    arr_length = len(market_caps) 
    coin = [x.text.strip() for x in soup.find_all("div", {"class" : "mr-md-3 mx-2 mb-md-0 text-3xl font-semibold"})]
    # example for coin: Bitcoin (BTC)
    coin_symbol = [re.findall('.*\((.*)\)', x)[0] for x in coin] * arr_length
    coin_name = [re.findall('(.*)[ ]\(', x)[0] for x in coin] * arr_length

    df = pd.DataFrame({'date' : dates, 'coin_name' : coin_name, 'symbol' : coin_symbol, 'market_cap' : market_caps, 'volume' : volumes, 'price' : open_price})
    df['date'] = pd.to_datetime(df['date'], format="%Y-%m-%d")
    df = df.astype({'market_cap' : 'float64', 'volume' : 'float32', 'price' : 'float32'})
    # Pandas Rolling function is backwards; reversing market_cap series and then reversing the series returned will
    # implement a forward rolling function
    df['24_hr_pct_change'] = df['market_cap'][::-1].rolling(window=2).apply(lambda x: day_pct_change(x))[::-1]
    df['7_day_pct_change'] = df['market_cap'][::-1].rolling(window=7).apply(lambda x: seven_day_pct_change(x))[::-1]
    df['v_marketcap'] = df.apply(lambda x: calculate_v_marketcap(x), axis=1)
    df = df.astype({'24_hr_pct_change' : 'float16', '7_day_pct_change' : 'float16', 'v_marketcap' : 'float16'})
    
    return df


# Volume divided by marketcap
def calculate_v_marketcap(x):
    try:
        return x['volume'] / x['market_cap']
    except:
        return 0


def seven_day_pct_change(x):
    return (x.iloc[6] - x.iloc[0]) / x.iloc[6] * 100


def day_pct_change(x):
    return (x.iloc[1] - x.iloc[0]) / x.iloc[1] * 100


# Calculate the ranking of the coins per day; ranking is determined by market cap
# To calculate daily rank for the last three months, the coins are sorted by market cap per day
def calculate_daily_rank(df):
    temp_df = pd.DataFrame(columns = ['date', 'coin_name', 'symbol', 'market_cap', 'volume', 'price',
        '24_hr_pct_change', '7_day_pct_change', 'v_marketcap', 'rank'])
    for date in df['date'].unique():
        date = pd.to_datetime(date).date()
        temp = df.loc[df['date'].dt.date == date]
        # Produces an array [1..{amount of rows}]
        temp['rank'] = np.arange((temp.sort_values('market_cap', ascending=False).shape[0]))+1
        temp_df = temp_df.append(temp)
    return temp_df


df = scrape_coin_gecko()
df = df.drop_duplicates()
df = calculate_daily_rank(df)
df.to_csv('data.csv')