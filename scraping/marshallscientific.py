"""
Created on Mon Jan  9 18:06:56 2017

@author: thotran
Marshall Scientific sells used equipment only. 
"""
import util
from Result import Result
import logging
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

MAIN_URL = "http://www.marshallscientific.com/searchresults.asp?Search="
DELIMITER = '+'


def extract_results(search_word: str, results: list, lock: threading.Lock, stop_event: threading.Event,
                    condition: str = 'used'):
    if condition == "new":
        return []
    url = util.create_url(MAIN_URL, search_word, DELIMITER)
    try:
        soup = util.get_soup(url)
        product_grid = soup.find('div', class_='v-product-grid')
        if not product_grid:
            return []
        total_equips = product_grid.find_all('div', class_='v-product')
    except Exception as e:
        logging.exception(f"Can't soup at {url}: {e}")
        return []
    equips = []

    for equip in total_equips:
        # Check if stop event is set
        if stop_event.is_set():
            break
        title = equip.find('a', class_='v-product__title productnamecolor colors_productname').find(string=True).strip()
        if not util.is_close_match(search_word, title):
            continue
        url = equip.find('a', class_='v-product__img').get('href')
        img_src = 'http:' + equip.find('img').get('src')
        equip.find('div', class_='product_productprice').find_all(string=True)
        price = equip.find('div', class_='product_productprice').find_all(string=True)
        price = util.get_price(''.join(price))
        if not util.is_valid_price(price):
            continue
        res = Result(title, url, price, img_src)
        # Acquire lock to safely update the results dictionary
        lock.acquire()
        results.append(res)
        lock.release()
        if len(results) >= util.MAX_RESULTS:
            stop_event.set()
            break
    return equips


def main():
    results = []
    lock = threading.Lock()
    stop_event = threading.Event()
    extract_results('vacuum', results, lock, stop_event)
    print(results)


if __name__ == '__main__':
    main()
