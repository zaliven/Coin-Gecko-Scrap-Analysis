# Coin Gecko Scrape
## Overview 
A script that web scrapes coingecko.com. It takes raw textual data, and transforms it into a dataframe that contains 3 months historical data of the top 1000 coins in the site (by marketcap).


![Imgur](https://i.imgur.com/CozCdI4.png)

## Fields included
```
date
price - open price (00:00AM) of the specific date
coin_name
symbol
market_cap
volume
v_marketcap - calculated after processing the data
24_hr_pct_change - calculated after processing the data, using a rolling window function
7_day_pct_change - calculated after processing the data, using a rolling window function
rank - calculated after processing the data. calculated by index of sorted coins market cap, per date
```


## External python libraries used
```
Pandas
Numpy
BeautifulSoup
```
